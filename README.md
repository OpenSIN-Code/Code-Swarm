# 🔥 Code-Swarm: Agenten-Swarms für `opencode CLI`

## 📌 Projektübersicht
Ein **vollständiges Agenten-System** für `opencode CLI` und `Code-Swarm`.
Enthält:
- **Haupt-Agenten (`opencode.json`)** für Coding, Planung, Validation
- **Sub-Agenten (`oh-my-opencode.json`)** für Research, Vision, Audio, Web-Recherche
- **LangGraph-Pipeline** für StateGraph, Agenten-Nodes, Edges
- **CI/CD-Pipelines** für GitHub Actions
- **Agenten-Prompts** für jeden Agenten
- **Feedback-Loops & Memory Layer** für Self-Improvement
- **CLI-Vorlage** (copy-paste ready)

## 📁 Struktur
```bash
Code-Swarm/
├── README.md                # Hauptdokumentation
├── opencode.json            # Haupt-Agenten-Definitionen
├── oh-my-opencode.json      # Sub-Agenten-Definitionen
├── langgraph/               # LangGraph-Pipeline
│   ├── state.py             # StateGraph-Definition
│   ├── graph.py             # Komplette Graph-Logik
│   └── nodes/               # Agenten-Nodes
├── agents/                  # Agenten-Definitionen & Prompts
│   ├── hermes/              # Prompts + Logik
│   ├── prometheus/          # Prompts + Logik
│   └── ...                  # Alle Agenten
├── cli/                     # Fertige CLI-Vorlage
│   ├── main.py              # CLI-Entry-Point
│   ├── commands.py          # CLI-Befehle
│   └── opencode.py          # `opencode CLI`-Befehl
├── memory/                  # Memory Layer
│   ├── vector_db.py         # Vektordatenbank
│   └── state.py             # LangGraph-State
├── feedback/                # Feedback-Loops & Self-Improvement
│   ├── self_improvement.py  # Self-Improvement Loop
│   ├── error_tracking.py    # Error Tracking
│   └── loops.py             # Feedback-Loops
├── tests/                   # Automatisierte Tests
│   ├── test_hermes.py        # Tests für Hermes
│   └── ...                  # Alle Tests
└── .github/workflows/       # CI/CD-Pipelines
    ├── test_hermes.yml      # Tests für Hermes
    └── ...                  # Alle Pipelines
```

## 🚀 Quick Start
```bash
# 1. Repo klonen
gh repo clone OpenSIN-Code/Code-Swarm
cd Code-Swarm

# 2. Agenten-System initialisieren
python cli/main.py init

# 3. Task ausführen
python cli/main.py run "Installiere Redis + Konfiguriere + Teste"

# 4. Zustand inspizieren
python cli/main.py inspect
```

## 📌 Wichtige Erkenntnisse
- **Mistral Small 4 (`mistral/mistral-small-latest`)** ist **ultra-schnell + SOTA** für Frontend-Agenten (Iris) und **alle Agenten, die schnell + schlau sein müssen**
- **DeepSeek V4-Pro** ist **beste Wahl für Backend-Agenten (Atlas, Janus, Hades)**
- **GLM-5.1** ist **beste Wahl für Lang-horizontale Agenten (Hermes, Prometheus, Zeus)**
- **Mimo V2.5 Pro** ist **beste Wahl für Vision/GUI-Agenten (Multimedia-Looker)**

## 🔗 Links
- [Benchmark-Arena](https://github.com/SIN-Hackathon/benchmark-arena) (Benchmarks, Tabellen, Empfehlungen)
- [Infra-SIN-OpenCode-Stack](https://github.com/OpenSIN-AI/Infra-SIN-OpenCode-Stack) (Agenten-Erklärungen)
