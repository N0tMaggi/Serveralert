import hashlib
import os
import time

from modules import alerts, config, state

HASH_SKIPPED = "HASH_SKIPPED"
file_snapshots = {}


def _get_config():
    if config.CONFIG is None:
        config.set_config(config.load_config())
    return config.CONFIG


def compute_file_hash(path, max_bytes, chunk_size):
    try:
        size = os.path.getsize(path)
        if size > max_bytes:
            return HASH_SKIPPED
        digest = hashlib.sha256()
        with open(path, "rb") as file_handle:
            while True:
                chunk = file_handle.read(chunk_size)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()
    except Exception:
        return None


def build_file_metadata(path, max_bytes, chunk_size, previous_metadata=None):
    try:
        stat_result = os.stat(path, follow_symlinks=False)
    except (FileNotFoundError, PermissionError):
        return None
    except Exception:
        return None

    is_dir = os.path.isdir(path)
    metadata = {
        "is_dir": is_dir,
        "mode": stat_result.st_mode,
        "mtime": stat_result.st_mtime,
        "size": 0 if is_dir else stat_result.st_size,
        "hash": None
    }

    if is_dir:
        return metadata

    if (
        previous_metadata
        and previous_metadata.get("mtime") == metadata["mtime"]
        and previous_metadata.get("size") == metadata["size"]
        and previous_metadata.get("mode") == metadata["mode"]
    ):
        metadata["hash"] = previous_metadata.get("hash")
    else:
        metadata["hash"] = compute_file_hash(path, max_bytes, chunk_size)

    return metadata


def metadata_changed(previous, current):
    if previous.get("is_dir") != current.get("is_dir"):
        return True
    if previous.get("mode") != current.get("mode"):
        return True
    if current.get("is_dir"):
        return False
    if previous.get("size") != current.get("size"):
        return True
    if previous.get("hash") == HASH_SKIPPED and current.get("hash") == HASH_SKIPPED:
        return False
    return previous.get("hash") != current.get("hash")


def check_files():
    global file_snapshots
    config_data = _get_config()
    file_config = config_data["file_monitor"]
    max_bytes = file_config["hash_max_file_size_mb"] * 1024 * 1024
    chunk_size = file_config["hash_chunk_size"]

    if not file_snapshots:
        for directory in config_data["monitored_directories"]:
            if os.path.exists(directory):
                try:
                    snapshot = {}
                    for entry in os.listdir(directory):
                        path = os.path.join(directory, entry)
                        metadata = build_file_metadata(path, max_bytes, chunk_size)
                        if metadata:
                            snapshot[entry] = metadata
                    file_snapshots[directory] = snapshot
                except Exception:
                    pass

    while True:
        state.update_thread_status("File Monitor")
        config_data = _get_config()
        detections = config_data["detections"]
        if not detections.get("file_changes", True):
            time.sleep(config_data["check_interval_seconds"])
            continue

        try:
            for directory in config_data["monitored_directories"]:
                if not os.path.exists(directory):
                    continue
                try:
                    previous_snapshot = file_snapshots.get(directory, {})
                    current_snapshot = {}
                    new_entries = []
                    modified_entries = []

                    try:
                        entries = os.listdir(directory)
                    except PermissionError:
                        continue

                    for entry in entries:
                        path = os.path.join(directory, entry)
                        metadata = build_file_metadata(
                            path,
                            max_bytes,
                            chunk_size,
                            previous_snapshot.get(entry)
                        )
                        if not metadata:
                            continue
                        current_snapshot[entry] = metadata
                        if entry not in previous_snapshot:
                            new_entries.append(entry)
                        elif metadata_changed(previous_snapshot[entry], metadata):
                            modified_entries.append(entry)

                    deleted_entries = [
                        entry for entry in previous_snapshot.keys() if entry not in current_snapshot
                    ]

                    if new_entries or modified_entries or deleted_entries:
                        change_messages = []
                        if new_entries:
                            change_messages.append(f"New: {', '.join(new_entries[:5])}")
                        if modified_entries:
                            change_messages.append(f"Changed: {', '.join(modified_entries[:5])}")
                        if deleted_entries:
                            change_messages.append(f"Deleted: {', '.join(deleted_entries[:5])}")
                        alerts.send_discord_alert(
                            "File System Monitor",
                            len(new_entries) + len(modified_entries) + len(deleted_entries),
                            0,
                            "CRITICAL",
                            f"File changes detected in {directory}",
                            "\n".join(change_messages)
                        )

                    file_snapshots[directory] = current_snapshot
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(config_data["check_interval_seconds"])
