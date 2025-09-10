# Sara AI Receptionist - Production Deployment Guide

## Overview

This guide covers deploying Sara AI Receptionist to production environments with proper security, monitoring, and scalability considerations.

## Prerequisites

### Infrastructure Requirements

- **Kubernetes cluster** (EKS, GKE, AKS, or self-managed)
- **Container registry** (ECR, GCR, ACR, or Docker Hub)
- **Database** (PostgreSQL 13+)
- **Redis** (for caching and rate limiting)
- **Load balancer** (ALB, GCLB, or nginx-ingress)
- **SSL certificates** (Let's Encrypt or commercial)
- **Monitoring** (Prometheus, Grafana, or cloud monitoring)

### Service Dependencies

- **OpenAI API** (GPT-4 access)
- **Twilio** (Voice and SMS)
- **WhatsApp Business API** (Meta)
- **Google Calendar API** (Google Cloud)
- **SMTP server** (Gmail, SendGrid, or AWS SES)

## Pre-Deployment Checklist

### 1. Security Configuration

- [ ] All API keys and secrets are properly configured
- [ ] SSL certificates are valid and configured
- [ ] Webhook URLs use HTTPS
- [ ] Database connections are encrypted
- [ ] Secrets are stored in Kubernetes secrets
- [ ] Network policies are configured
- [ ] RBAC permissions are set

### 2. Monitoring Setup

- [ ] Prometheus/Grafana or cloud monitoring configured
- [ ] Log aggregation (ELK, Fluentd, or cloud logging)
- [ ] Alerting rules configured
- [ ] Health checks implemented
- [ ] Metrics collection enabled

### 3. Database Setup

- [ ] PostgreSQL instance provisioned
- [ ] Database backups configured
- [ ] Connection pooling configured
- [ ] Migrations tested
- [ ] Performance tuning applied

### 4. External Services

- [ ] OpenAI API key with sufficient credits
- [ ] Twilio account with phone numbers
- [ ] WhatsApp Business API approved
- [ ] Google Calendar API enabled
- [ ] SMTP server configured

## Deployment Steps

### 1. Build and Push Docker Image

```bash
# Build the image
./scripts/build.sh v1.0.0 your-registry.com

# Push to registry
docker push your-registry.com/sara-ai-receptionist:v1.0.0
```

### 2. Configure Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace sara

# Create secrets
kubectl create secret generic sara-secrets \
  --from-literal=OPENAI_API_KEY="your_openai_key" \
  --from-literal=TWILIO_ACCOUNT_SID="your_twilio_sid" \
  --from-literal=TWILIO_AUTH_TOKEN="your_twilio_token" \
  --from-literal=WHATSAPP_ACCESS_TOKEN="your_whatsapp_token" \
  --from-literal=GOOGLE_CALENDAR_ID="your_calendar_id" \
  --from-literal=SMTP_USERNAME="your_smtp_user" \
  --from-literal=SMTP_PASSWORD="your_smtp_pass" \
  --from-literal=SECRET_KEY="your_secret_key" \
  --from-literal=ENCRYPTION_KEY="your_encryption_key" \
  --from-literal=DATABASE_URL="postgresql://user:pass@host:5432/sara" \
  -n sara

# Create Google Calendar credentials secret
kubectl create secret generic sara-credentials \
  --from-file=credentials.json=./credentials.json \
  -n sara
```

### 3. Deploy Infrastructure

```bash
# Deploy PostgreSQL
kubectl apply -f k8s/postgres.yaml

# Deploy Redis
kubectl apply -f k8s/redis.yaml

# Wait for infrastructure to be ready
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n sara
kubectl wait --for=condition=available --timeout=300s deployment/redis -n sara
```

### 4. Deploy Application

```bash
# Deploy Sara application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Wait for application to be ready
kubectl wait --for=condition=available --timeout=300s deployment/sara-backend -n sara
```

### 5. Run Database Migrations

```bash
# Run migrations
kubectl run sara-migration --image=your-registry.com/sara-ai-receptionist:v1.0.0 \
  --command -- alembic upgrade head \
  --env="DATABASE_URL=postgresql://user:pass@postgres:5432/sara" \
  -n sara

# Wait for migration to complete
kubectl wait --for=condition=complete job/sara-migration -n sara

# Clean up migration job
kubectl delete job sara-migration -n sara
```

### 6. Verify Deployment

```bash
# Check pod status
kubectl get pods -n sara

# Check service status
kubectl get services -n sara

# Check ingress status
kubectl get ingress -n sara

# Test health endpoint
curl https://sara.yourdomain.com/health
```

## Production Configuration

### 1. Resource Limits

```yaml
# In k8s/deployment.yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

### 2. Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sara-hpa
  namespace: sara
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sara-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 3. Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: sara-pdb
  namespace: sara
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: sara-backend
```

### 4. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sara-network-policy
  namespace: sara
spec:
  podSelector:
    matchLabels:
      app: sara-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: sara
    ports:
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 6379
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

## Monitoring and Observability

### 1. Prometheus Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: sara
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'sara-backend'
      static_configs:
      - targets: ['sara-service:8000']
      metrics_path: /metrics
      scrape_interval: 5s
```

### 2. Grafana Dashboard

Create a Grafana dashboard with:
- Request rate and latency
- Error rate and status codes
- Database connection pool metrics
- External API call metrics
- Resource utilization (CPU, memory)

### 3. Alerting Rules

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: sara-alerts
  namespace: sara
spec:
  groups:
  - name: sara.rules
    rules:
    - alert: SaraHighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate detected"
    
    - alert: SaraHighLatency
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High latency detected"
```

## Security Hardening

### 1. Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sara
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 2. RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: sara
  name: sara-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: sara-rolebinding
  namespace: sara
subjects:
- kind: ServiceAccount
  name: sara-service-account
  namespace: sara
roleRef:
  kind: Role
  name: sara-role
  apiGroup: rbac.authorization.k8s.io
```

### 3. Security Context

```yaml
# In deployment.yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
```

## Backup and Disaster Recovery

### 1. Database Backups

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: sara
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              pg_dump $DATABASE_URL > /backup/sara-$(date +%Y%m%d).sql
              gzip /backup/sara-$(date +%Y%m%d).sql
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: sara-secrets
                  key: DATABASE_URL
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: postgres-backup-pvc
          restartPolicy: OnFailure
```

### 2. Application State Backup

- Configuration backups (ConfigMaps, Secrets)
- Knowledge base exports
- Audit logs retention

## Performance Optimization

### 1. Database Optimization

```sql
-- Add indexes for performance
CREATE INDEX idx_interactions_call_id ON interactions(call_id);
CREATE INDEX idx_interactions_created_at ON interactions(created_at);
CREATE INDEX idx_interactions_channel ON interactions(channel);
CREATE INDEX idx_interactions_intent ON interactions(intent);

-- Optimize queries
ANALYZE interactions;
```

### 2. Caching Strategy

- Redis for session data
- Application-level caching for FAQ data
- CDN for static assets

### 3. Load Balancing

```yaml
# nginx-ingress configuration
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sara-ingress
  namespace: sara
  annotations:
    nginx.ingress.kubernetes.io/load-balance: "round_robin"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$binary_remote_addr"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
```

## Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**
   ```bash
   kubectl describe pod <pod-name> -n sara
   kubectl logs <pod-name> -n sara
   ```

2. **Database Connection Issues**
   ```bash
   kubectl exec -it <postgres-pod> -n sara -- psql -U sara -d sara
   ```

3. **External API Issues**
   ```bash
   kubectl exec -it <sara-pod> -n sara -- curl -v https://api.openai.com/v1/models
   ```

### Health Checks

```bash
# Check application health
curl https://sara.yourdomain.com/health

# Check readiness
curl https://sara.yourdomain.com/health/ready

# Check liveness
curl https://sara.yourdomain.com/health/live
```

### Log Analysis

```bash
# View application logs
kubectl logs -f deployment/sara-backend -n sara

# Search for errors
kubectl logs deployment/sara-backend -n sara | grep ERROR

# Follow logs with timestamps
kubectl logs -f deployment/sara-backend -n sara --timestamps
```

## Maintenance

### 1. Regular Updates

- Monitor for security updates
- Update dependencies regularly
- Test updates in staging environment
- Use rolling updates for zero-downtime deployments

### 2. Capacity Planning

- Monitor resource usage
- Plan for traffic growth
- Scale resources proactively
- Review and optimize costs

### 3. Security Maintenance

- Rotate API keys regularly
- Update SSL certificates
- Review access permissions
- Monitor for security vulnerabilities

## Support and Escalation

### 1. Monitoring Alerts

- Set up alerting for critical issues
- Define escalation procedures
- Maintain runbooks for common issues

### 2. Incident Response

- Document incident procedures
- Maintain communication channels
- Post-incident reviews and improvements

### 3. Documentation

- Keep deployment docs updated
- Document configuration changes
- Maintain troubleshooting guides
