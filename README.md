# 🧠 PIThy - Assistant IA Local

Un assistant IA modulaire et intelligent basé sur **Ollama**, **ChromaDB** et **Docker**.

## ✨ Caractéristiques

- 💬 **Chat naturel** avec Ollama (modèle par défaut)
- 💻 **Génération de code** avec modèle spécialisé
- 📚 **Mémoire RAG** avec embeddings vectoriels
- 🔧 **Exécution de commandes système** sécurisée
- 🐳 **Entièrement dockerisé** avec docker-compose
- 🎯 **Routing intelligent** des requêtes
- 🔐 **Mode sécurisé** par défaut

## 🚀 Démarrage rapide

### Prérequis

- Docker et Docker Compose
- Ollama installé et lancé localement sur `localhost:11434`
- Modèles Ollama préalablement téléchargés:
  ```bash
  ollama pull dolphin-mistral:7b
  ollama pull qwen2.5-coder:7b
  ollama pull nomic-embed-text
  ```

### Lancement

1. **Démarrer l'application complète:**
   ```bash
   docker-compose up --build
   ```

2. **Se connecter au conteneur PIThy:**
   ```bash
   docker-compose exec pithy bash
   ```

3. **Lancer l'agent dans le conteneur:**
   ```bash
   python main.py
   ```

### Lancement local (sans Docker)

```bash
# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
export OLLAMA_URL=http://localhost:11434
export CHROMA_URL=http://localhost:8000

# Lancer ChromaDB (si besoin)
docker run -p 8000:8000 chromadb/chroma:latest

# Démarrer l'agent
python main.py
```

## 📝 Exemples d'utilisation

```
>> Salut, comment tu vas?
🤖 [Réponse via chat LLM]

>> Écris une fonction Python pour calculer la suite de Fibonacci
🤖 [Code généré via modèle code]

>> Exécute ls -la
⚠️ Exécuter: ls -la? (y/n): y
🤖 [Résultat de la commande]

>> Souviens-toi: Les bases de données distribuées...
🤖 ✅ Information mémorisée

>> Qu'est-ce que je t'ai dit sur...
🤖 [Recherche dans la mémoire RAG]
```

## 📁 Architecture

```
pithy/
├── core/              # Agent, routing, brain
├── llm/              # Interface Ollama
├── memory/           # RAG avec ChromaDB
├── tools/            # Shell et filesystem
├── data/             # Logs et base de données
├── main.py           # Point d'entrée
├── config.py         # Configuration
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## ⚙️ Configuration

Éditer `.env`:

```env
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=dolphin-mistral:7b
CODE_MODEL=qwen2.5-coder:7b
EMBED_MODEL=nomic-embed-text
SAFE_MODE=true
CHROMA_URL=http://localhost:8000
```

## 🔐 Sécurité

- **SAFE_MODE activé par défaut** : les commandes système demandent confirmation
- **Commandes autorisées** : `ls`, `pwd`, `cat`, `grep`, `find`, `head`, `tail`, etc.
- **Paths sécurisés** : les opérations filesystem restent dans le répertoire autorisé

## 📊 Logs

Les logs sont disponibles dans `data/logs/pithy.log`

```bash
# Consulter les logs
tail -f data/logs/pithy.log
```

## 🧪 Troubleshooting

### Erreur de connexion Ollama

```
[Erreur de connexion à Ollama]
```

**Solution:** Vérifier que Ollama est lancé:
```bash
ollama serve
```

### ChromaDB non accessible

```
[Erreur initialisation VectorStore]
```

**Solution:** Lancer ChromaDB séparément:
```bash
docker run -p 8000:8000 chromadb/chroma:latest
```

### Module non trouvé

```
ModuleNotFoundError: No module named 'chromadb'
```

**Solution:** Réinstaller les dépendances:
```bash
pip install -r requirements.txt
```

## 📦 Dépendances

- `requests` - Requêtes HTTP vers Ollama
- `chromadb` - Vector store
- `numpy` - Calculs numériques
- `python-dotenv` - Gestion des variables d'environnement

## 🎯 Roadmap

- [ ] Interface web (FastAPI)
- [ ] Intégration VSCode
- [ ] Plugins système
- [ ] Support multi-utilisateurs
- [ ] Webhooks

## 📄 Licence

MIT

## 👨‍💻 Auteur

PIThy - Assistant IA Local
