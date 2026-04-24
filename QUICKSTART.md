# 🎯 Guide de démarrage PIThy

## Prérequis absolus

### 1. Ollama et modèles

```bash
# Installer Ollama (https://ollama.ai)
# Ou si vous utilisez Docker:
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Télécharger les modèles nécessaires
ollama pull dolphin-mistral:7b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text

# Vérifier que Ollama tourne
curl http://localhost:11434/api/tags
```

### 2. Docker et Docker Compose

```bash
# Vérifier l'installation
docker --version
docker-compose --version
```

## Démarrage rapide (Docker)

### Option 1: Utiliser le script

```bash
cd /home/fatsio/pithy
./start.sh
```

### Option 2: Commandes manuelles

```bash
cd /home/fatsio/pithy

# Démarrer les services
docker-compose up --build

# Dans un autre terminal, lancer l'agent
docker-compose exec pithy python main.py
```

### Option 3: Développement local (sans Docker)

```bash
cd /home/fatsio/pithy

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # ou: venv\Scripts\activate sur Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer ChromaDB (optionnel, pour le RAG)
docker run -p 8000:8000 chromadb/chroma:latest

# Lancer l'agent
python main.py
```

## Architecture détaillée

### Modules

| Module | Responsabilité |
|--------|-----------------|
| `core/agent.py` | Orchestration principale |
| `core/router.py` | Routing des requêtes |
| `core/brain.py` | Logique RAG et contexte |
| `llm/ollama_client.py` | Client Ollama |
| `memory/embeddings.py` | Gestion des embeddings |
| `memory/vector_store.py` | ChromaDB integration |
| `tools/shell.py` | Exécution commandes |
| `tools/filesystem.py` | Opérations fichiers |

### Flux de traitement d'une requête

```
Requête utilisateur
    ↓
Router.route() → Déterminer le type
    ↓
┌─────────────────────────────────────┐
│ Type détecté:                       │
│ • chat → Brain + Chat Model         │
│ • code → Brain + Code Model         │
│ • system → ShellTool + confirmation │
│ • memory → VectorStore search       │
└─────────────────────────────────────┘
    ↓
LLM.generate(prompt) → Réponse
    ↓
Brain.remember() → Mémorisation RAG
    ↓
Retour à l'utilisateur
```

## Configuration avancée

### Variables d'environnement (.env)

```env
# Connexion Ollama
OLLAMA_URL=http://localhost:11434

# Modèles
DEFAULT_MODEL=dolphin-mistral:7b
CODE_MODEL=qwen2.5-coder:7b
EMBED_MODEL=nomic-embed-text

# Sécurité
SAFE_MODE=true

# ChromaDB
CHROMA_URL=http://localhost:8000
```

### Modèles alternatifs

Vous pouvez remplacer les modèles par d'autres disponibles sur Ollama:

```bash
# Modèles de chat
ollama pull llama2:7b
ollama pull neural-chat:7b
ollama pull mistral:7b

# Modèles de code
ollama pull codellama:7b
ollama pull starcoder:7b

# Embeddings alternatifs
ollama pull all-minilm:latest
```

Puis mettre à jour `.env`:
```env
DEFAULT_MODEL=llama2:7b
CODE_MODEL=codellama:7b
EMBED_MODEL=all-minilm:latest
```

## Commandes Docker utiles

```bash
# Voir les logs du conteneur
docker-compose logs -f pithy

# Exécuter un shell dans le conteneur
docker-compose exec pithy bash

# Vérifier l'état des services
docker-compose ps

# Redémarrer les services
docker-compose restart

# Arrêter tous les services
docker-compose down

# Supprimer les volumes (attention: supprime la base de données)
docker-compose down -v
```

## Troubleshooting

### 1. "Connection refused" pour Ollama

```
[Erreur de connexion à Ollama]
```

**Vérifier:**
```bash
# Ollama tourne-t-il?
ps aux | grep ollama

# Port 11434 écoute-t-il?
netstat -tlnp | grep 11434
curl http://localhost:11434/api/tags
```

**Solution:**
```bash
# Lancer Ollama
ollama serve

# Ou si vous utilisez Docker:
docker run -d --gpus=all -v ollama:/root/.ollama \
  -p 11434:11434 --name ollama ollama/ollama
```

### 2. "Model not found"

```
[Erreur Ollama]
```

**Solution:**
```bash
# Télécharger le modèle
ollama pull dolphin-mistral:7b

# Vérifier
ollama list
```

### 3. ChromaDB ne répond pas

```
[Erreur initialisation VectorStore]
```

**Solution:**
```bash
# Vérifier que le service tourne
docker-compose ps chroma

# Redémarrer
docker-compose restart chroma

# Ou lancer manuellement
docker run -p 8000:8000 chromadb/chroma:latest
```

### 4. Permissions refusées dans Docker

```
Permission denied: './data/db'
```

**Solution:**
```bash
# Changer les permissions
chmod -R 777 data/

# Ou en root
sudo chmod -R 777 /home/fatsio/pithy/data
```

### 5. Module non trouvé

```
ModuleNotFoundError: No module named 'chromadb'
```

**Solution:**
```bash
# Dans le conteneur
docker-compose exec pithy pip install -r requirements.txt

# Ou localement
pip install -r requirements.txt
```

## Tests et validation

### Test des modules

```bash
# Test du client Ollama
docker-compose exec pithy python -c \
  "from llm.ollama_client import OllamaClient; \
  c = OllamaClient('dolphin-mistral:7b'); \
  print(c.generate('Test'))"

# Test du vector store
docker-compose exec pithy python -c \
  "from memory.vector_store import VectorStore; \
  vs = VectorStore(); \
  vs.add_texts(['Test'], ids=['1']); \
  print(vs.search('Test'))"

# Test du shell
docker-compose exec pithy python -c \
  "from tools.shell import ShellTool; \
  s = ShellTool(); \
  print(s.run('ls -la'))"
```

### Logs complets

```bash
# Tous les logs
docker-compose logs

# Logs en live
docker-compose logs -f

# Logs du conteneur pithy
docker-compose logs -f pithy

# Logs du conteneur chroma
docker-compose logs -f chroma
```

## Performance et optimisation

### Augmenter les ressources Docker

Éditer `docker-compose.yml`:
```yaml
services:
  pithy:
    ...
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Utiliser des GPU

```yaml
services:
  pithy:
    runtime: nvidia  # Nécessite nvidia-docker
    environment:
      - CUDA_VISIBLE_DEVICES=0
```

## Prochaines étapes

- [ ] Ajouter une interface web (FastAPI)
- [ ] Intégration VSCode via extension
- [ ] Support multi-utilisateurs
- [ ] Persistance des conversations
- [ ] Webhooks et plugins
- [ ] Fine-tuning des modèles

## Support

Pour les problèmes, consultez:
- Logs: `data/logs/pithy.log`
- Documentation: `README.md`
- Architecture: `Architecture.md`
