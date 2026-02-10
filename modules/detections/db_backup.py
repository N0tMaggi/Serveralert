import datetime
import gzip
import json
import os
import subprocess
import time

import requests

from modules import alerts, logger, runtime as runtime_mod, state, system_info


def perform_db_backup(runtime=None):
    runtime = runtime if runtime is not None else runtime_mod.get_runtime()
    config_data = runtime.config
    webhook_url = config_data["webhooks"].get("db") or config_data["discord_webhook_url"]
    if not webhook_url:
        logger.log("No DB webhook configured.")
        return

    db_config = config_data["database"]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"db_backup_{timestamp}.sql"
    filepath = os.path.join("/tmp", filename)
    zip_filename = f"{filename}.gz"
    zip_filepath = f"{filepath}.gz"

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

        with open(filepath, "rb") as source_file, gzip.open(zip_filepath, "wb") as zipped_file:
            zipped_file.writelines(source_file)

        file_size_mb = os.path.getsize(zip_filepath) / (1024 * 1024)
        interval_minutes = db_config["backup_interval_minutes"]
        next_run = datetime.datetime.now() + datetime.timedelta(minutes=interval_minutes)
        next_run_ts = int(next_run.timestamp())

        system_data = system_info.collect_system_info(runtime)
        embed_payload = {
            "title": "Database Backup",
            "description": "Backup completed successfully.",
            "color": 3066993,
            "fields": [
                {
                    "name": "Backup Details",
                    "value": f"Filename: `{zip_filename}`\nSize: `{file_size_mb:.2f} MB`",
                    "inline": False
                },
                {
                    "name": "Next Backup",
                    "value": f"<t:{next_run_ts}:F> (<t:{next_run_ts}:R>)",
                    "inline": False
                },
                {
                    "name": "System",
                    "value": system_info.format_system_info(system_data),
                    "inline": False
                }
            ],
            "footer": {"text": "ServerAlert Database Module"},
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }

        with open(zip_filepath, "rb") as file_handle:
            files = {"file": (zip_filename, file_handle, "application/gzip")}
            payload = {"payload_json": json.dumps({"embeds": [embed_payload]})}
            response = runtime.session.post(webhook_url, data=payload, files=files, timeout=30)
            if response.status_code == 413:
                logger.log("DB backup upload too large after gzip. Sending metadata only.")
                payload = {"embeds": [embed_payload]}
                response = runtime.session.post(webhook_url, json=payload, timeout=30)
            if response.status_code >= 400:
                raise requests.RequestException(
                    f"Webhook returned {response.status_code}: {response.text[:200]}"
                )

    except subprocess.CalledProcessError as exc:
        logger.log(f"Database backup failed: {exc}")
        alerts.send_discord_alert("Database Backup", "Failed", "", "CRITICAL", "Database backup process failed", str(exc))
    except Exception as exc:
        logger.log(f"Error sending backup: {exc}")
        alerts.send_discord_alert("Database Backup", "Error", "", "CRITICAL", "Error sending database backup", str(exc))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)


def db_backup_loop():
    while True:
        state.update_thread_status("DB Backup")
        runtime = runtime_mod.get_runtime()
        perform_db_backup(runtime)
        config_data = runtime.config
        time.sleep(config_data["database"]["backup_interval_minutes"] * 60)
