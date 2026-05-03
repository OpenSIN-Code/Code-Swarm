#!/bin/bash

# Code-Swarm Vercel Deployment Script
# Usage: ./vercel-deploy.sh [production|preview]

set -euo pipefail

ENVIRONMENT="${1:-preview}"
VERCEL_TOKEN="${VERCEL_TOKEN:-}"

if [ -z "$VERCEL_TOKEN" ]; then
  echo "ERROR: VERCEL_TOKEN environment variable is required"
  exit 1
fi

# Install Vercel CLI
echo "📦 Installing Vercel CLI..."
npm install -g vercel@latest

# Pull environment information
echo "🔍 Pulling environment information for $ENVIRONMENT..."
vercel pull --yes --environment=$ENVIRONMENT --token=$VERCEL_TOKEN

# Build project
echo "🏗️ Building project for $ENVIRONMENT..."
vercel build --$ENVIRONMENT --token=$VERCEL_TOKEN

# Deploy
echo "🚀 Deploying to $ENVIRONMENT..."
DEPLOY_OUTPUT=$(vercel deploy --prebuilt --token=$VERCEL_TOKEN)
DEPLOY_URL=$(echo "$DEPLOY_OUTPUT" | grep -Eo 'https://[^ ]+')

echo "✅ Deployment successful!"
echo "🔗 URL: $DEPLOY_URL"

echo ""
echo "📋 Next steps:"
echo "1. Set environment variables in Vercel dashboard:"
echo "   - SECRET_KEY (generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\")"
echo "   - ALLOWED_ORIGINS (comma-separated list)"
echo "   - ENVIRONMENT=$ENVIRONMENT"
echo "2. Configure custom domain if needed"
echo "3. Set up GitHub Actions for CI/CD (see SECURITY.md)"
