import platform
import time

import psutil


def collect_system_info(runtime=None):
    try:
        if runtime is not None:
            hostname = runtime.hostname
            ip_address = runtime.ip_address
        else:
            import socket

            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        os_info = f"{platform.system()} {platform.release()}"
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_string = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
        return {
            "host": hostname,
            "ip": ip_address,
            "os": os_info,
            "uptime": uptime_string,
            "uptime_seconds": int(uptime_seconds)
        }
    except Exception:
        return {
            "host": "unknown",
            "ip": "unknown",
            "os": "unknown",
            "uptime": "unknown",
            "uptime_seconds": 0
        }


def format_system_info(info):
    if not isinstance(info, dict):
        return "System info unavailable"
    return (
        f"Host: {info.get('host', 'unknown')} ({info.get('ip', 'unknown')}) | "
        f"OS: {info.get('os', 'unknown')} | Uptime: {info.get('uptime', 'unknown')}"
    )


def get_system_info(runtime=None):
    return format_system_info(collect_system_info(runtime))


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
