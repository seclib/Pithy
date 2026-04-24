#!/usr/bin/env python3
"""
PIThy CLI — Générateur et gestionnaire du mini OS IA local.

Commandes:
    pithy init              → initialise un projet pithy complet
    pithy run               → lance l'assistant IA
    pithy doctor            → vérifie l'état du système
    pithy reset             → reset mémoire + base vectorielle
    pithy docker up         → lance docker-compose
    pithy docker down       → arrête docker-compose
    pithy docker build      → reconstruit les images
    pithy add plugin <name> → installe un plugin
    pithy plugins           → liste les plugins
    pithy models            → liste les modèles Ollama
"""

import os
import sys
import json
import shutil
import subprocess

# =========================
# Couleurs terminal
# =========================

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    DIM = "\033[2m"


def ok(msg):
    print(f"  {C.GREEN}✅{C.RESET} {msg}")

def err(msg):
    print(f"  {C.RED}❌{C.RESET} {msg}")

def warn(msg):
    print(f"  {C.YELLOW}⚠️{C.RESET}  {msg}")

def info(msg):
    print(f"  {C.CYAN}ℹ️{C.RESET}  {msg}")

def header(msg):
    print(f"\n{C.BOLD}{C.CYAN}{msg}{C.RESET}")


# =========================
# INIT — Initialisation projet
# =========================

def cmd_init(args):
    """Initialise un projet pithy complet."""
    target = args[0] if args else "."
    target = os.path.abspath(target)

    header(f"🚀 Initialisation de PIThy dans {target}")

    # Créer les répertoires
    dirs = [
        "core", "llm", "memory", "tools", "plugins",
        "data/db", "data/logs",
    ]
    for d in dirs:
        path = os.path.join(target, d)
        os.makedirs(path, exist_ok=True)
        ok(f"Répertoire: {d}/")

    # Créer les __init__.py
    for module in ["core", "llm", "memory", "tools", "plugins"]:
        init_file = os.path.join(target, module, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f'"""PIThy - {module.capitalize()} module"""\n')
            ok(f"{module}/__init__.py")

    # Créer .env si absent
    env_file = os.path.join(target, ".env")
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write(
                "OLLAMA_URL=http://localhost:11434\n"
                "CHROMA_URL=http://localhost:8000\n"
                "DEFAULT_MODEL=dolphin-mistral:7b\n"
                "CODE_MODEL=qwen2.5-coder:7b\n"
                "EMBED_MODEL=nomic-embed-text\n"
                "SAFE_MODE=true\n"
            )
        ok(".env")

    # Créer .gitignore si absent
    gitignore = os.path.join(target, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w") as f:
            f.write(
                "__pycache__/\n*.pyc\n.env\ndata/db/\ndata/logs/\n"
                "*.egg-info/\ndist/\nbuild/\n"
            )
        ok(".gitignore")

    print(f"\n{C.GREEN}{C.BOLD}✅ Projet PIThy initialisé !{C.RESET}")
    print(f"\n   Lancez avec : {C.CYAN}pithy run{C.RESET}")
    print(f"   Ou Docker :  {C.CYAN}pithy docker up{C.RESET}")


# =========================
# RUN — Lancer l'assistant
# =========================

def cmd_run(args):
    """Lance l'assistant IA."""
    header("🧠 Lancement de PIThy...")
    # Import et lance main
    try:
        from main import main
        main()
    except ImportError:
        # Fallback: exécuter comme sous-processus
        subprocess.run([sys.executable, "main.py"])


# =========================
# DOCTOR — Diagnostic système
# =========================

def cmd_doctor(args):
    """Vérifie l'état du système."""
    header("🩺 Diagnostic PIThy")

    # Python
    ok(f"Python {sys.version.split()[0]}")

    # Vérifier les modules
    modules = ["requests", "chromadb", "numpy"]
    for mod in modules:
        try:
            __import__(mod)
            ok(f"Module: {mod}")
        except ImportError:
            err(f"Module manquant: {mod} → pip install {mod}")

    # Vérifier Ollama
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            ok(f"Ollama: {len(models)} modèles disponibles")

            # Vérifier les modèles requis
            from config import DEFAULT_MODEL, CODE_MODEL, EMBED_MODEL
            for name, model in [("Chat", DEFAULT_MODEL), ("Code", CODE_MODEL), ("Embed", EMBED_MODEL)]:
                found = any(model in m for m in models)
                if found:
                    ok(f"Modèle {name}: {model}")
                else:
                    warn(f"Modèle {name} manquant: {model} → ollama pull {model}")
        else:
            err("Ollama: non joignable")
    except Exception:
        err("Ollama: non joignable (http://localhost:11434)")

    # Vérifier ChromaDB
    try:
        import requests
        from config import CHROMA_URL
        r = requests.get(f"{CHROMA_URL}/api/v1/heartbeat", timeout=5)
        if r.status_code == 200:
            ok(f"ChromaDB: connecté ({CHROMA_URL})")
        else:
            warn(f"ChromaDB: HTTP {r.status_code}")
    except Exception:
        warn("ChromaDB: non joignable (lancez 'pithy docker up')")

    # Vérifier Docker
    try:
        result = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            ok(f"Docker: {result.stdout.strip()}")
        else:
            warn("Docker: installé mais erreur")
    except FileNotFoundError:
        warn("Docker: non installé")

    # Vérifier docker-compose
    try:
        result = subprocess.run(
            ["docker", "compose", "version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            ok(f"Docker Compose: {result.stdout.strip()}")
        else:
            warn("Docker Compose: non disponible")
    except FileNotFoundError:
        warn("Docker Compose: non installé")

    # Vérifier les fichiers du projet
    print()
    header("📁 Structure du projet")
    required_files = [
        "config.py", "main.py", "cli.py",
        "docker-compose.yml", "Dockerfile", "requirements.txt",
        "core/agent.py", "core/brain.py", "core/router.py", "core/orchestrator.py",
        "llm/ollama_client.py",
        "memory/embeddings.py", "memory/vector_store.py",
        "tools/shell.py", "tools/filesystem.py",
        "plugins/loader.py",
    ]
    for f in required_files:
        if os.path.exists(f):
            ok(f)
        else:
            err(f"Manquant: {f}")

    # Plugins
    print()
    header("🔌 Plugins")
    plugins_dir = "./plugins"
    if os.path.isdir(plugins_dir):
        count = 0
        for entry in sorted(os.listdir(plugins_dir)):
            ppath = os.path.join(plugins_dir, entry)
            meta = os.path.join(ppath, "plugin.json")
            if os.path.isdir(ppath) and os.path.isfile(meta):
                try:
                    with open(meta) as f:
                        data = json.load(f)
                    status = "✅" if data.get("enabled", True) else "❌"
                    print(f"  {status} {data['name']} v{data.get('version', '?')} [{data.get('type', '?')}]")
                    count += 1
                except Exception:
                    warn(f"Plugin invalide: {entry}")
        if count == 0:
            info("Aucun plugin installé")
    else:
        info("Répertoire plugins/ non trouvé")

    print()


# =========================
# RESET — Reset mémoire
# =========================

def cmd_reset(args):
    """Reset mémoire + base vectorielle."""
    header("🗑️  Reset PIThy")

    confirm = input("⚠️  Supprimer toute la mémoire et les logs ? (y/n): ")
    if confirm.strip().lower() != "y":
        print("Annulé.")
        return

    # Supprimer data/db
    db_dir = "./data/db"
    if os.path.isdir(db_dir):
        shutil.rmtree(db_dir)
        os.makedirs(db_dir, exist_ok=True)
        ok("Base vectorielle supprimée")
    else:
        info("Pas de base vectorielle")

    # Supprimer data/logs
    log_dir = "./data/logs"
    if os.path.isdir(log_dir):
        for f in os.listdir(log_dir):
            os.remove(os.path.join(log_dir, f))
        ok("Logs supprimés")
    else:
        info("Pas de logs")

    print(f"\n{C.GREEN}✅ Reset terminé.{C.RESET}")


# =========================
# DOCKER — Gestion Docker
# =========================

def cmd_docker(args):
    """Gestion Docker Compose."""
    if not args:
        print("Usage: pithy docker [up|down|build|logs]")
        return

    action = args[0]
    compose_cmd = ["docker", "compose"]

    if action == "up":
        header("🐳 Démarrage Docker...")
        subprocess.run(compose_cmd + ["up", "--build", "-d"])
        print(f"\n{C.GREEN}✅ Services démarrés.{C.RESET}")
        print(f"   Attachez-vous avec: {C.CYAN}docker attach pithy_core{C.RESET}")

    elif action == "down":
        header("🐳 Arrêt Docker...")
        subprocess.run(compose_cmd + ["down"])

    elif action == "build":
        header("🐳 Build Docker...")
        subprocess.run(compose_cmd + ["build"])

    elif action == "logs":
        service = args[1] if len(args) > 1 else ""
        cmd = compose_cmd + ["logs", "-f"]
        if service:
            cmd.append(service)
        subprocess.run(cmd)

    else:
        print(f"Action inconnue: {action}")
        print("Actions disponibles: up, down, build, logs")


# =========================
# ADD PLUGIN — Créer un plugin
# =========================

def cmd_add_plugin(args):
    """Crée un nouveau plugin."""
    if not args:
        print("Usage: pithy add plugin <name>")
        return

    name = args[0].lower().replace(" ", "_")
    plugin_dir = os.path.join("./plugins", name)

    if os.path.exists(plugin_dir):
        err(f"Le plugin '{name}' existe déjà")
        return

    header(f"🔌 Création du plugin: {name}")

    os.makedirs(plugin_dir, exist_ok=True)

    # plugin.json
    meta = {
        "name": name,
        "version": "1.0.0",
        "type": "tool",
        "description": f"Plugin {name}",
        "enabled": True,
    }
    with open(os.path.join(plugin_dir, "plugin.json"), "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    ok("plugin.json")

    # main.py
    main_code = f'''"""
Plugin: {name}
Description: TODO
"""


class Plugin:
    """Plugin {name}."""

    def get_tools(self) -> dict:
        """Retourne les outils disponibles."""
        return {{
            "hello": self.hello,
        }}

    def execute(self, command: str = "hello") -> str:
        """Point d\'entrée principal."""
        tools = self.get_tools()
        if command in tools:
            return tools[command]()
        return f"Commande inconnue: {{command}}"

    def hello(self) -> str:
        """Exemple de commande."""
        return "Hello from {name} plugin!"
'''
    with open(os.path.join(plugin_dir, "main.py"), "w") as f:
        f.write(main_code)
    ok("main.py")

    print(f"\n{C.GREEN}✅ Plugin '{name}' créé dans plugins/{name}/{C.RESET}")
    print(f"   Éditez {C.CYAN}plugins/{name}/main.py{C.RESET} pour ajouter vos commandes.")


# =========================
# PLUGINS — Lister les plugins
# =========================

def cmd_plugins(args):
    """Liste les plugins installés."""
    header("🔌 Plugins installés")
    plugins_dir = "./plugins"

    if not os.path.isdir(plugins_dir):
        info("Aucun répertoire plugins/")
        return

    count = 0
    for entry in sorted(os.listdir(plugins_dir)):
        ppath = os.path.join(plugins_dir, entry)
        meta = os.path.join(ppath, "plugin.json")
        if os.path.isdir(ppath) and os.path.isfile(meta):
            try:
                with open(meta) as f:
                    data = json.load(f)
                status = C.GREEN + "ON " + C.RESET if data.get("enabled") else C.RED + "OFF" + C.RESET
                print(f"  {status} {data['name']:<20} v{data.get('version', '?'):<8} [{data.get('type', '?'):<12}] {data.get('description', '')}")
                count += 1
            except Exception:
                warn(f"Plugin invalide: {entry}")

    if count == 0:
        info("Aucun plugin installé. Créez-en un avec: pithy add plugin <name>")
    print()


# =========================
# MODELS — Lister les modèles Ollama
# =========================

def cmd_models(args):
    """Liste les modèles Ollama disponibles."""
    header("🤖 Modèles Ollama")
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        r.raise_for_status()
        models = r.json().get("models", [])
        if models:
            for m in models:
                size = m.get("size", 0)
                size_gb = f"{size / 1e9:.1f}GB" if size else "?"
                print(f"  🤖 {m['name']:<30} {size_gb}")
        else:
            info("Aucun modèle installé")
    except Exception as e:
        err(f"Impossible de contacter Ollama: {e}")
    print()


# =========================
# HELP
# =========================

def cmd_help(args=None):
    """Affiche l'aide."""
    print(f"""
{C.BOLD}{C.CYAN}🧠 PIThy CLI — Mini OS IA Local{C.RESET}

{C.BOLD}Commandes:{C.RESET}
  {C.CYAN}pithy init [path]{C.RESET}           Initialise un projet pithy
  {C.CYAN}pithy run{C.RESET}                   Lance l'assistant IA
  {C.CYAN}pithy doctor{C.RESET}                Diagnostic système complet
  {C.CYAN}pithy reset{C.RESET}                 Reset mémoire + logs
  {C.CYAN}pithy docker up{C.RESET}             Lance Docker Compose
  {C.CYAN}pithy docker down{C.RESET}           Arrête Docker Compose
  {C.CYAN}pithy docker build{C.RESET}          Reconstruit les images
  {C.CYAN}pithy docker logs [svc]{C.RESET}     Affiche les logs
  {C.CYAN}pithy add plugin <name>{C.RESET}     Crée un nouveau plugin
  {C.CYAN}pithy plugins{C.RESET}               Liste les plugins
  {C.CYAN}pithy models{C.RESET}                Liste les modèles Ollama
  {C.CYAN}pithy help{C.RESET}                  Affiche cette aide
""")


# =========================
# MAIN
# =========================

COMMANDS = {
    "init": cmd_init,
    "run": cmd_run,
    "doctor": cmd_doctor,
    "reset": cmd_reset,
    "docker": cmd_docker,
    "plugins": cmd_plugins,
    "models": cmd_models,
    "help": cmd_help,
}


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h"):
        cmd_help()
        return

    cmd = args[0]
    remaining = args[1:]

    # Commande spéciale: "add plugin"
    if cmd == "add" and remaining and remaining[0] == "plugin":
        cmd_add_plugin(remaining[1:])
        return

    if cmd in COMMANDS:
        COMMANDS[cmd](remaining)
    else:
        err(f"Commande inconnue: {cmd}")
        cmd_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
