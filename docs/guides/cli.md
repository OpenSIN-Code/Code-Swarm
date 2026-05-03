# CLI Usage Guide

## Overview

The Code-Swarm CLI provides commands for managing agents, tasks, and deployments.

## Commands

### Server Management

#### Start API Server
```bash
code-swarm api [OPTIONS]

Options:
  --host TEXT          Host to bind to (default: 127.0.0.1)
  --port INTEGER       Port to bind to (default: 8000)
  --reload             Enable auto-reload on code changes
  --workers INTEGER    Number of worker processes (default: 1)
```

**Example:**
```bash
code-swarm api --host 0.0.0.0 --port 8000 --reload
```

### Agent Management

#### List Agents
```bash
code-swarm agents list [OPTIONS]

Options:
  --role TEXT          Filter by role (backend, frontend, etc.)
  --status TEXT        Filter by status (idle, active, completed)
  --format TEXT        Output format: json, table (default: table)
```

**Example:**
```bash
code-swarm agents list --role backend --format json
```

**Output:**
```
┌─────────┬─────────┬─────────┬──────────┐
│ ID      │ Name    │ Role    │ Status   │
├─────────┼─────────┼─────────┼──────────┤
│ agent_1 │ solver  │ backend │ idle     │
│ agent_2 │ designer│ frontend│ active   │
└─────────┴─────────┴─────────┴──────────┘
```

#### Create Agent
```bash
code-swarm agents create [OPTIONS]

Options:
  --name TEXT          Agent name (required)
  --model TEXT         Model ID (default: gpt-4)
  --role TEXT          Agent role (backend, frontend, etc.)
  --capabilities TEXT  Comma-separated capabilities
```

**Example:**
```bash
code-swarm agents create \
  --name solver \
  --role backend \
  --capabilities code-generation,testing
```

#### Show Agent Details
```bash
code-swarm agents show <agent_id>
```

**Output:**
```
Agent: solver (agent_1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model:         gpt-4
Role:          backend
Status:        idle
Capabilities:  code-generation, testing
Created:       2026-05-03 10:00:00 UTC
```

### Task Management

#### List Tasks
```bash
code-swarm tasks list [OPTIONS]

Options:
  --status TEXT        Filter by status (pending, active, completed)
  --assigned-to TEXT   Filter by agent
  --format TEXT        Output format: json, table
```

**Example:**
```bash
code-swarm tasks list --status pending
```

#### Create Task
```bash
code-swarm tasks create [OPTIONS]

Options:
  --title TEXT         Task title (required)
  --description TEXT   Detailed description
  --priority INTEGER   Priority level 1-10
  --assigned-to TEXT   Agent to assign task to
```

**Example:**
```bash
code-swarm tasks create \
  --title "Fix login endpoint" \
  --description "Add JWT refresh token" \
  --priority 8 \
  --assigned-to solver
```

#### Show Task Details & Logs
```bash
code-swarm tasks show <task_id>
```

**Output:**
```
Task: Fix login endpoint (task_1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status:       active
Priority:     8/10
Assigned:     solver
Created:      2026-05-03 10:00:00 UTC
Progress:     ████████░░ 80%

Last 5 log entries:
  [10:05:20] Analyzing endpoint...
  [10:05:25] Found 3 issues
  [10:05:30] Generating fix...
  [10:06:15] Testing fix...
  [10:06:45] Fix validated ✓
```

#### Watch Task Execution (Real-time)
```bash
code-swarm tasks watch <task_id>

Flags:
  --follow     Continue watching until completion
  --filter     Filter logs by agent or action
```

**Example:**
```bash
code-swarm tasks watch task_1 --follow
```

**Output (streaming):**
```
task_1: hermes | Distributing task...
task_1: prometheus | Analyzing requirements...
task_1: zeus | Planning architecture...
task_1: atlas | Generating backend...
task_1: iris | Generating frontend...
task_1: [COMPLETE] ✓ All systems ready
```

### Deployment

#### Deploy to Vercel
```bash
code-swarm deploy vercel [OPTIONS]

Options:
  --project TEXT       Vercel project name
  --env-file TEXT      Path to .env file
  --production         Deploy to production
```

**Example:**
```bash
code-swarm deploy vercel --project code-swarm --production
```

#### Deploy to Kubernetes
```bash
code-swarm deploy k8s [OPTIONS]

Options:
  --context TEXT       Kubernetes context
  --namespace TEXT     Target namespace
  --replicas INTEGER   Number of replicas
```

### Database

#### Initialize Database
```bash
code-swarm db init

Creates tables and indices in Supabase.
```

#### Run Migrations
```bash
code-swarm db migrate

Applies pending schema migrations.
```

### Monitoring

#### Show System Status
```bash
code-swarm status

Output:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 API Server: healthy
🟢 Database: connected
🟢 Simone-MCP: connected
🟡 Cache: degraded

Active Agents: 3
Running Tasks: 12
Avg Response Time: 145ms
```

#### Show Logs
```bash
code-swarm logs [OPTIONS]

Options:
  --tail INTEGER       Show last N lines (default: 50)
  --agent TEXT         Filter by agent
  --level TEXT         Log level (debug, info, warning, error)
  --follow             Follow logs in real-time
```

**Example:**
```bash
code-swarm logs --agent solver --level error --follow
```

### Configuration

#### Show Config
```bash
code-swarm config show

Output:
SUPABASE_URL: postgresql://...
SIMONE_MCP_URL: http://92.5.60.87:8234
PRIMARY_MODEL: gpt-4
ENVIRONMENT: production
```

#### Edit Config
```bash
code-swarm config set <KEY> <VALUE>

Example:
code-swarm config set PRIMARY_MODEL gpt-4-turbo
```

## Environment Variables

The CLI respects all environment variables defined in `.env`:

```bash
export SUPABASE_URL=postgresql://...
export SIMONE_MCP_URL=http://92.5.60.87:8234
export PRIMARY_MODEL=gpt-4
export SECRET_KEY=your-secret-key
```

## Tips & Tricks

### Batch Operations
```bash
# Create 5 agents at once
for i in {1..5}; do
  code-swarm agents create --name "agent-$i" --role backend
done
```

### Export Task Results
```bash
# Export to JSON
code-swarm tasks list --format json > tasks.json

# Export to CSV
code-swarm tasks list --format csv > tasks.csv
```

### Debug Mode
```bash
# Enable debug logging
DEBUG=1 code-swarm api

# Verbose output
code-swarm --verbose agents list
```

### Shell Completion
```bash
# Bash
eval "$(code-swarm --bash-complete)"

# Zsh
eval "$(code-swarm --zsh-complete)"
```

## Help

```bash
# Global help
code-swarm --help

# Command-specific help
code-swarm agents --help
code-swarm tasks --help
code-swarm deploy --help
```

Last updated: 2026-05-03
