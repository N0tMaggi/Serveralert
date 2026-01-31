import copy
import json
import os

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def load_env_file(path):
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as exc:
        print(f"Failed to read .env file: {exc}")


def env_value(key, default, cast=None):
    value = os.environ.get(key)
    if value is None:
        return default
    if cast is None:
        return value
    try:
        return cast(value)
    except (TypeError, ValueError):
        return default


def env_bool(key, default):
    value = os.environ.get(key)
    if value is None:
        return default
    value_lower = value.lower()
    if value_lower in {"1", "true", "yes", "on"}:
        return True
    if value_lower in {"0", "false", "no", "off"}:
        return False
    return default


def env_list(key, default):
    value = os.environ.get(key)
    if value is None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def env_float(key, default):
    return env_value(key, default, cast=float)


def env_int(key, default):
    return env_value(key, default, cast=int)


def build_default_config():
    default_webhook_fallback = env_value(
        "WEBHOOK_DEFAULT",
        "https://discord.com/api/webhooks/1431187987282133113/3MLfgswtruHYCTgDO3Q2E3t84wKJtOVz6WW2dG2SmhuiNre3dRjKbiNy_VwSAXpWFS6t"
    )

    return {
        "discord_webhook_url": default_webhook_fallback,
        "thresholds": {
            "cpu": env_float("CPU_THRESHOLD", 50),
            "memory": env_float("MEMORY_THRESHOLD", 50),
            "disk": env_float("DISK_THRESHOLD", 80),
            "load_average": env_float("LOAD_AVG_THRESHOLD", 5.0),
            "connections": env_int("CONNECTION_THRESHOLD", 1000),
            "processes": env_int("PROCESS_THRESHOLD", 500)
        },
        "check_interval_seconds": env_int("CHECK_INTERVAL_SECONDS", 300),
        "monitored_services": env_list(
            "MONITORED_SERVICES",
            [
                "apache2",
                "mariadb",
                "ssh",
                "maggi.dev.web.service",
                "codeserv.cloud.web.service",
                "isafemboy.gay.web.service"
            ]
        ),
        "monitored_directories": env_list(
            "MONITORED_DIRECTORIES",
            [
                "/etc",
                "/usr/bin",
                "/usr/sbin",
                "/bin",
                "/sbin",
                "/var/www"
            ]
        ),
        "alert_min_interval_seconds": env_int("ALERT_MIN_INTERVAL", 120),
        "request_timeout_seconds": env_int("REQUEST_TIMEOUT_SECONDS", 5),
        "request_max_retries": env_int("REQUEST_MAX_RETRIES", 3),
        "alert_ping_everyone": env_bool("ALERT_PING_EVERYONE", True),
        "file_monitor": {
            "hash_max_file_size_mb": env_int("FILE_HASH_MAX_MB", 5),
            "hash_chunk_size": env_int("FILE_HASH_CHUNK_SIZE", 65536)
        },
        "health_server": {
            "enabled": env_bool("HEALTH_SERVER_ENABLED", True),
            "host": env_value("HEALTH_SERVER_HOST", "127.0.0.1"),
            "port": env_int("HEALTH_SERVER_PORT", 8765)
        },
        "log_monitor": {
            "geoip_lookup": env_bool("GEOIP_LOOKUP_ENABLED", True),
            "geoip_cache_ttl": env_int("GEOIP_CACHE_TTL", 3600)
        },
        "database": {
            "host": env_value("DB_HOST", "127.0.0.1"),
            "port": env_int("DB_PORT", 3306),
            "user": env_value("DB_USER", "root"),
            "password": env_value("DB_PASS", ""),
            "backup_interval_minutes": env_int("DB_BACKUP_INTERVAL_MINUTES", 30)
        },
        "webhooks": {
            "default": default_webhook_fallback,
            "db": env_value("WEBHOOK_DB", ""),
            "resource": env_value("WEBHOOK_RESOURCE", ""),
            "service_status": env_value("WEBHOOK_SERVICE_STATUS", ""),
            "service_change": env_value("WEBHOOK_SERVICE_CHANGE", ""),
            "file_monitor": env_value("WEBHOOK_FILE_MONITOR", ""),
            "ssh_success": env_value("WEBHOOK_SSH_SUCCESS", ""),
            "ssh_failed": env_value("WEBHOOK_SSH_FAILED", ""),
            "sudo": env_value("WEBHOOK_SUDO", ""),
            "privilege": env_value("WEBHOOK_PRIVILEGE", ""),
            "password": env_value("WEBHOOK_PASSWORD", ""),
            "kernel": env_value("WEBHOOK_KERNEL", ""),
            "firewall": env_value("WEBHOOK_FIREWALL", "")
        },
        "embed": {
            "title_prefix": env_value("EMBED_TITLE_PREFIX", "ServerAlert"),
            "footer_text": env_value("EMBED_FOOTER_TEXT", "ServerAlert"),
            "separator": env_value("EMBED_SEPARATOR", "------------------------------"),
            "thumbnail_url": env_value("EMBED_THUMB_URL", ""),
            "image_url": env_value("EMBED_IMAGE_URL", ""),
            "image_warning_url": env_value("EMBED_IMAGE_WARNING_URL", ""),
            "show_top_processes": env_bool("EMBED_SHOW_TOP_PROCESSES", True)
        },
        "detections": {
            "resources": env_bool("DETECT_RESOURCES", True),
            "network_load": env_bool("DETECT_NETWORK_LOAD", True),
            "critical_services": env_bool("DETECT_CRITICAL_SERVICES", True),
            "service_changes": env_bool("DETECT_SERVICE_CHANGES", True),
            "log_monitor": env_bool("DETECT_LOG_MONITOR", True),
            "file_monitor": env_bool("DETECT_FILE_MONITOR", True),
            "db_backup": env_bool("DETECT_DB_BACKUP", True),
            "health_server": env_bool("DETECT_HEALTH_SERVER", True),
            "cpu": env_bool("DETECT_CPU", True),
            "memory": env_bool("DETECT_MEMORY", True),
            "disk": env_bool("DETECT_DISK", True),
            "process_count": env_bool("DETECT_PROCESS_COUNT", True),
            "connections": env_bool("DETECT_CONNECTIONS", True),
            "load_average": env_bool("DETECT_LOAD_AVG", True),
            "service_status": env_bool("DETECT_SERVICE_STATUS", True),
            "ssh_login": env_bool("DETECT_SSH_LOGIN", True),
            "ssh_failed": env_bool("DETECT_SSH_FAILED", True),
            "sudo": env_bool("DETECT_SUDO", True),
            "privilege": env_bool("DETECT_PRIVILEGE", True),
            "password_change": env_bool("DETECT_PASSWORD_CHANGE", True),
            "kernel": env_bool("DETECT_KERNEL", True),
            "firewall": env_bool("DETECT_FIREWALL", True),
            "file_changes": env_bool("DETECT_FILE_CHANGES", True)
        }
    }

CONFIG_PATH = os.environ.get(
    "SERVERALERT_CONFIG",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "serveralert_config.json")
)

CONFIG = None


def _deep_update(original, updates):
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(original.get(key), dict):
            original[key] = _deep_update(original.get(key, {}), value)
        else:
            original[key] = value
    return original


def load_config():
    config = copy.deepcopy(build_default_config())
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
                file_values = json.load(config_file)
            config = _deep_update(config, file_values)
        except Exception as exc:
            print(f"Failed to load config file ({CONFIG_PATH}), using defaults. Error: {exc}")
    return config


def set_config(config):
    global CONFIG
    CONFIG = config
