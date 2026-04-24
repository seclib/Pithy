"""
PIThy CLI — Outil de contrôle de la plateforme
"""

import sys
import os
import argparse
import subprocess
import json
import logging
from pithy_os import PithyOS

# Configuration du logging minimaliste pour le CLI
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("pithy-cli")

class PithyCLI:
    """Contrôleur principal pour le CLI pithy."""

    def __init__(self):
        self.os_instance = None

    def _get_os(self):
        """Initialise une instance de l'OS si nécessaire (lazy loading)."""
        if not self.os_instance:
            try:
                self.os_instance = PithyOS()
            except Exception as e:
                print(f"❌ Erreur lors de l'initialisation de PIThy OS: {e}")
                sys.exit(1)
        return self.os_instance

    def start(self):
        """Démarre la stack Docker."""
        print("🚀 Démarrage de la stack PIThy (Docker)...")
        try:
            subprocess.run(["docker-compose", "up", "-d"], check=True)
            print("✅ Stack démarrée avec succès.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors du démarrage: {e}")

    def stop(self):
        """Arrête la stack Docker."""
        print("🛑 Arrêt de la stack PIThy...")
        try:
            subprocess.run(["docker-compose", "down"], check=True)
            print("✅ Stack arrêtée.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'arrêt: {e}")

    def status(self):
        """Affiche l'état complet du système."""
        print("📊 État actuel du système :")
        pithy = self._get_os()
        print(pithy.get_system_status())

    def list_plugins(self):
        """Liste les plugins actifs."""
        print("🔌 Plugins chargés :")
        pithy = self._get_os()
        plugins = pithy.plugins.loaded_plugins
        if not plugins:
            print("  (aucun plugin chargé)")
        for name, meta in plugins.items():
            print(f"  - {name} (v{meta.get('version', '?.?.?')}) [{meta.get('type', 'unknown')}]")

    def load_plugin(self, name):
        """Charge un plugin dynamiquement."""
        print(f"🔌 Tentative de chargement du plugin: {name}...")
        pithy = self._get_os()
        # En production, cela re-scannerait le dossier
        pithy.plugins.load_all() 
        if name in pithy.plugins.loaded_plugins:
            print(f"✅ Plugin '{name}' chargé et prêt.")
        else:
            print(f"❌ Plugin '{name}' introuvable ou erreur de chargement.")

    def doctor(self):
        """Diagnostic complet du système."""
        print("🩺 PIThy Doctor — Diagnostic du système\n")
        
        # 1. Vérification Docker
        print("🐳 Docker:")
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, text=True)
            if res.returncode == 0:
                print("  ✅ Docker Engine est installé et actif.")
            else:
                print("  ❌ Docker Engine est inactif.")
        except FileNotFoundError:
            print("  ❌ Docker n'est pas installé.")

        # 2. Vérification Ollama
        print("\n🧠 Ollama:")
        from llm.ollama_client import OllamaClient
        from config import DEFAULT_MODEL
        ollama = OllamaClient(DEFAULT_MODEL)
        if ollama.is_available():
            print(f"  ✅ Ollama est joignable. Modèle par défaut: {DEFAULT_MODEL}")
        else:
            print("  ❌ Ollama est injoignable. Vérifiez le service.")

        # 3. Vérification Dépendances
        print("\n📦 Dépendances Python:")
        deps = ["requests", "chromadb", "numpy"]
        for d in deps:
            try:
                importlib.import_module(d)
                print(f"  ✅ {d} est installé.")
            except ImportError:
                print(f"  ❌ {d} est manquant.")
        
        print("\n🏁 Diagnostic terminé.")

def main():
    parser = argparse.ArgumentParser(prog="pithy", description="CLI de contrôle PIThy")
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    # Start / Stop / Status
    subparsers.add_parser("start", help="Démarre la stack Docker")
    subparsers.add_parser("stop", help="Arrête la stack Docker")
    subparsers.add_parser("status", help="Affiche l'état du système")
    subparsers.add_parser("doctor", help="Diagnostic système")

    # Plugins
    plugin_parser = subparsers.add_parser("plugins", help="Gestion des plugins")
    plugin_subparsers = plugin_parser.add_subparsers(dest="plugin_command", help="Sous-commandes plugins")
    plugin_subparsers.add_parser("list", help="Liste les plugins")
    load_p = plugin_subparsers.add_parser("load", help="Charge un plugin")
    load_p.add_argument("name", help="Nom du plugin")

    args = parser.parse_args()
    cli = PithyCLI()

    if args.command == "start":
        cli.start()
    elif args.command == "stop":
        cli.stop()
    elif args.command == "status":
        cli.status()
    elif args.command == "doctor":
        cli.doctor()
    elif args.command == "plugins":
        if args.plugin_command == "list":
            cli.list_plugins()
        elif args.plugin_command == "load":
            cli.load_plugin(args.name)
    else:
        parser.print_help()

if __name__ == "__main__":
    import importlib
    main()
