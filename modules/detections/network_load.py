import os
import time

import psutil

from modules import alerts, logger, runtime as runtime_mod, state


def check_network_and_load():
    while True:
        state.update_thread_status("Network/Load")
        runtime = runtime_mod.get_runtime()
        config_data = runtime.config
        thresholds = config_data["thresholds"]
        detections = config_data["detections"]
        try:
            if detections.get("connections", True):
                connections = psutil.net_connections()
                connection_count = len(connections)
                if connection_count > thresholds["connections"]:
                    alerts.send_discord_alert(
                        "Network Connections",
                        connection_count,
                        thresholds["connections"],
                        "CRITICAL",
                        "High number of connections detected",
                        runtime=runtime
                    )
                else:
                    alerts.send_discord_alert(
                        "Network Connections",
                        connection_count,
                        thresholds["connections"],
                        "NORMAL",
                        "Connection count is normal",
                        runtime=runtime
                    )

            if detections.get("load_average", True):
                load_avg = os.getloadavg()[0]
                if load_avg > thresholds["load_average"]:
                    alerts.send_discord_alert(
                        "Load Average",
                        load_avg,
                        thresholds["load_average"],
                        "CRITICAL",
                        "High system load detected",
                        runtime=runtime
                    )
                else:
                    alerts.send_discord_alert(
                        "Load Average",
                        load_avg,
                        thresholds["load_average"],
                        "NORMAL",
                        "Load average is normal",
                        runtime=runtime
                    )
        except Exception as exc:
            logger.log(f"Network/load monitor error: {exc}")
        time.sleep(config_data["check_interval_seconds"])
