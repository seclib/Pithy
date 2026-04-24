#!/usr/bin/env python3
"""Test de syntaxe et imports du projet PIThy"""

import sys

tests = [
    ("config", lambda: __import__('config')),
    ("llm.ollama_client", lambda: __import__('llm.ollama_client', fromlist=['OllamaClient'])),
    ("core.router", lambda: __import__('core.router', fromlist=['Router'])),
    ("memory.embeddings", lambda: __import__('memory.embeddings', fromlist=['Embeddings'])),
    ("memory.vector_store", lambda: __import__('memory.vector_store', fromlist=['VectorStore'])),
    ("tools.shell", lambda: __import__('tools.shell', fromlist=['ShellTool'])),
    ("core.agent", lambda: __import__('core.agent', fromlist=['Agent'])),
]

print("🔍 Test de syntaxe et imports...\n")

passed = 0
failed = 0

for name, test in tests:
    try:
        test()
        print(f"✅ {name}")
        passed += 1
    except Exception as e:
        print(f"❌ {name}: {e}")
        failed += 1

print(f"\n📊 Résultat: {passed} passés, {failed} échoués")
sys.exit(0 if failed == 0 else 1)
