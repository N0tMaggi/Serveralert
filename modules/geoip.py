import ipaddress
import threading
import time

import requests

from modules import runtime as runtime_mod

geoip_cache = {}
geoip_cache_lock = threading.Lock()


def is_private_ip(ip_str):
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_private
    except ValueError:
        return True


def lookup_geoip(ip_str, runtime=None):
    runtime = runtime if runtime is not None else runtime_mod.get_runtime()
    config_data = runtime.config
    log_config = config_data.get("log_monitor", {})
    if not log_config.get("geoip_lookup", False) or not ip_str or is_private_ip(ip_str):
        return ip_str

    now = time.time()
    ttl = log_config.get("geoip_cache_ttl", 3600)
    with geoip_cache_lock:
        cached = geoip_cache.get(ip_str)
        if cached and now - cached["timestamp"] < ttl:
            return cached["data"]

    location = "Unknown"
    request_timeout = config_data.get("request_timeout_seconds", 5)
    try:
        response = runtime.session.get(
            f"http://ip-api.com/json/{ip_str}?fields=status,country,regionName,city,query",
            timeout=request_timeout
        )
        data = response.json()
        if data.get("status") == "success":
            city = data.get("city") or data.get("regionName")
            country = data.get("country", "")
            location_parts = [part for part in [city, country] if part]
            location = ", ".join(location_parts) if location_parts else "Unknown"
    except Exception:
        location = "Lookup failed"

    with geoip_cache_lock:
        geoip_cache[ip_str] = {"timestamp": now, "data": location}

    return f"{ip_str} ({location})"
