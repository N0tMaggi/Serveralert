import os
import time

import psutil

from modules import alerts, config, state


def _get_config():
    if config.CONFIG is None:
        config.set_config(config.load_config())
    return config.CONFIG


def check_network_and_load():
    while True:
        state.update_thread_status("Network/Load")
        config_data = _get_config()
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
                        "High number of connections detected"
                    )
                else:
                    alerts.send_discord_alert(
                        "Network Connections",
                        connection_count,
                        thresholds["connections"],
                        "NORMAL",
                        "Connection count is normal"
                    )

            if detections.get("load_average", True):
                load_avg = os.getloadavg()[0]
                if load_avg > thresholds["load_average"]:
                    alerts.send_discord_alert(
                        "Load Average",
                        load_avg,
                        thresholds["load_average"],
                        "CRITICAL",
                        "High system load detected"
                    )
                else:
                    alerts.send_discord_alert(
                        "Load Average",
                        load_avg,
                        thresholds["load_average"],
                        "NORMAL",
                        "Load average is normal"
                    )
        except Exception:
            pass
        time.sleep(config_data["check_interval_seconds"])
