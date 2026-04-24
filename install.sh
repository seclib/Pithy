#!/bin/bash
# Installation complète de PIThy sur Linux

set -e

echo "🚀 Installation de PIThy"
echo "======================="
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Vérifier les prérequis
echo -e "${YELLOW}[1/5]${NC} Vérification des prérequis..."

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker n'est pas installé${NC}"
    echo "Installation recommandée:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Compose n'est pas installé${NC}"
    echo "Installation:"
    echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    echo "  sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi

if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama n'est pas installé${NC}"
    echo "Installation:"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

echo -e "${GREEN}✅ Prérequis OK${NC}"

# 2. Télécharger les modèles Ollama
echo ""
echo -e "${YELLOW}[2/5]${NC} Vérification des modèles Ollama..."

OLLAMA_RUNNING=$(curl -s http://localhost:11434/api/tags 2>/dev/null || echo "")

if [ -z "$OLLAMA_RUNNING" ]; then
    echo -e "${YELLOW}⚠️  Ollama n'est pas lancé${NC}"
    echo "Lancez Ollama dans un terminal:"
    echo "  ollama serve"
    echo ""
    read -p "Appuyez sur Entrée quand Ollama est lancé..."
fi

echo "Téléchargement des modèles (cela peut prendre du temps)..."
ollama pull dolphin-mistral:7b &
OLLAMA_PID=$!

echo "Pendant ce temps, téléchargement des autres modèles..."
ollama pull qwen2.5-coder:7b &

echo "Et des embeddings..."
ollama pull nomic-embed-text &

wait $OLLAMA_PID
echo -e "${GREEN}✅ Modèles téléchargés${NC}"

# 3. Configurer le projet
echo ""
echo -e "${YELLOW}[3/5]${NC} Configuration du projet..."

# Créer les répertoires de données
mkdir -p data/{db,logs}
chmod 777 data/{db,logs}

echo -e "${GREEN}✅ Répertoires créés${NC}"

# 4. Vérifier l'installation
echo ""
echo -e "${YELLOW}[4/5]${NC} Vérification de l'installation..."

bash check.sh

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Certains contrôles ont échoué${NC}"
    exit 1
fi

# 5. Fin
echo ""
echo -e "${YELLOW}[5/5]${NC} Installation terminée!"
echo ""
echo -e "${GREEN}🎉 PIThy est prêt à être lancé!${NC}"
echo ""
echo "Commandes de démarrage:"
echo ""
echo "  1. Build et lancement:"
echo "     docker-compose up --build"
echo ""
echo "  2. Dans un autre terminal, lancez l'agent:"
echo "     docker-compose exec pithy python main.py"
echo ""
echo "  3. Ou en mode développement (sans Docker):"
echo "     python3 main.py"
echo ""
echo "Documentation:"
echo "  - README.md        : Documentation générale"
echo "  - QUICKSTART.md    : Guide de démarrage"
echo "  - PROJECT_SUMMARY.md : Résumé du projet"
echo ""
