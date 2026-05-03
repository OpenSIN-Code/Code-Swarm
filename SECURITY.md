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
