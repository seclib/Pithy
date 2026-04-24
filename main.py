"""
PIThy - Assistant IA local intelligent
Point d'entrée principal — mode interactif.
"""

import sys
import logging
from config import OLLAMA_URL, CHROMA_URL, DEFAULT_MODEL, CODE_MODEL, SAFE_MODE
from pithy_os import PithyOS
from llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

BANNER = r"""
╔══════════════════════════════════════════════════════╗
║          🧠 PIThy — Autonomous AI OS                 ║
║       Ollama + RAG + Plugins + Infra Manager         ║
╠══════════════════════════════════════════════════════╣
║  Commandes:                                          ║
║    exit             → quitter                        ║
║    status           → état complet du système        ║
║    plugins          → lister les plugins             ║
║    remember:xxx     → mémoriser xxx                  ║
║    recall:xxx       → rechercher dans la mémoire     ║
║    shell:xxx        → exécuter une commande          ║
║    mode:pipeline    → activer le mode multi-modèle   ║
║    mode:single      → revenir au mode simple         ║
╚══════════════════════════════════════════════════════╝
"""

# ... (check_services stays the same) ...

def show_status(pithy_os):
    """Affiche l'état actuel du système unifié."""
    print(pithy_os.get_system_status())


def main():
    """Boucle principale de l'assistant."""
    print(BANNER)
    check_services()

    try:
        pithy_os = PithyOS()
        print("🟢 PIThy OS est prêt.\n")
    except Exception as e:
        logger.error("Impossible de démarrer PIThy OS: %s", e)
        print(f"🔴 Erreur au démarrage: {e}")
        sys.exit(1)

    strategy = "single"  # Mode par défaut

    while True:
        try:
            mode_indicator = f"[{pithy_os.infra.mode}]"
            query = input(f"{mode_indicator} >> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 À bientôt!")
            break

        if not query:
            continue

        # --- Commandes spéciales ---

        if query.lower() == "exit":
            pithy_os.shutdown()
            print("👋 À bientôt!")
            break

        if query.lower() == "status":
            show_status(pithy_os)
            continue

        if query.lower() == "plugins":
            print(pithy_os.agent.list_plugins())
            continue

        if query.lower().startswith("mode:"):
            new_mode = query[5:].strip().lower()
            if new_mode in ("single", "compare", "pipeline"):
                strategy = new_mode
                print(f"🔄 Mode changé: {strategy}")
            else:
                print("⚠️  Modes disponibles: single, compare, pipeline")
            continue

        if query.lower().startswith("remember:"):
            content = query[9:].strip()
            if content:
                print(pithy_os.agent.remember(content))
            else:
                print("⚠️  Usage: remember:contenu à mémoriser")
            continue

        if query.lower().startswith("recall:"):
            search = query[7:].strip()
            if search:
                print(pithy_os.agent.recall(search))
            else:
                print("⚠️  Usage: recall:terme de recherche")
            continue

        if query.lower().startswith("shell:"):
            cmd = query[6:].strip()
            if cmd:
                result = pithy_os.agent.shell.run(cmd)
                if result["status"] == "ok":
                    print(result["stdout"] or result["stderr"] or "(pas de sortie)")
                else:
                    print(f"❌ {result['status']}: {result['stderr']}")
            else:
                print("⚠️  Usage: shell:commande")
            continue

        if query.lower().startswith("plugin:"):
            parts = query[7:].split(":", 1)
            plugin_name = parts[0].strip()
            plugin_cmd = parts[1].strip() if len(parts) > 1 else None
            print(pithy_os.agent.run_plugin(plugin_name, plugin_cmd))
            continue

        # --- Requête normale → pithy_os ---
        response = pithy_os.run(query, strategy=strategy)
        print(f"\n🤖 {response}\n")


if __name__ == "__main__":
    main()
