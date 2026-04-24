"""
PIThy Infra Manager — System Monitor
Surveille CPU, RAM, disque et charge système.
"""

import os
import time
import logging

logger = logging.getLogger(__name__)


def _read_file(path: str) -> str:
    """Lit un fichier système de manière sûre."""
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return ""


class SystemMonitor:
    """Collecte les métriques système via /proc (zero dependency)."""

    def __init__(self):
        self._prev_cpu = None
        self._prev_time = None

    def get_cpu_percent(self) -> float:
        """Retourne le % d'utilisation CPU global."""
        try:
            raw = _read_file("/proc/stat")
            if not raw:
                return 0.0

            line = raw.split("\n")[0]  # "cpu  user nice system idle ..."
            parts = line.split()[1:]
            values = [int(v) for v in parts]

            idle = values[3] + (values[4] if len(values) > 4 else 0)
            total = sum(values)

            if self._prev_cpu is not None:
                d_idle = idle - self._prev_cpu[0]
                d_total = total - self._prev_cpu[1]
                cpu_pct = (1.0 - d_idle / max(d_total, 1)) * 100.0
            else:
                cpu_pct = 0.0

            self._prev_cpu = (idle, total)
            return round(cpu_pct, 1)
        except Exception as e:
            logger.debug("CPU read error: %s", e)
            return 0.0

    def get_memory(self) -> dict:
        """Retourne les infos mémoire en MB."""
        info = {"total_mb": 0, "used_mb": 0, "free_mb": 0, "percent": 0.0}
        try:
            raw = _read_file("/proc/meminfo")
            if not raw:
                return info

            mem = {}
            for line in raw.split("\n"):
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    mem[key] = int(val)  # kB

            total = mem.get("MemTotal", 0) / 1024
            free = mem.get("MemAvailable", mem.get("MemFree", 0)) / 1024
            used = total - free

            info["total_mb"] = round(total)
            info["used_mb"] = round(used)
            info["free_mb"] = round(free)
            info["percent"] = round((used / max(total, 1)) * 100, 1)
        except Exception as e:
            logger.debug("Memory read error: %s", e)

        return info

    def get_disk(self, path: str = "/") -> dict:
        """Retourne les infos disque."""
        info = {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0.0}
        try:
            st = os.statvfs(path)
            total = (st.f_blocks * st.f_frsize) / (1024 ** 3)
            free = (st.f_bavail * st.f_frsize) / (1024 ** 3)
            used = total - free

            info["total_gb"] = round(total, 1)
            info["used_gb"] = round(used, 1)
            info["free_gb"] = round(free, 1)
            info["percent"] = round((used / max(total, 1)) * 100, 1)
        except Exception as e:
            logger.debug("Disk read error: %s", e)

        return info

    def get_load_average(self) -> tuple:
        """Retourne le load average (1, 5, 15 minutes)."""
        try:
            return os.getloadavg()
        except Exception:
            return (0.0, 0.0, 0.0)

    def get_uptime_seconds(self) -> float:
        """Retourne l'uptime en secondes."""
        try:
            raw = _read_file("/proc/uptime")
            return float(raw.split()[0]) if raw else 0.0
        except Exception:
            return 0.0

    def snapshot(self) -> dict:
        """Retourne un snapshot complet des métriques système."""
        return {
            "timestamp": time.time(),
            "cpu_percent": self.get_cpu_percent(),
            "memory": self.get_memory(),
            "disk": self.get_disk(),
            "load_avg": self.get_load_average(),
            "uptime_s": self.get_uptime_seconds(),
        }
