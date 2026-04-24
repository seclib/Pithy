#!/bin/bash
# Checklist de vérification avant lancement de PIThy

echo "🔍 PIThy - Pre-launch Checklist"
echo "=================================="
echo ""

PASS=0
FAIL=0

check() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
        ((PASS++))
    else
        echo "❌ $1"
        ((FAIL++))
    fi
}

# 1. Vérifier les fichiers
echo "📁 Vérification des fichiers..."
test -f config.py && true || false; check "config.py existe"
test -f main.py && true || false; check "main.py existe"
test -f requirements.txt && true || false; check "requirements.txt existe"
test -f docker-compose.yml && true || false; check "docker-compose.yml existe"
test -f Dockerfile && true || false; check "Dockerfile existe"

# 2. Vérifier les modules
echo ""
echo "📦 Vérification des modules..."
test -d core && test -f core/agent.py && true || false; check "core/agent.py existe"
test -f core/brain.py && true || false; check "core/brain.py existe"
test -f core/router.py && true || false; check "core/router.py existe"
test -f llm/ollama_client.py && true || false; check "llm/ollama_client.py existe"
test -f memory/embeddings.py && true || false; check "memory/embeddings.py existe"
test -f memory/vector_store.py && true || false; check "memory/vector_store.py existe"
test -f tools/shell.py && true || false; check "tools/shell.py existe"
test -f tools/filesystem.py && true || false; check "tools/filesystem.py existe"

# 3. Vérifier la syntaxe Python
echo ""
echo "🐍 Vérification de la syntaxe Python..."
python3 -m py_compile core/*.py 2>/dev/null; check "core/ - syntaxe valide"
python3 -m py_compile llm/*.py 2>/dev/null; check "llm/ - syntaxe valide"
python3 -m py_compile memory/*.py 2>/dev/null; check "memory/ - syntaxe valide"
python3 -m py_compile tools/*.py 2>/dev/null; check "tools/ - syntaxe valide"

# 4. Vérifier les dépendances externes
echo ""
echo "🔧 Vérification des outils..."
command -v docker &> /dev/null; check "Docker installé"
command -v docker-compose &> /dev/null; check "Docker Compose installé"
command -v python3 &> /dev/null; check "Python 3 installé"

# 5. Vérifier la configuration
echo ""
echo "⚙️ Vérification de la configuration..."
grep -q "OLLAMA_URL" .env; check ".env contient OLLAMA_URL"
grep -q "DEFAULT_MODEL" .env; check ".env contient DEFAULT_MODEL"
grep -q "SAFE_MODE" .env; check ".env contient SAFE_MODE"

# 6. Vérifier la documentation
echo ""
echo "📚 Vérification de la documentation..."
test -f README.md && true || false; check "README.md existe"
test -f QUICKSTART.md && true || false; check "QUICKSTART.md existe"
test -f PROJECT_SUMMARY.md && true || false; check "PROJECT_SUMMARY.md existe"

# Résumé
echo ""
echo "=================================="
echo "✅ Passé: $PASS"
echo "❌ Échoué: $FAIL"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "🎉 Tous les contrôles sont passés!"
    echo "Vous pouvez lancer: docker-compose up --build"
    exit 0
else
    echo ""
    echo "⚠️ Certains contrôles ont échoué. Vérifiez l'installation."
    exit 1
fi
