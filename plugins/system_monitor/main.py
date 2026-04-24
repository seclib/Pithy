"""
Plugin: System Monitor
Fournit des informations système (CPU, RAM, disque, uptime).
"""

import subprocess


class Plugin:
    """Plugin de monitoring système."""

    def get_tools(self) -> dict:
        """Retourne les outils disponibles."""
        return {
            "sysinfo": self.system_info,
            "diskinfo": self.disk_info,
            "processes": self.top_processes,
        }

    def execute(self, command: str = "sysinfo") -> str:
        """Point d'entrée principal."""
        tools = self.get_tools()
        if command in tools:
            return tools[command]()
        return f"Commande inconnue: {command}. Disponibles: {', '.join(tools.keys())}"

    def system_info(self) -> str:
        """Informations système basiques."""
        info = []
        try:
            # Uptime
            uptime = subprocess.getoutput("uptime -p 2>/dev/null || uptime")
            info.append(f"⏱️  Uptime: {uptime.strip()}")

            # CPU
            cpu = subprocess.getoutput(
                "grep -c ^processor /proc/cpuinfo 2>/dev/null || echo 'N/A'"
            )
            info.append(f"🔧 CPU cores: {cpu.strip()}")

            # RAM
            mem = subprocess.getoutput(
                "free -h 2>/dev/null | grep Mem | awk '{print $2 \" total, \" $3 \" used, \" $4 \" free\"}'"
            )
            if mem.strip():
                info.append(f"💾 RAM: {mem.strip()}")

            # Hostname
            hostname = subprocess.getoutput("hostname 2>/dev/null")
            info.append(f"🏷️  Host: {hostname.strip()}")

        except Exception as e:
            info.append(f"[Erreur] {e}")

        return "\n".join(info)

    def disk_info(self) -> str:
        """Informations disque."""
        try:
            return subprocess.getoutput("df -h / 2>/dev/null")
        except Exception as e:
            return f"[Erreur] {e}"

    def top_processes(self) -> str:
        """Top 10 processus par CPU."""
        try:
            return subprocess.getoutput(
                "ps aux --sort=-%cpu 2>/dev/null | head -11"
            )
        except Exception as e:
            return f"[Erreur] {e}"
