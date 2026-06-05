# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial SIN-Code-Bundle integration (ceo-audit workflow v3)
- OpenCode MCP server registration under `OpenSIN-Code/Code-Swarm`
- Repository-level `SIN_GITHUB_FALLBACK_TOKEN` secret for the App commenter fallback
- Multi-agent orchestration system (v0.4.0 Beta) for software engineering
- LangGraph state management, Simone-MCP AST-level code ops, Supabase persistence
- API: response time p99 <500ms, 1000+ concurrent users, 99.9% uptime target
- `agents/`, `api/`, `auth/`, `cache/`, `cli/`, `code_swarm/`, `db/`, `memory/`, `recursivemas/` modules
- Helm and k8s manifests for cloud deployment
- `PLAN.md` and MkDocs site under `docs/`

### Security
- All commits verified via `git-immortal-commit` (annotated tags)
- JWT-based auth for API endpoints (see `auth/` module)

