import time

import psutil

from modules import alerts, config, state, system_info


def _get_config():
    if config.CONFIG is None:
        config.set_config(config.load_config())
    return config.CONFIG


def check_resources():
    while True:
        state.update_thread_status("Resources")
        config_data = _get_config()
        thresholds = config_data["thresholds"]
        detections = config_data["detections"]
        try:
            if detections.get("cpu", True):
                cpu_usage = psutil.cpu_percent(interval=1)
                if cpu_usage > thresholds["cpu"]:
                    alerts.send_discord_alert("CPU Usage", f"{cpu_usage}%", f"{thresholds['cpu']}%", "CRITICAL", "CPU usage is above threshold", top_processes=system_info.get_top_processes("cpu"))
                else:
                    alerts.send_discord_alert("CPU Usage", f"{cpu_usage}%", f"{thresholds['cpu']}%", "NORMAL", "CPU usage is back to normal")

            if detections.get("memory", True):
                memory = psutil.virtual_memory()
                if memory.percent > thresholds["memory"]:
                    alerts.send_discord_alert("Memory Usage", f"{memory.percent}%", f"{thresholds['memory']}%", "CRITICAL", "Memory usage is above threshold", top_processes=system_info.get_top_processes("memory"))
                else:
                    alerts.send_discord_alert("Memory Usage", f"{memory.percent}%", f"{thresholds['memory']}%", "NORMAL", "Memory usage is back to normal")

            if detections.get("disk", True):
                disk = psutil.disk_usage("/")
                if disk.percent > thresholds["disk"]:
                    alerts.send_discord_alert("Disk Usage", f"{disk.percent}%", f"{thresholds['disk']}%", "CRITICAL", "Disk usage is above threshold")
                else:
                    alerts.send_discord_alert("Disk Usage", f"{disk.percent}%", f"{thresholds['disk']}%", "NORMAL", "Disk usage is back to normal")

            if detections.get("process_count", True):
                process_count = len(psutil.pids())
                if process_count > thresholds["processes"]:
                    alerts.send_discord_alert("Process Count", process_count, thresholds["processes"], "CRITICAL", "Too many running processes detected")
                else:
                    alerts.send_discord_alert("Process Count", process_count, thresholds["processes"], "NORMAL", "Process count is within limits")

        except Exception:
            pass
        time.sleep(config_data["check_interval_seconds"])
