import time

import psutil

from modules import alerts, logger, runtime as runtime_mod, state, system_info


def check_resources():
    while True:
        state.update_thread_status("Resources")
        runtime = runtime_mod.get_runtime()
        config_data = runtime.config
        thresholds = config_data["thresholds"]
        detections = config_data["detections"]
        try:
            if detections.get("cpu", True):
                cpu_usage = psutil.cpu_percent(interval=1)
                if cpu_usage > thresholds["cpu"]:
                    alerts.send_discord_alert(
                        "CPU Usage",
                        f"{cpu_usage}%",
                        f"{thresholds['cpu']}%",
                        "CRITICAL",
                        "CPU usage is above threshold",
                        top_processes=system_info.get_top_processes("cpu"),
                        runtime=runtime
                    )
                else:
                    alerts.send_discord_alert(
                        "CPU Usage",
                        f"{cpu_usage}%",
                        f"{thresholds['cpu']}%",
                        "NORMAL",
                        "CPU usage is back to normal",
                        runtime=runtime
                    )

            if detections.get("memory", True):
                memory = psutil.virtual_memory()
                if memory.percent > thresholds["memory"]:
                    alerts.send_discord_alert(
                        "Memory Usage",
                        f"{memory.percent}%",
                        f"{thresholds['memory']}%",
                        "CRITICAL",
                        "Memory usage is above threshold",
                        top_processes=system_info.get_top_processes("memory"),
                        runtime=runtime
                    )
                else:
                    alerts.send_discord_alert(
                        "Memory Usage",
                        f"{memory.percent}%",
                        f"{thresholds['memory']}%",
                        "NORMAL",
                        "Memory usage is back to normal",
                        runtime=runtime
                    )

            if detections.get("disk", True):
                disk = psutil.disk_usage("/")
                if disk.percent > thresholds["disk"]:
                    alerts.send_discord_alert(
                        "Disk Usage",
                        f"{disk.percent}%",
                        f"{thresholds['disk']}%",
                        "CRITICAL",
                        "Disk usage is above threshold",
                        runtime=runtime
                    )
                else:
                    alerts.send_discord_alert(
                        "Disk Usage",
                        f"{disk.percent}%",
                        f"{thresholds['disk']}%",
                        "NORMAL",
                        "Disk usage is back to normal",
                        runtime=runtime
                    )

            if detections.get("process_count", True):
                process_count = len(psutil.pids())
                if process_count > thresholds["processes"]:
                    alerts.send_discord_alert(
                        "Process Count",
                        process_count,
                        thresholds["processes"],
                        "CRITICAL",
                        "Too many running processes detected",
                        runtime=runtime
                    )
                else:
                    alerts.send_discord_alert(
                        "Process Count",
                        process_count,
                        thresholds["processes"],
                        "NORMAL",
                        "Process count is within limits",
                        runtime=runtime
                    )

        except Exception as exc:
            logger.log(f"Resource monitor error: {exc}")
        time.sleep(config_data["check_interval_seconds"])
