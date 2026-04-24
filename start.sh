#!/bin/bash

# Script de démarrage rapide pour PIThy
# Usage: ./start.sh

set -e

echo "🚀 PIThy - Démarrage rapide"
echo "=============================="
echo ""

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    exit 1
fi

# Vérifier docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé"
    exit 1
fi

# Vérifier Ollama
echo "🔍 Vérification de Ollama..."
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Ollama n'est pas lancé sur localhost:11434"
    echo "   Démarrez Ollama avec: ollama serve"
    echo ""
    read -p "Continuer quand même? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Vérifier les modèles
echo "📦 Vérification des modèles Ollama..."
MODELS=("dolphin-mistral:7b" "qwen2.5-coder:7b" "nomic-embed-text")
for model in "${MODELS[@]}"; do
    if curl -s http://localhost:11434/api/tags | grep -q "$model"; then
        echo "  ✅ $model"
    else
        echo "  ⚠️  $model non trouvé"
        echo "     Téléchargez-le avec: ollama pull $model"
    fi
done

echo ""
echo "🐳 Démarrage Docker Compose..."
docker-compose up -d

echo ""
echo "⏳ Attente du démarrage des services..."
sleep 3

echo "✅ Services lancés!"
echo ""
echo "Étapes suivantes:"
echo "1. docker-compose logs -f pithy  (pour voir les logs)"
echo "2. docker-compose exec pithy python main.py  (pour lancer l'agent)"
echo ""
echo "Pour arrêter: docker-compose down"
