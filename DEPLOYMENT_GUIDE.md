# MOP Gear Metrology System - Production Deployment Guide

## Overview

This guide covers deploying the MOP Gear Metrology System to production with enterprise-grade security, monitoring, and scalability.

## 🔧 System Requirements

### Minimum Requirements
- **CPU**: 2 cores, 2.5 GHz
- **RAM**: 4 GB
- **Storage**: 10 GB available space
- **OS**: Windows 10/11, Linux (Ubuntu 18+), macOS 10.15+
- **Python**: 3.13+ (recommended)
- **Network**: HTTPS capability for API deployment

### Recommended Production Requirements
- **CPU**: 4+ cores, 3.0+ GHz
- **RAM**: 16 GB+ 
- **Storage**: SSD with 50 GB+ available
- **OS**: Ubuntu 20.04 LTS or Windows Server 2019+
- **Network**: Load balancer, dedicated domain
- **Database**: PostgreSQL or MongoDB (for session/metrics storage)

## 🚀 Quick Production Setup

### 1. Environment Preparation

```bash
# Clone repository
git clone https://github.com/bfoster59/MOP.git
cd MOP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install psutil gunicorn  # Additional production dependencies
```

### 2. Environment Configuration

Create `.env` file:
```env
# Production Environment Configuration
MOP_ENV=production
MOP_LOG_LEVEL=INFO
MOP_LOG_DIR=/var/log/mop
MOP_DEV_MODE=false

# Security
ADMIN_KEY=your-secure-admin-key-here
SECRET_KEY=your-secret-key-for-sessions

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_TIMEOUT=30

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
MAX_BATCH_SIZE=100

# Database (optional, for persistent storage)
DATABASE_URL=postgresql://user:pass@localhost/mop_db

# Monitoring
ENABLE_METRICS=true
METRICS_RETENTION_DAYS=30
HEALTH_CHECK_INTERVAL=30
```

### 3. Security Setup

```bash
# Create secure admin key
python -c "import secrets; print('ADMIN_KEY=' + secrets.token_urlsafe(32))" >> .env

# Set file permissions (Linux/macOS)
chmod 600 .env
chmod +x *.py

# Create log directory
mkdir -p /var/log/mop
chown $(whoami):$(whoami) /var/log/mop
```

### 4. Start Production Services

#### Option A: Gunicorn (Recommended for Linux)
```bash
# Start secure API with Gunicorn
gunicorn secure_api:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 30 \
    --log-level info \
    --access-logfile /var/log/mop/access.log \
    --error-logfile /var/log/mop/error.log \
    --daemon
```

#### Option B: Uvicorn (Cross-platform)
```bash
# Start secure API with Uvicorn
uvicorn secure_api:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log
```

#### Option C: Windows Service
```powershell
# Install as Windows Service (requires additional setup)
# Use NSSM or similar service manager
nssm install MOPGearAPI "C:\path\to\python.exe" "C:\path\to\MOP\secure_api.py"
nssm start MOPGearAPI
```

## 🔐 Security Configuration

### SSL/TLS Setup

#### With Nginx (Recommended)
```nginx
# /etc/nginx/sites-available/mop-api
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}

# Rate limiting configuration
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
}
```

#### Direct SSL with Uvicorn
```bash
# Generate self-signed certificate for testing
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Start with SSL
uvicorn secure_api:app \
    --host 0.0.0.0 \
    --port 8443 \
    --ssl-keyfile key.pem \
    --ssl-certfile cert.pem
```

### API Key Management

```python
# Create initial API keys
python -c "
from secure_api import APIKeyManager
admin_key = APIKeyManager.create_user('admin', ['calculate', 'batch', 'admin'])
user_key = APIKeyManager.create_user('production_client', ['calculate', 'batch'])
print(f'Admin Key: {admin_key}')
print(f'User Key: {user_key}')
"
```

### Firewall Configuration

```bash
# Linux (ufw)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct access to API
sudo ufw enable

# Windows (PowerShell as Administrator)
New-NetFirewallRule -DisplayName "MOP API HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
New-NetFirewallRule -DisplayName "Block MOP Direct" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Block
```

## 📊 Monitoring & Logging

### Production Monitoring Setup

```python
# Initialize monitoring in your startup script
from production_monitoring import initialize_production_monitoring

# Start monitoring
production_manager = initialize_production_monitoring(
    log_level="INFO",
    log_dir="/var/log/mop"
)

print("Production monitoring initialized")
```

### Log Rotation Configuration

```bash
# /etc/logrotate.d/mop-api
/var/log/mop/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload mop-api
    endscript
}
```

### Monitoring Endpoints

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (if implemented)
- **User Info**: `GET /auth/info`

### External Monitoring Integration

#### Prometheus Metrics (Optional)
```python
# Add to secure_api.py for Prometheus integration
from prometheus_client import Counter, Histogram, Gauge, generate_latest

REQUEST_COUNT = Counter('mop_requests_total', 'Total requests')
REQUEST_DURATION = Histogram('mop_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('mop_active_connections', 'Active connections')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🔧 Performance Optimization

### Application-Level Optimization

```python
# Enable caching in production
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_calculation(z, dp, pa, helix, t, d):
    # Cache frequently-used calculations
    return calculate_gear_parameters(z, dp, pa, helix, t, d)
```

### Database Configuration (Optional)

```sql
-- PostgreSQL setup for session storage
CREATE DATABASE mop_production;
CREATE USER mop_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE mop_production TO mop_user;

-- Tables for API keys and sessions
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    permissions TEXT[] NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    request_count INTEGER DEFAULT 0
);

CREATE TABLE calculation_logs (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    calculation_type VARCHAR(50),
    parameters JSONB,
    execution_time FLOAT,
    success BOOLEAN,
    error_type VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### System-Level Optimization

```bash
# Linux system optimization
# /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768

# /etc/sysctl.conf
net.core.somaxconn = 1024
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 8192
vm.swappiness = 10
```

## 🔄 Backup & Recovery

### Database Backup
```bash
#!/bin/bash
# backup_script.sh
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/backup/mop"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -h localhost -U mop_user mop_production > $BACKUP_DIR/db_backup_$DATE.sql

# Backup configuration
cp -r /etc/mop /backup/mop/config_$DATE/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
```

### Application Backup
```bash
# Backup critical application data
tar -czf /backup/mop/mop_app_$(date +%Y%m%d).tar.gz \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='venv' \
    /opt/mop/
```

## 📋 Health Checks & Alerts

### Docker Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### Systemd Service Health Check
```ini
# /etc/systemd/system/mop-api.service
[Unit]
Description=MOP Gear Metrology API
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/mop
Environment=PATH=/opt/mop/venv/bin
ExecStart=/opt/mop/venv/bin/gunicorn secure_api:app --bind 0.0.0.0:8000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### External Monitoring
```bash
# Uptime monitoring with curl
*/5 * * * * curl -f https://your-domain.com/health || echo "MOP API Health Check Failed" | mail -s "Alert" admin@company.com
```

## 🚨 Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
ps aux | grep python | grep mop
free -h

# Solutions:
# 1. Reduce worker count
# 2. Add memory limits
# 3. Implement result caching cleanup
```

#### Slow Response Times
```bash
# Check system resources
top -p $(pgrep -f secure_api)
iostat -x 1

# Check application logs
tail -f /var/log/mop/performance.log

# Solutions:
# 1. Increase worker count
# 2. Enable caching
# 3. Optimize database queries
```

#### High Error Rates
```bash
# Check error logs
tail -f /var/log/mop/errors.log
grep "ERROR" /var/log/mop/*.log | tail -20

# Check validation failures
grep "validation" /var/log/mop/calculations.log
```

### Debug Mode
```bash
# Enable debug logging temporarily
export MOP_LOG_LEVEL=DEBUG
export MOP_DEV_MODE=true
systemctl restart mop-api
```

## 📊 Production Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] API keys generated
- [ ] Database initialized (if used)
- [ ] Log directories created with proper permissions
- [ ] Backup procedures tested

### Post-Deployment
- [ ] Health check responding
- [ ] Authentication working
- [ ] Rate limiting functional
- [ ] Logging operational
- [ ] Monitoring active
- [ ] SSL/TLS verified
- [ ] Performance benchmarked
- [ ] Backup schedule activated

### Ongoing Maintenance
- [ ] Monitor system resources
- [ ] Review security logs
- [ ] Update API keys periodically
- [ ] Test backup restoration
- [ ] Update dependencies
- [ ] Monitor error rates
- [ ] Review performance metrics

## 📞 Support & Maintenance

### Regular Maintenance Tasks

**Daily**:
- Check system health
- Review error logs
- Monitor resource usage

**Weekly**:
- Review security logs
- Update system packages
- Verify backups

**Monthly**:
- Rotate API keys
- Performance review
- Security audit
- Update documentation

### Support Contacts
- **Technical Issues**: Check GitHub issues
- **Security Concerns**: Follow responsible disclosure
- **Performance Questions**: Review monitoring docs

---

**Production deployment requires careful attention to security, monitoring, and maintenance. This system provides enterprise-grade precision for gear metrology applications.** ⚙️🔧
