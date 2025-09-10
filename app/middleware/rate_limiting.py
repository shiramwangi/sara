"""
Rate limiting middleware
"""

import time
import logging
import structlog
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

# Simple in-memory rate limiter (use Redis in production)
rate_limit_storage: Dict[str, Tuple[float, int]] = {}


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests"""
    
    def __init__(self, app, calls_per_minute: int = 60, calls_per_hour: int = 1000):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limits
        if not self._check_rate_limit(client_id):
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                ip=request.client.host if request.client else None
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Process request
        response = await call_next(request)
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Use IP address as client ID
        client_ip = request.client.host if request.client else "unknown"
        
        # For webhooks, also include the webhook source
        if request.url.path.startswith("/webhook"):
            webhook_source = request.url.path.split("/")[-1]
            return f"{client_ip}:{webhook_source}"
        
        return client_ip
    
    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limits"""
        current_time = time.time()
        
        # Get or create client data
        if client_id not in rate_limit_storage:
            rate_limit_storage[client_id] = (current_time, 1)
            return True
        
        last_reset, call_count = rate_limit_storage[client_id]
        
        # Reset counters if more than an hour has passed
        if current_time - last_reset > 3600:  # 1 hour
            rate_limit_storage[client_id] = (current_time, 1)
            return True
        
        # Check hourly limit
        if call_count >= self.calls_per_hour:
            return False
        
        # Check minute limit (sliding window)
        minute_ago = current_time - 60
        if last_reset > minute_ago and call_count >= self.calls_per_minute:
            return False
        
        # Increment call count
        rate_limit_storage[client_id] = (last_reset, call_count + 1)
        return True
    
    def _cleanup_old_entries(self):
        """Clean up old rate limit entries"""
        current_time = time.time()
        to_remove = []
        
        for client_id, (last_reset, _) in rate_limit_storage.items():
            if current_time - last_reset > 3600:  # 1 hour
                to_remove.append(client_id)
        
        for client_id in to_remove:
            del rate_limit_storage[client_id]
        
        logger.info("Cleaned up old rate limit entries", removed_count=len(to_remove))
