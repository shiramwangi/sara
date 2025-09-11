"""
Configuration management for Sara AI Receptionist
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")

    # Twilio Configuration
    twilio_account_sid: str = Field(..., env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(..., env="TWILIO_PHONE_NUMBER")

    # WhatsApp Configuration
    whatsapp_access_token: str = Field(..., env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = Field(..., env="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_verify_token: str = Field(..., env="WHATSAPP_VERIFY_TOKEN")

    # Google Calendar Configuration
    google_calendar_credentials_file: str = Field(
        "credentials.json", env="GOOGLE_CALENDAR_CREDENTIALS_FILE"
    )
    google_calendar_id: str = Field(..., env="GOOGLE_CALENDAR_ID")
    # Optional: Service Account auth (preferred for server environments)
    google_service_account_file: Optional[str] = Field(
        None, env="GOOGLE_SERVICE_ACCOUNT_FILE"
    )
    google_service_account_info: Optional[str] = Field(
        None, env="GOOGLE_SERVICE_ACCOUNT_INFO"
    )  # JSON string
    google_calendar_delegated_user: Optional[str] = Field(
        None, env="GOOGLE_CALENDAR_DELEGATED_USER"
    )

    # Email Configuration
    smtp_server: str = Field("smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: str = Field(..., env="SMTP_USERNAME")
    smtp_password: str = Field(..., env="SMTP_PASSWORD")

    # Database Configuration
    database_url: str = Field("sqlite:///./sara.db", env="DATABASE_URL")

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/sara.log", env="LOG_FILE")

    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    debug: bool = Field(False, env="DEBUG")

    # AI Configuration
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    max_tokens: int = Field(1000, env="MAX_TOKENS")
    temperature: float = Field(0.7, env="TEMPERATURE")

    # Business Logic
    business_name: str = Field("Sara AI Receptionist", env="BUSINESS_NAME")
    business_phone: str = Field("", env="BUSINESS_PHONE")
    business_email: str = Field("", env="BUSINESS_EMAIL")
    timezone: str = Field("UTC", env="TIMEZONE")

    # Rate Limiting
    max_requests_per_minute: int = Field(60, env="MAX_REQUESTS_PER_MINUTE")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
