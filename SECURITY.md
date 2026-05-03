# Code-Swarm Security Best Practices

## 🔒 Security Hardening (SOTA 2026)

### 1. SECRET_KEY Management

**Production Requirement**:
- MUST be supplied via `SECRET_KEY` environment variable
- MUST be strong random value (64+ bytes)
- MUST NOT be the legacy default
- Generate with: `python -c "import secrets; print(secrets.token_urlsafe(64))"`

**Development Behavior**:
- Ephemeral key generated on boot
- Tokens invalidated on restart
- Loud warning logged

### 2. CORS Configuration

**Production Requirement**:
- MUST declare explicit origins via `ALLOWED_ORIGINS`
- Comma-separated list (no spaces)
- Example: `https://app.opensin.ai,https://docs.opensin.ai`

**Development Behavior**:
- Falls back to localhost origins
- Loud warning logged

### 3. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ Production | Strong random secret |
| `ALLOWED_ORIGINS` | ✅ Production | Comma-separated allowed origins |
| `ENVIRONMENT` | ❌ | `development`, `staging`, `production` |
| `CODE_SWARM_BASE_DIR` | ❌ | Base directory for data storage |

### 4. Security Headers

- `Content-Security-Policy`: Restricted sources
- `X-Frame-Options`: DENY
- `X-Content-Type-Options`: nosniff
- `Strict-Transport-Security`: max-age=31536000; includeSubDomains

### 5. Rate Limiting

- 1000 requests/hour default
- Configurable via `RATE_LIMIT` env var
- Redis-backed for distributed environments

### 6. Authentication

- JWT with HS256
- 15 minute token expiration
- Refresh tokens with 7 day expiration
- RBAC with 3 roles: `user`, `agent`, `admin`

### 7. Monitoring

- Prometheus metrics enabled by default
- Sentry integration optional
- Health checks: `/health`, `/ready`

## 🛡️ Deployment Security

### Production Checklist

1. [ ] `SECRET_KEY` set to strong random value
2. [ ] `ALLOWED_ORIGINS` set to production domains
3. [ ] `ENVIRONMENT=production`
4. [ ] Database with TLS connection
5. [ ] Redis with TLS connection
6. [ ] All secrets in secure vault (not in repo)
7. [ ] CI/CD pipeline with security scanning

### Security Scanning

- Trivy: Filesystem scanning for vulnerabilities
- Bandit: Python code security analysis
- Safety: Python dependency vulnerability scanning
- Snyk: Container image scanning

## 🚨 Incident Response

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| Critical | < 1 hour | CEO + Security Team |
| High | < 4 hours | Security Team |
| Medium | < 24 hours | Development Team |
| Low | < 72 hours | Developer On-Call |

## 🚀 CI/CD Pipeline (GitHub Actions)

### Test Pipeline (`.github/workflows/test.yml`)

```yaml
name: Code-Swarm Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: "3.11"

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ --cov=api --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

### Security Pipeline (`.github/workflows/security.yml`)

```yaml
name: Code-Swarm Security Scan

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * *'

env:
  PYTHON_VERSION: "3.11"

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Security scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "."
          format: "table"
          exit-code: "1"
          severity: "CRITICAL,HIGH"
```

### Deployment Pipeline (manuell)

1. **Vercel Deployment**:
   ```bash
   npm install -g vercel
   vercel pull --yes --environment=production --token=$VERCEL_TOKEN
   vercel build --prod --token=$VERCEL_TOKEN
   vercel deploy --prebuilt --prod --token=$VERCEL_TOKEN
   ```

2. **Environment Variables**:
   ```bash
   # Set required env vars in Vercel
   vercel env add SECRET_KEY production
   vercel env add ALLOWED_ORIGINS production
   vercel env add ENVIRONMENT production
   ```

## 🚀 Vercel Deployment

### Deployment Script

```bash
# Make executable
chmod +x vercel-deploy.sh

# Deploy to preview
./vercel-deploy.sh preview

# Deploy to production
./vercel-deploy.sh production
```

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Strong random secret | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `ALLOWED_ORIGINS` | Comma-separated allowed origins | `https://app.opensin.ai,https://docs.opensin.ai` |
| `ENVIRONMENT` | `production` or `preview` | `production` |
| `VERCEL_TOKEN` | Vercel API token | `vercel token create` |

### Post-Deployment Checklist

1. [ ] Verify `/health` endpoint returns 200 OK
2. [ ] Verify `/docs` Swagger UI is accessible
3. [ ] Test authentication flow
4. [ ] Verify CORS headers are correct
5. [ ] Set up monitoring and alerts
6. [ ] Configure custom domain
7. [ ] Set up SSL certificates

## 🚀 Production Deployment

### Deployment Script

```bash
# Make executable
chmod +x vercel-deploy-prod.sh

# Deploy to production
./vercel-deploy-prod.sh
```

### Environment Variables

| Variable | Production Value | Description |
|----------|------------------|-------------|
| `SECRET_KEY` | `FJ9wyxt_wMEPV6pYvu2Ptt_pP04q1OjbNgVM3ZnhltUD6zPnHQh-sAqXajbuohLUq7nwe6Iihj0L6RnpMknyog` | Strong random secret |
| `ALLOWED_ORIGINS` | `https://app.opensin.ai,https://docs.opensin.ai` | Production domains |
| `ENVIRONMENT` | `production` | Production mode |
| `DATABASE_URL` | `postgresql://opensin:S3cur3P@ssw0rd@db.opensin.ai:5432/code_swarm_prod` | Production database |
| `REDIS_URL` | `redis://:R3d1sP@ssw0rd@cache.opensin.ai:6379/0` | Production cache |
| `PRIMARY_MODEL` | `fireworks-ai/minimax-m2.7` | Primary agent model |
| `VISION_MODEL` | `nvidia/nvidia/nemotron-3-nano-omni` | Vision model |

### Post-Deployment

1. **Health Check**
   ```bash
   curl https://api.opensin.ai/health
   ```

2. **Metrics**
   ```bash
   curl https://api.opensin.ai/metrics
   ```

3. **Swagger UI**
   ```bash
   https://api.opensin.ai/docs
   ```

### Monitoring

- **Prometheus**: https://prometheus.opensin.ai
- **Grafana**: https://grafana.opensin.ai/d/code-swarm
- **Sentry**: https://sentry.io/organizations/opensin/
- **Logs**: https://logs.opensin.ai

### Alerting

- **Critical**: CEO + Security Team
- **High**: Security Team
- **Medium**: Development Team
- **Low**: Developer On-Call
