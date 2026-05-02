# 🔥 Code-Swarm SOTA Implementation Plan
**Erstellt:** 2026-05-02  
**Status:** SOTA Best Practice für OpenCode Swarm System  
**Repo:** https://github.com/OpenSIN-Code/Code-Swarm

---

## 📊 KURZUEBERSICHT

| Aspekt | Status | Empfehlung |
|--------|--------|------------|
| **Agenten-Architektur** | ❌ Zu viele Hauptagenten | ✅ Max 2 auswählbare Agenten |
| **Swarm-System** | ⚠️ Fragmentiert | ✅ Code-Swarm LangGraph Pipeline |
| **Modell-Strategie** | ⚠️ Wild gemischt | ✅ Fireworks AI + Vercel DeepSeek V4 |
| **Subagenten** | ⚠️ Hauptagenten statt Subagenten | ✅ Alle spezialisierten Agenten als Subagenten |
| **Benchmarking** | ❌ Kein Benchmark-Tracking | ✅ swe_bench, humaneval_x, agentic_workflows |

---

## 🎯 VISION: SOTA SWARM ARCHITEKTUR

```
┌─────────────────────────────────────────────────────────────┐
│  SIN-Zeus (Fleet Commander) [FIREWORKS AI MINIMAX M2.7]    │
│  └─> LangGraph Pipeline                                     │
│      ├── Research Swarm (Athena, Argus, Daedalus)           │
│      ├── Planning Swarm (Prometheus)                        │
│      ├── Execution Layer (Atlas Backend, Iris Frontend)     │
│      ├── Validation Superlayer (Zeus)                       │
│      └── Memory + Feedback Loops                            │
└─────────────────────────────────────────────────────────────┘
          │
          ▼ (Delegiert an oh-my-opencode Subagenten)
┌─────────────────────────────────────────────────────────────┐
│  oh-my-opencode.json (SUBAGENTEN - NICHT auswählbar!)        │
│  ├── aegis, apollo (Build)                                  │
│  ├── argus, athena (Research)                               │
│  ├── audio_agent (Audio/STT)                                │
│  ├── multimedia_looker (Vision)                             │
│  └── web_recherche_agent (Web Research)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 ANALYSE: AKTUELLER STAND

### ✅ Was Code-Swarm bereits KORREKT hat:

| Feature | Status | Details |
|---------|--------|---------|
| **LangGraph Orchestration** | ✅ SOTA | StateGraph mit `task`, `research`, `plans`, `validated_plan`, `execution_log`, `memory`, `errors`, `feedback`, `metrics` |
| **Spezialisierte Agenten** | ✅ SOTA | Atlas (Backend), Hermes (Dispatch), Iris (Frontend), Janus (API), Hades (DB), Asclepius (QA), Prometheus (Planung), Zeus (Validation) |
| **Model-Hierarchie** | ✅ SOTA | Modelle sind definiert, aber noch nicht optimal |
| **Sub-Agenten System** | ✅ SOTA | `sub/` Agent mit aegis, apollo, argus, athena, audio_agent |
| **Kein tmux/worktrees** | ✅ SOTA | "KEIN tmux! KEINE Worktrees! KEIN Background-Dispatch!" — opencode-native Delegation |
| **Feedback Loops** | ✅ SOTA | `feedback/self_improvement.py`, `feedback/error_tracking.py` |
| **Memory Layer** | ✅ SOTA | `memory/vector_db.py`, `memory/state.py` |
| **Benchmarks** | ✅ SOTA | swe_bench, humaneval_x, agentic_workflows, terminal_bench |
| **JSON Output** | ✅ SOTA | Alle Agenten Output als JSON |

### ❌ Was in deinem aktuellen opencode.json FALSCH ist:

| Problem | Aktuell | SOTA Best Practice |
|---------|---------|-------------------|
| **35 auswählbare Agenten** | ❌ Zuviel! | ✅ Max **2** auswählbare Hauptagenten |
| **Sisyphus/Atlas/Hephaestus** | ❌ Generische Agenten | ✅ Ersetzen durch spezialisierte Code-Swarm Agenten |
| **Alle Agenten als "Hauptagenten"** | ❌ Kein Swarm | ✅ Nur SIN-Zeus + 1 User-Agent, Rest als Subagenten |
| **Omoc Swarm Commands** | ❌ Komplex | ✅ Code-Swarm LangGraph Swarm = SOTA |
| **Fireworks AI Account** | ❌ Gesperrt | ✅ Neuer Account bereits aktiv! |
| **Modelle nicht optimiert** | ❌ Wild gemischt | ✅ Fireworks AI + Vercel DeepSeek V4 Hierarchy |

---

## 🧠 GESAMMELTE KENNTNISSE AUS ANALYSE

### 1. Code-Swarm Repo Struktur

```
Code-Swarm/
├── README.md                # Hauptdokumentation
├── configs/
│   ├── opencode.json        # Haupt-Agenten-Definitionen
│   └── oh-my-opencode.json  # Sub-Agenten-Definitionen
├── langgraph/               # LangGraph Pipeline
│   ├── state.py             # StateGraph-Definition
│   └── graph.py             # Komplette Graph-Logik
├── agents/                  # Agenten-Prompts
│   ├── hermes/              # Dispatcher (Mistral Small)
│   ├── prometheus/          # System Planner (Mistral Large)
│   ├── zeus/                # Validation Superlayer (Mistral Medium)
│   ├── atlas/               # Backend Engineer (Mistral Large)
│   ├── iris/                # Frontend Engineer (Mistral Small)
│   ├── janus/               # API Architect (Mistral Small)
│   ├── hades/               # Database Architect (Mistral Small)
│   ├── asclepius/           # QA/Testing (Mistral Small)
│   └── sub/                 # Sub-Agenten
│       ├── aegis/
│       ├── apollo/
│       ├── argus/
│       ├── athena/
│       └── audio_agent/
├── cli/                     # CLI
│   └── main.py
├── memory/                  # Memory Layer
│   ├── vector_db.py
│   └── state.py
├── feedback/                # Feedback Loops
│   ├── self_improvement.py
│   └── error_tracking.py
└── code_swarm/              # Core System
    ├── __init__.py
    ├── events.py
    ├── memory.py
    └── registry.py
```

### 2. Verfügbare Modelle (via `opencode models`)

#### 🔥 FIREWORKS AI
| Modell | ID | Best Practice |
|--------|----|---------------|
| **Kimi K2.6** | `fireworks-ai/accounts/fireworks/models/kimi-k2p6` | Ultra-Coder-Modell, starkes Reasoning |
| **Minimax M2.7** | `fireworks-ai/accounts/fireworks/models/minimax-m2p7` | **DEIN ULTIMATIVES CODER-MODELL!** |
| **Qwen 3.6 Plus** | `fireworks-ai/accounts/fireworks/models/qwen3p6-plus` | Starkes Allround-Modell |

#### 🌐 VERCEL
| Modell | ID | Best Practice |
|--------|----|---------------|
| **DeepSeek V4 Pro** | `vercel/deepseek/deepseek-v4-pro` | Premium Coding + komplexe推理aufgaben |
| **DeepSeek V4 Flash** | `vercel/deepseek/deepseek-v4-flash` | Schnelles Coding, günstig |

#### ⚡ NVIDIA (Fallback)
| Modell | ID | Best Practice |
|--------|----|---------------|
| **Nemotron 3 Nano Omni** | `nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | Reasoning-Spezialist |
| **GLM 5.1** | `nvidia/z-ai/glm-5.1` | **FALLBACK** für NON-VISION Tasks |

### 3. Modell-Strategie (User Bestätigt)

**NUR** diese Modelle für NON-VISION Agenten:

| Modell | Provider | Primär/Fallback | Einsatz |
|--------|----------|-----------------|---------|
| `fireworks-ai/minimax-m2.7` | Fireworks AI | **PRIMARY** | Alle wichtigen Coding/Reasoning Tasks |
| `vercel/deepseek/deepseek-v4-flash` | Vercel | **PRIMARY (schnell)** | Research, einfache Tasks |
| `vercel/deepseek/deepseek-v4-pro` | Vercel | **PRIMARY (komplex)** | Komplexe Planung, Architektur |
| `nvidia/z-ai/glm-5.1` | NVIDIA | **FALLBACK** | Wenn andere nicht verfügbar |

### 4. Agenten-Zuordnung (SOTA Best Practice)

#### Hauptagenten (NUR 2 auswählbar!)
| Agent | Primär-Modell | Fallback | Einsatzbereich |
|-------|---------------|----------|----------------|
| **SIN-Zeus** (Fleet Commander) | `fireworks-ai/minimax-m2.7` | `vercel/deepseek/deepseek-v4-pro` | Oberbefehl, Dispatching, GitHub Issues |
| **coder-sin-swarm** (User Coder) | `fireworks-ai/minimax-m2.7` | `vercel/deepseek/deepseek-v4-flash` | User-facing Coding Tasks |

#### Subagenten (oh-my-opencode.json - NICHT auswählbar!)
| Agent | Primär-Modell | Fallback | Einsatzbereich |
|-------|---------------|----------|----------------|
| **hermes** (Dispatcher) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | Task-Verteilung, Swarm-Orchesterierung |
| **prometheus** (Planner) | `vercel/deepseek/deepseek-v4-pro` | `fireworks-ai/minimax-m2.7` | Architektur-Design, Feedback-Loops |
| **zeus** (Validator) | `vercel/deepseek/deepseek-v4-pro` | `fireworks-ai/minimax-m2.7` | Review, Security, Future-proofing |
| **atlas** (Backend) | `fireworks-ai/minimax-m2.7` | `vercel/deepseek/deepseek-v4-flash` | Backend, APIs, DB-Schema |
| **iris** (Frontend) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | UI/UX, pixel-perfect Designs |
| **janus** (API) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | REST/GraphQL APIs |
| **hades** (DB) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | DB-Design, SQLAlchemy |
| **asclepius** (QA) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | Tests, Edge Cases |
| **athena** (Research) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | Marktanalyse, Trends |
| **argus** (Web Research) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | Foren, Social Media |
| **daedalus** (Tech Research) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | Code-Analyse, Architektur |
| **hermes_scout** (Retriever) | `vercel/deepseek/deepseek-v4-flash` | `nvidia/z-ai/glm-5.1` | Schnelle Abfragen, API-Integration |
| **multimedia_looker** (Vision) | `nvidia/meta/llama-3.2-11b-vision-instruct` | `mistral/pixtral-12b` | Screenshots, GUI-Elemente |
| **audio_agent** (Audio) | `groq/whisper-large-v3` | `nvidia/openai/whisper-large-v3` | STT/TTS |
| **aegis** (Build) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | Build-Tasks |
| **apollo** (Build) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | Build-Tasks |
| **omoc** (Orchestrator) | `vercel/deepseek/deepseek-v4-flash` | `fireworks-ai/minimax-m2.7` | Swarm-Orchestrierung |
| **sin-executor-solo** | `fireworks-ai/minimax-m2.7` | `vercel/deepseek/deepseek-v4-flash` | Single-Agent Coding |

---

## 🚀 IMPLEMENTATION ROADMAP

### Phase 1: Plan erstellen ✅
- [x] Analyse aller Repos (OpenSIN-Code, Code-Swarm)
- [x] Sammlung aller verfügbaren Modelle
- [x] Bestimmung der optimalen Modell-Strategie
- [x] Dokumentation der SOTA Architektur

### Phase 2: Neue opencode.json erstellen
- [ ] **NUR 2 auswählbare Agenten:**
  - SIN-Zeus (Fleet Commander)
  - coder-sin-swarm (User Coder)
- [ ] Alle spezialisierten Agenten (Hermes, Prometheus, Atlas, etc.) als **Subagenten** verschieben
- [ ] Modelle auf Fireworks AI + Vercel DeepSeek V4 Hierarchy umstellen

### Phase 3: oh-my-opencode.json aktualisieren
- [ ] Alle Subagenten korrekt konfigurieren
- [ ] Modelle zuweisen (Fireworks AI + Vercel)
- [ ] Tools und Benchmarks definieren

### Phase 4: Code-Swarm LangGraph Pipeline integrieren
- [ ] State Management überprüfen
- [ ] Feedback Loops aktivieren
- [ ] Memory Layer konfigurieren

### Phase 5: Test und Validierung
- [ ] Benchmark-Tests durchführen (swe_bench, humaneval_x)
- [ ] Swarm-Koordination testen
- [ ] Performance-Metriken sammeln

---

## 📋 KONFIGURATIONS-BLOCKS

### Provider-Konfiguration (für opencode.json)

```json
"provider": {
  "fireworks-ai": {
    "npm": "@ai-sdk/openai-compatible",
    "name": "Fireworks AI",
    "options": {
      "baseURL": "https://api.fireworks.ai/inference/v1"
    },
    "models": {
      "minimax-m2.7": {
        "id": "fireworks-ai/accounts/fireworks/models/minimax-m2p7",
        "name": "Minimax M2.7 (Fireworks AI)",
        "limit": {
          "context": 262144,
          "output": 32768
        }
      }
    }
  },
  "vercel": {
    "models": {
      "deepseek-v4-flash": {
        "id": "vercel/deepseek/deepseek-v4-flash"
      },
      "deepseek-v4-pro": {
        "id": "vercel/deepseek/deepseek-v4-pro"
      }
    }
  },
  "nvidia-nim": {
    "npm": "@ai-sdk/openai",
    "name": "NVIDIA NIM",
    "options": {
      "baseURL": "https://integrate.api.nvidia.com/v1",
      "apiKey": "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"
    },
    "models": {
      "glm-5.1": {
        "id": "nvidia/z-ai/glm-5.1",
        "name": "GLM 5.1 (NVIDIA NIM)",
        "limit": {
          "context": 262144,
          "output": 32768
        }
      },
      "llama-3.2-11b-vision-instruct": {
        "id": "nvidia/meta/llama-3.2-11b-vision-instruct",
        "limit": {
          "context": 131072,
          "output": 32768
        },
        "modalities": {
          "input": ["text", "image"],
          "output": ["text"]
        }
      }
    }
  },
  "groq": {
    "models": {
      "whisper-large-v3": {
        "id": "groq/whisper-large-v3"
      }
    }
  }
}
```

---

## 🔧 BENCHMARK-TRACKING

| Benchmark | Beschreibung | Target Agents |
|-----------|--------------|---------------|
| **swe_bench_mini** | Software Engineering Benchmark Mini | Atlas, Janus, Hades |
| **humaneval_x** | HumanEval Extended | Atlas, Asclepius |
| **swe_bench_pro** | Software Engineering Benchmark Pro | Alle Coding-Agenten |
| **agentic_workflows** | Agentic Workflows Test | Hermes, Prometheus |
| **terminal_bench_2.0** | Terminal Benchmark | Hermes, Prometheus |
| **marktanalyse** | Marktanalyse Benchmark | Athena |
| **web_recherche** | Web Recherche Benchmark | Argus |
| **code_review** | Code Review Benchmark | Daedalus |
| **vision_gui_grounding** | Vision GUI Grounding | Multimedia-Looker |
| **mmmu_pro** | MMMU Pro | Multimedia-Looker |

---

## 📊 GEWÜNSCHTE ARCHITEKTUR (FINAL)

```
User-Interface (OpenCode)
    │
    ▼
┌─────────────────────────────────────────┐
│  SIN-Zeus (Fleet Commander)             │
│  Primär: fireworks-ai/minimax-m2.7      │
│  Fallback: vercel/deepseek-v4-pro       │
│  Entscheidet: Welche Agenten arbeiten   │
└─────────────────────────────────────────┘
    │
    ├──► LangGraph Pipeline
    │       │
    │       ├── Research Swarm
    │       │   ├── Athena (vercel/deepseek-v4-flash)
    │       │   ├── Argus (vercel/deepseek-v4-flash)
    │       │   └── Daedalus (vercel/deepseek-v4-flash)
    │       │
    │       ├── Planning Swarm
    │       │   └── Prometheus (vercel/deepseek-v4-pro)
    │       │
    │       ├── Execution Layer
    │       │   ├── Atlas Backend (fireworks-ai/minimax-m2.7)
    │       │   ├── Iris Frontend (vercel/deepseek-v4-flash)
    │       │   ├── Janus API (vercel/deepseek-v4-flash)
    │       │   └── Hades DB (vercel/deepseek-v4-flash)
    │       │
    │       └── Validation Superlayer
    │           └── Zeus (vercel/deepseek-v4-pro)
    │
    └──► Subagenten (oh-my-opencode.json)
            ├── aegis, apollo (Build)
            ├── hermes_scout (Retriever)
            ├── multimedia_looker (Vision)
            ├── audio_agent (Audio)
            └── omoc (Orchestrator)
```

---

## 🎯 ERFOLGSKRITERIEN

1. **Max 2 auswählbare Agenten** in opencode.json
2. **Alle spezialisierten Agenten** als Subagenten
3. **Nur Fireworks AI + Vercel Modelle** für NON-VISION
4. **Benchmark-Tracking** für alle Agenten
5. **LangGraph Pipeline** für Swarm-Koordination
6. **Feedback Loops** für Self-Improvement
7. **Memory Layer** für Vektor-DB

---

## 🔗 REFERENZEN

- [Code-Swarm Repo](https://github.com/OpenSIN-Code/Code-Swarm)
- [OpenSIN-Code Repo](https://github.com/OpenSIN-Code/OpenSIN-Code)
- [Benchmark Arena](https://github.com/SIN-Hackathon/benchmark-arena)
- [Infra-SIN-OpenCode-Stack](https://github.com/OpenSIN-AI/Infra-SIN-OpenCode-Stack)

---

**Nächster Schritt:** Neue opencode.json und oh-my-opencode.json erstellen basierend auf diesem Plan.