# 🔥 Code-Swarm: Agenten-Swarms für `opencode CLI`

> **🚫 KEIN tmux! KEINE Worktrees! KEIN Background-Dispatch!**
> Subagent-Delegation erfolgt **NUR** via opencode-native oh-my-opencode Sub-Sessions.

## 📌 Projektübersicht
Code-Swarm definiert **Haupt- und Sub-Agenten** für `opencode CLI`.
Die Architektur ist **opencode-native**:

```
SIN-Zeus (Hauptagent)
  ├── Delegiert an oh-my-opencode Subagenten
  │   ├── Athena → Research  (klickbar in opencode Session)
  │   ├── Argus  → Web-Suche (klickbar in opencode Session)
  │   └── ...    → Du siehst WAS sie tun!
  │
  └── LangGraph-Pipeline orchestriert den Flow
```

### Kernprinzipien
- **✅ Hauptagent → oh-my-opencode Subagenten** — INNERHALB der opencode Session
- **✅ Jeder Subagent ist klickbar & nachverfolgbar**
- **✅ Kein tmux, keine Worktrees, keine Background-Prozesse**
- **✅ Kein `call_omo_agent` für Subagent-Dispatch**
- **✅ opencode-native Delegation (das was funktioniert)**

### Enthält
- **Haupt-Agenten (`opencode.json`)** für Coding, Planung, Validation
- **Sub-Agenten (`oh-my-opencode.json`)** für Research, Vision, Audio, Web-Recherche
- **LangGraph-Pipeline** für StateGraph, Agenten-Nodes, Edges
- **Agenten-Prompts** für jeden Agenten
- **Feedback-Loops & Memory Layer** für Self-Improvement

## 📁 Struktur
```bash
Code-Swarm/
├── README.md                # Hauptdokumentation
├── opencode.json            # Haupt-Agenten-Definitionen
├── oh-my-opencode.json      # Sub-Agenten-Definitionen
├── langgraph/               # LangGraph-Pipeline
│   ├── state.py             # StateGraph-Definition
│   ├── graph.py             # Komplette Graph-Logik
├── agents/                  # Agenten-Prompts
│   ├── hermes/              
│   ├── prometheus/          
│   └── ...                  # Alle 22 Agenten
├── cli/                     # CLI
│   └── main.py              
├── memory/                  # Memory Layer
│   ├── vector_db.py         
│   └── state.py             
├── feedback/                # Feedback-Loops
│   ├── self_improvement.py  
│   └── error_tracking.py    
└── tests/                   # Tests
```

## 🚀 Quick Start
```bash
# 1. Repo klonen + Configs kopieren
gh repo clone OpenSIN-Code/Code-Swarm
cd Code-Swarm
cp configs/opencode.json ~/.config/opencode/opencode.json
cp configs/oh-my-opencode.json ~/.config/opencode/oh-my-opencode.json

# 2. SIN-Zeus delegiert Tasks an Subagenten
# Das passiert automatisch in opencode — kein extra CLI nötig!
```

## 📌 Modell-Hierarchie (von User bestätigt)

### 🥇 `mistral/mistral-large-latest` — **Stärkstes Modell**
- **Prometheus** (System Planner) — maximale Planungs-Qualität
- **Atlas** (Backend Engineer) — komplexe Backend-Architektur

### 🥈 `mistral/mistral-medium-latest` — **Stark + Ausgewogen**
- **Zeus** (Validation Superlayer) — kritische Reviews & Audits

### 🥉 `mistral/mistral-small-latest` — **Ultra-schnell + SOTA** (Standard für ALLE anderen)
- Alle anderen Haupt- & Sub-Agenten
- User bestätigt: "ultra viel besser als deepseek-v4-pro, glm-5.1"

### Spezialisiert
- **Mimo V2.5 Pro** — Vision/GUI-Agenten (Multimedia-Looker)
- **Whisper-Large-v3 + Coqui-TTS** — Audio-Agenten

## 🔗 Links
- [Benchmark-Arena](https://github.com/SIN-Hackathon/benchmark-arena) (Benchmarks, Tabellen, Empfehlungen)
- [Infra-SIN-OpenCode-Stack](https://github.com/OpenSIN-AI/Infra-SIN-OpenCode-Stack) (Agenten-Erklärungen)
