# Deployment to Vercel

## Prerequisites

- Vercel account & project created
- `vercel` CLI installed (`npm i -g vercel`)
- Supabase instance (managed PostgreSQL)
- Environment variables configured

## Step 1: Create Vercel Project

If not already created:

```bash
vercel create code-swarm
```

## Step 2: Configure Environment Variables

In Vercel dashboard → Settings → Environment Variables:

```
SUPABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_KEY=eyJhbGc...
SIMONE_MCP_URL=http://92.5.60.87:8234
PRIMARY_MODEL=gpt-4
VISION_MODEL=gpt-4-vision
SECRET_KEY=your-random-secret-key
ENVIRONMENT=production
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

## Step 3: Configure vercel.json

The project includes `vercel.json` with Serverless Function configuration:

```json
{
  "buildCommand": "pip install -r requirements.txt",
  "outputDirectory": "api",
  "functions": {
    "api/main.py": {
      "runtime": "python3.9",
      "memory": 3008,
      "maxDuration": 60
    }
  },
  "routes": [
    {"src": "^/api/(.*)", "dest": "api/main.py"},
    {"src": "^/(.*)$", "dest": "/api/main.py"}
  ],
  "env": {
    "ENVIRONMENT": "@env_production"
  }
}
```

## Step 4: Deploy

```bash
# Preview deployment
vercel preview

# Production deployment
vercel --prod
```

**Output:**
```
✅ Production: https://code-swarm-abc123.vercel.app
📝 Inspect: https://vercel.com/opensin/code-swarm/...
```

## Step 5: Verify Deployment

```bash
# Check health endpoint
curl https://code-swarm-abc123.vercel.app/health

# Check API docs
curl https://code-swarm-abc123.vercel.app/docs
```

## Monitoring

### Vercel Dashboard
- Deployment history → Logs
- Function logs → Real-time output
- Analytics → Request metrics

### Sentry Integration

Configure Sentry for error tracking:

```bash
# Install Sentry
pip install sentry-sdk

# Set environment variable
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
```

In `api/main.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
)
```

### Prometheus Metrics

Vercel exports metrics to `/metrics`:

```bash
curl https://code-swarm-abc123.vercel.app/metrics
```

Monitor key metrics:
- **API latency:** p50, p99
- **Error rate:** 4xx, 5xx responses
- **Task execution:** average duration
- **Agent utilization:** active agents

## Troubleshooting

### Build Fails

Check build logs in Vercel dashboard:
```
❌ Build error: Module 'simone_mcp' not found
→ Fix: Add to `requirements.txt`
```

### Function Timeout

If tasks exceed 60s:
- Split long tasks into subtasks
- Increase Vercel Function memory & timeout (max 3008 MB, 60s)
- Use external job queue (Upstash, AWS SQS)

### Cold Starts

Minimize cold start delay:
- Keep dependencies lean
- Pre-warm with health checks
- Use WebSocket for long-running tasks

### Database Connection Issues

```bash
# Verify Supabase URL format
echo $SUPABASE_URL
# Should be: postgresql://user:pass@db.supabase.co:5432/postgres

# Test connection
psql $SUPABASE_URL -c "SELECT 1"
```

## Rollback

If deployment has issues:

```bash
# List recent deployments
vercel list

# Rollback to previous
vercel rollback <deployment-url>
```

## Custom Domain

In Vercel dashboard → Settings → Domains:

```
Add domain: your-domain.com
```

DNS records automatically configured. Propagation: ~10 minutes.

## Performance Optimization

### Enable Compression
Already enabled in `vercel.json` for gzip.

### Database Connection Pooling
Supabase automatically manages 15 connections per client.

### CDN Caching
```python
# In api/main.py
@app.get("/agents")
def list_agents():
    response.headers["Cache-Control"] = "public, max-age=60"
    return _load_agents()
```

## Cost Estimation

| Service | Cost |
|---|---|
| Vercel (Hobby) | $0 |
| Supabase (Free) | $0 (up to 500MB) |
| Simone-MCP VM | ~$10-20/month (OCI) |
| **Total** | **~$10-20/month** |

Upgrade to Pro for higher limits.

Last updated: 2026-05-03
