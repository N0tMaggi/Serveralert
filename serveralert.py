import threading
import time

from modules import config, logger
from modules.detections import db_backup, file_monitor, log_monitor, network_load, resources, services
from modules import health_server


def start_monitoring():
    logger.log("Starting ServerAlert System...")
    config_data = config.CONFIG
    detections = config_data["detections"]
    threads = []

    if detections.get("resources", True):
        threads.append(threading.Thread(target=resources.check_resources, daemon=True, name="Resources"))
    if detections.get("network_load", True):
        threads.append(threading.Thread(target=network_load.check_network_and_load, daemon=True, name="NetworkLoad"))
    if detections.get("critical_services", True):
        threads.append(threading.Thread(target=services.check_critical_services, daemon=True, name="CriticalServices"))
    if detections.get("service_changes", True):
        threads.append(threading.Thread(target=services.monitor_service_changes, daemon=True, name="ServiceChanges"))
    if detections.get("log_monitor", True):
        threads.append(threading.Thread(target=log_monitor.monitor_logs, daemon=True, name="LogMonitor"))
    if detections.get("file_monitor", True):
        threads.append(threading.Thread(target=file_monitor.check_files, daemon=True, name="FileMonitor"))
    if detections.get("db_backup", True):
        threads.append(threading.Thread(target=db_backup.db_backup_loop, daemon=True, name="DBBackup"))

    if detections.get("health_server", True) and config_data["health_server"].get("enabled", False):
        threads.append(threading.Thread(target=health_server.start_health_server, daemon=True, name="HealthServer"))

    for thread in threads:
        thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.log("Stopping ServerAlert System...")


if __name__ == "__main__":
    config.load_env_file(config.ENV_PATH)
    config.set_config(config.load_config())
    start_monitoring()
