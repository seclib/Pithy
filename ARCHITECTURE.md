# PIThy Architecture

Voici l'architecture complète et unifiée de la plateforme **PIThy AI Automation Platform Core**.

```text
                    ┌─────────────────────────────┐
                    │         USER / CLI          │
                    │  (pithy-cli / VSCode)       │
                    └────────────┬────────────────┘
                                 │
                                 ▼
        ┌─────────────────────────────────────────────┐
        │             pithy CORE AGENT                │
        │─────────────────────────────────────────────│
        │  🧠 LLM Router (Ollama)                     │
        │  🧠 Intent Detection Engine                 │
        │  🧠 Multi-Model Orchestrator               │
        │  📚 RAG Context Builder                    │
        │  🧰 Tool Dispatcher (system actions)        │
        └────────────┬──────────────────────────────┘
                     │
     ┌───────────────┼───────────────────────────────┐
     ▼               ▼                               ▼

┌────────────┐  ┌───────────────┐        ┌────────────────────┐
│   MEMORY    │  │    TOOLS      │        │      INFRA         │
│   LAYER     │  │   LAYER       │        │    MANAGER         │
└────────────┘  └───────────────┘        └────────────────────┘
     │               │                               │
     ▼               ▼                               ▼

📚 RAG SYSTEM       🧰 Shell Tool              ⚙️ Docker Controller
- ChromaDB          - bash exec safe          - start/stop services
- Embeddings        - filesystem access       - lifecycle mgmt
- long-term memory  - logs analyzer           - container orchestration

                     │                               │
                     └──────────────┬────────────────┘
                                    ▼

                     ┌─────────────────────────────┐
                     │   PREDICTIVE SCALING        │
                     │─────────────────────────────│
                     │ 🔮 usage prediction         │
                     │ 🚀 pre-start services       │
                     │ 💤 idle detection           │
                     │ ⚡ warm/cold switching      │
                     └────────────┬────────────────┘
                                  │
                                  ▼

        ┌─────────────────────────────────────────────┐
        │             DOCKER COMPOSE STACK            │
        │─────────────────────────────────────────────│
        │  🟢 pithy agent service                    │
        │  🟢 Ollama LLM runtime                     │
        │  🟢 ChromaDB vector database               │
        │  🟡 optional tools services                │
        └─────────────────────────────────────────────┘


                     ┌─────────────────────────────┐
                     │     PLUGIN SYSTEM           │
                     │─────────────────────────────│
                     │ 🔌 dynamic loading          │
                     │ 🔌 hooks system             │
                     │ 🔌 runtime extensions       │
                     └────────────┬────────────────┘
                                  │
                                  ▼

        ┌─────────────────────────────────────────────┐
        │            EXTENSION LAYER                  │
        │─────────────────────────────────────────────│
        │ VSCode plugin                              │
        │ Git automation                             │
        │ system monitoring plugins                  │
        │ custom AI behaviors                        │
        └─────────────────────────────────────────────┘
```

## 🧩 Composants Clés

### 1. Agent Layer (`core/`)
L'intelligence centrale. Elle route les requêtes vers les modèles appropriés (Ollama) et gère le contexte via le RAG.
- **Router** : Détecte l'intention (Chat, Code, System).
- **Orchestrator** : Sélectionne la stratégie de réponse.
- **Brain** : Construit le contexte final.

### 2. Infra Layer (`infra_manager/`)
Le gestionnaire de ressources Docker. Il assure que les services nécessaires sont démarrés au bon moment.
- **Predictive Scaling Engine** : Anticipe l'usage futur.
- **Docker Controller** : Manipule les containers.
- **AutoScaler** : La boucle de contrôle autonome.

### 3. Memory & Tools Layer (`memory/`, `tools/`)
- **RAG** : Stockage vectoriel via ChromaDB.
- **Tools** : Shell sécurisé, accès fichiers, analyse de logs, gestion des ressources.

### 4. Extension Layer (`plugins/`, `core/unified_plugins.py`)
Système de plugins unifié permettant d'étendre la plateforme tant au niveau de l'IA (outils) que de l'infrastructure (hooks).

---
*PIThy — Autonomous AI Operating Layer*
