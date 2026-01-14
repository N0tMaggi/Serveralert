import datetime
import json
import os
import subprocess
import time

import requests

from modules import alerts, config, state, system_info


def _get_config():
    if config.CONFIG is None:
        config.set_config(config.load_config())
    return config.CONFIG


def perform_db_backup():
    config_data = _get_config()
    webhook_url = config_data["webhooks"].get("db") or config_data["discord_webhook_url"]
    if not webhook_url:
        print("No DB webhook configured.")
        return

    db_config = config_data["database"]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"db_backup_{timestamp}.sql"
    filepath = os.path.join("/tmp", filename)

    try:
        cmd = [
            "mysqldump",
            f"--host={db_config['host']}",
            f"--port={db_config['port']}",
            f"--user={db_config['user']}",
            f"--password={db_config['password']}",
            "--all-databases",
            "--result-file=" + filepath
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        interval_minutes = db_config["backup_interval_minutes"]
        next_run = datetime.datetime.now() + datetime.timedelta(minutes=interval_minutes)
        next_run_ts = int(next_run.timestamp())

        embed_payload = {
            "title": "Database Backup",
            "description": "Backup completed successfully.",
            "color": 3066993,
            "fields": [
                {
                    "name": "Backup Details",
                    "value": f"Filename: `{filename}`\nSize: `{file_size_mb:.2f} MB`",
                    "inline": False
                },
                {
                    "name": "Next Backup",
                    "value": f"<t:{next_run_ts}:F> (<t:{next_run_ts}:R>)",
                    "inline": False
                },
                {
                    "name": "System",
                    "value": system_info.get_system_info(),
                    "inline": False
                }
            ],
            "footer": {"text": "ServerAlert Database Module"},
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }

        with open(filepath, "rb") as file_handle:
            files = {"file": (filename, file_handle, "application/sql")}
            payload = {"payload_json": json.dumps({"embeds": [embed_payload]})}
            requests.post(webhook_url, data=payload, files=files, timeout=30)

    except subprocess.CalledProcessError as exc:
        print(f"Database backup failed: {exc}")
        alerts.send_discord_alert("Database Backup", "Failed", "", "CRITICAL", "Database backup process failed", str(exc))
    except Exception as exc:
        print(f"Error sending backup: {exc}")
        alerts.send_discord_alert("Database Backup", "Error", "", "CRITICAL", "Error sending database backup", str(exc))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


def db_backup_loop():
    while True:
        state.update_thread_status("DB Backup")
        perform_db_backup()
        config_data = _get_config()
        time.sleep(config_data["database"]["backup_interval_minutes"] * 60)
