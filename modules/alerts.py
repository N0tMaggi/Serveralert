import time

import requests

from modules import config, embed, system_info

alert_state = {}
alert_state_lock = None
last_alert_times = {}

ALWAYS_SEND_TYPES = {
    "SSH Login",
    "SSH Failed Login",
    "New Service Started",
    "File System Monitor",
    "Sudo Usage",
    "Service Stopped",
    "Privilege Escalation",
    "Password Change",
    "Kernel Alert",
    "Firewall Event"
}

RESOURCE_ALERT_TYPES = {
    "CPU Usage",
    "Memory Usage",
    "Disk Usage",
    "Process Count",
    "Network Connections",
    "Load Average"
}

SERVICE_CHANGE_ALERT_TYPES = {"New Service Started", "Service Stopped"}


def _get_config():
    if config.CONFIG is None:
        config.set_config(config.load_config())
    return config.CONFIG


def _get_alert_lock():
    global alert_state_lock
    if alert_state_lock is None:
        import threading

        alert_state_lock = threading.Lock()
    return alert_state_lock


def get_detection_category(detection_type):
    if detection_type.startswith("Service:"):
        return "service_status"
    if detection_type in RESOURCE_ALERT_TYPES:
        return "resource"
    if detection_type in SERVICE_CHANGE_ALERT_TYPES:
        return "service_change"
    if "File System Monitor" in detection_type:
        return "file_monitor"
    if detection_type == "SSH Login":
        return "ssh_success"
    if detection_type == "SSH Failed Login":
        return "ssh_failed"
    if detection_type == "Sudo Usage":
        return "sudo"
    if detection_type == "Privilege Escalation":
        return "privilege"
    if detection_type == "Password Change":
        return "password"
    if detection_type == "Kernel Alert":
        return "kernel"
    if detection_type == "Firewall Event":
        return "firewall"
    return "default"


def get_webhook_url(detection_type):
    config_data = _get_config()
    webhooks = config_data["webhooks"]
    category = get_detection_category(detection_type)
    return webhooks.get(category) or webhooks.get("default") or config_data["discord_webhook_url"]


def send_discord_alert(detection_type, value, threshold, status, message, extra_info="", top_processes=None):
    config_data = _get_config()
    should_send = False

    if detection_type in ALWAYS_SEND_TYPES:
        should_send = True
    else:
        with _get_alert_lock():
            current_state = alert_state.get(detection_type, "NORMAL")

            if status == "CRITICAL":
                if current_state != "CRITICAL":
                    should_send = True
                    alert_state[detection_type] = "CRITICAL"

            elif status == "NORMAL":
                if current_state == "CRITICAL":
                    should_send = True
                    alert_state[detection_type] = "NORMAL"

    if not should_send:
        return

    alert_min_interval = config_data["alert_min_interval_seconds"]
    if detection_type not in ALWAYS_SEND_TYPES and alert_min_interval > 0:
        last_time = last_alert_times.get(detection_type, 0)
        if last_time and time.time() - last_time < alert_min_interval and alert_state.get(detection_type) == status:
            return
        last_alert_times[detection_type] = time.time()

    system_info_text = system_info.get_system_info()
    embed_config = config_data.get("embed", {})
    if not embed_config.get("show_top_processes", True):
        top_processes = None
    embed_payload = embed.build_embed(
        detection_type,
        status,
        message,
        system_info_text,
        value=value,
        threshold=threshold,
        extra_info=extra_info,
        top_processes=top_processes,
        embed_config=embed_config
    )

    if status == "CRITICAL" and config_data.get("alert_ping_everyone", True):
        data = {"content": "@everyone CRITICAL ALERT", "embeds": [embed_payload]}
    else:
        data = {"embeds": [embed_payload]}

    webhook_url = get_webhook_url(detection_type)
    if not webhook_url:
        print(f"No webhook configured for detection type {detection_type}")
        return

    request_timeout = config_data["request_timeout_seconds"]
    request_max_retries = config_data["request_max_retries"]

    for attempt in range(request_max_retries):
        try:
            requests.post(webhook_url, json=data, timeout=request_timeout)
            break
        except Exception as exc:
            if attempt == request_max_retries - 1:
                print(f"Error sending alert: {exc}")
            else:
                time.sleep(1)
