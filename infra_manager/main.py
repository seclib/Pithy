"""
PIThy Infra Manager — Standalone entry point
Lance le gestionnaire d'infrastructure en mode autonome.
"""

import sys
import time
import signal
import logging

# Setup logging avant les imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Point d'entrée standalone du gestionnaire d'infrastructure."""
    from infra_manager.core.manager import InfraManager

    print("""
╔══════════════════════════════════════════════════╗
║     🧠 PIThy Infra Manager                      ║
║     Mini Cloud OS IA Local                       ║
╚══════════════════════════════════════════════════╝
""")

    manager = InfraManager(auto_start=True)

    # Gestion du signal d'arrêt
    def shutdown(signum, frame):
        print("\n🛑 Arrêt du gestionnaire...")
        manager.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("🟢 Infra Manager actif. Ctrl+C pour arrêter.\n")

    # Boucle d'affichage du status
    try:
        while True:
            print(manager.status())
            print(f"\n{'─' * 50}")
            time.sleep(30)
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()
