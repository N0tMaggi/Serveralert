import platform
import socket
import time

import psutil


def get_system_info():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        os_info = f"{platform.system()} {platform.release()}"
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_string = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
        return f"Host: {hostname} ({ip_address}) | OS: {os_info} | Uptime: {uptime_string}"
    except Exception:
        return "System info unavailable"


def get_top_processes(sort_by="cpu", limit=5):
    try:
        processes = []
        for proc in psutil.process_iter([
            "pid",
            "name",
            "username",
            "cpu_percent",
            "memory_percent"
        ]):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if sort_by == "cpu":
            processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
        elif sort_by == "memory":
            processes.sort(key=lambda x: x["memory_percent"], reverse=True)

        top_procs = processes[:limit]
        lines = []
        for proc in top_procs:
            lines.append(
                f"{proc['name']} (PID: {proc['pid']}, User: {proc['username']}): "
                f"{proc['cpu_percent']}% CPU, {proc['memory_percent']:.1f}% MEM"
            )
        return "\n".join(lines) if lines else "No active process data."
    except Exception:
        return "Could not fetch process list."
