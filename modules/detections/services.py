import subprocess
import time

from modules import alerts, logger, runtime as runtime_mod, state

running_services_snapshot = set()


def check_critical_services():
    while True:
        state.update_thread_status("Critical Services")
        runtime = runtime_mod.get_runtime()
        config_data = runtime.config
        detections = config_data["detections"]
        if not detections.get("service_status", True):
            time.sleep(config_data["check_interval_seconds"])
            continue

        try:
            for service in config_data["monitored_services"]:
                result = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True)
                status = result.stdout.strip()

                if status != "active":
                    try:
                        logs = subprocess.check_output(
                            ["journalctl", "-u", service, "-n", "5", "--no-pager"],
                            text=True
                        )
                    except Exception:
                        logs = "Could not fetch logs."

                    alerts.send_discord_alert(
                        f"Service: {service}",
                        status,
                        "active",
                        "CRITICAL",
                        f"Service {service} is down. Attempting restart...",
                        f"Recent Logs:\n{logs}",
                        runtime=runtime
                    )
                    subprocess.run(["systemctl", "restart", service])
                    time.sleep(5)
                    result_retry = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True)
                    if result_retry.stdout.strip() == "active":
                        alerts.send_discord_alert(
                            f"Service: {service}",
                            "active",
                            "active",
                            "NORMAL",
                            f"Service {service} recovered successfully",
                            runtime=runtime
                        )
                    else:
                        alerts.send_discord_alert(
                            f"Service: {service}",
                            "failed",
                            "active",
                            "CRITICAL",
                            f"Service {service} failed to restart",
                            runtime=runtime
                        )
                else:
                    alerts.send_discord_alert(
                        f"Service: {service}",
                        "active",
                        "active",
                        "NORMAL",
                        f"Service {service} is running",
                        runtime=runtime
                    )
        except Exception as exc:
            logger.log(f"Critical services monitor error: {exc}")
        time.sleep(config_data["check_interval_seconds"])


def monitor_service_changes():
    global running_services_snapshot

    try:
        output = subprocess.check_output(
            ["systemctl", "list-units", "--type=service", "--state=running", "--no-pager", "--plain"],
            text=True
        )
        running_services_snapshot = set(
            line.split()[0] for line in output.splitlines() if line and ".service" in line
        )
    except Exception:
        pass

    while True:
        state.update_thread_status("Service Changes")
        runtime = runtime_mod.get_runtime()
        config_data = runtime.config
        detections = config_data["detections"]
        if not detections.get("service_changes", True):
            time.sleep(60)
            continue

        try:
            output = subprocess.check_output(
                ["systemctl", "list-units", "--type=service", "--state=running", "--no-pager", "--plain"],
                text=True
            )
            current_services = set(
                line.split()[0] for line in output.splitlines() if line and ".service" in line
            )

            new_services = current_services - running_services_snapshot
            stopped_services = running_services_snapshot - current_services

            if new_services:
                for service in new_services:
                    alerts.send_discord_alert(
                        "New Service Started",
                        service,
                        "",
                        "WARNING",
                        f"A new service has started: {service}",
                        runtime=runtime
                    )

            if stopped_services:
                for service in stopped_services:
                    if service.replace(".service", "") not in config_data["monitored_services"]:
                        alerts.send_discord_alert(
                            "Service Stopped",
                            service,
                            "",
                            "WARNING",
                            f"A service has stopped: {service}",
                            runtime=runtime
                        )

            running_services_snapshot = current_services
        except Exception as exc:
            logger.log(f"Service change monitor error: {exc}")
        time.sleep(60)
