import time

STATUS_IMAGES = {
    "CRITICAL": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Cross_red_circle.svg/480px-Cross_red_circle.svg.png",
    "WARNING": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Dialog-warning.svg/480px-Dialog-warning.svg.png",
    "NORMAL": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Check_green_circle.svg/480px-Check_green_circle.svg.png",
    "INFO": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Infobox_info_icon.svg/480px-Infobox_info_icon.svg.png",
    "UNKNOWN": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Infobox_info_icon.svg/480px-Infobox_info_icon.svg.png"
}

STATUS_META = {
    "CRITICAL": {"label": "Critical", "color": 15158332},
    "WARNING": {"label": "Warning", "color": 15105570},
    "NORMAL": {"label": "Normal", "color": 3066993},
    "INFO": {"label": "Info", "color": 3447003},
    "UNKNOWN": {"label": "Unknown", "color": 9807270}
}


def build_embed(
    detection_type,
    status,
    message,
    system_info,
    value=None,
    threshold=None,
    extra_info=None,
    top_processes=None,
    embed_config=None
):
    embed_config = embed_config or {}
    title_prefix = embed_config.get("title_prefix", "ServerAlert")
    separator = embed_config.get("separator", "------------------------------")
    footer_text = embed_config.get("footer_text", "ServerAlert")
    status_meta = STATUS_META.get(status, STATUS_META["INFO"])

    # Determine image based on status
    image_url = STATUS_IMAGES.get(status, STATUS_IMAGES["INFO"])
    if status not in STATUS_IMAGES and status != "INFO":
        if "FAIL" in status or "DOWN" in status:
            image_url = STATUS_IMAGES["CRITICAL"]
        elif "OK" in status or "UP" in status or "RECOVERED" in status:
            image_url = STATUS_IMAGES["NORMAL"]

    if embed_config.get("thumbnail_url"):
        thumbnail_url = embed_config["thumbnail_url"]
    else:
        thumbnail_url = image_url

    image_override = ""
    if status == "CRITICAL":
        image_override = embed_config.get("image_critical_url", "")
    elif status == "WARNING":
        image_override = embed_config.get("image_warning_url", "")
    else:
        image_override = embed_config.get("image_url", "")

    title = f"{title_prefix} - {detection_type}"
    description = f"Status: **{status_meta['label']}**\n{separator}"

    embed = {
        "title": title,
        "description": description,
        "color": status_meta["color"],
        "fields": [
            {"name": "Summary", "value": message or "No message provided.", "inline": False}
        ],
        "thumbnail": {"url": thumbnail_url},
        "footer": {"text": footer_text},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    }

    if isinstance(system_info, dict):
        embed["fields"].append({"name": "Host", "value": system_info.get("host", "unknown"), "inline": True})
        embed["fields"].append({"name": "IP", "value": system_info.get("ip", "unknown"), "inline": True})
        embed["fields"].append({"name": "OS", "value": system_info.get("os", "unknown"), "inline": True})
        embed["fields"].append({"name": "Uptime", "value": system_info.get("uptime", "unknown"), "inline": True})
    elif system_info:
        embed["fields"].append({"name": "System", "value": system_info, "inline": False})

    if value is not None and value != "":
        embed["fields"].append({"name": "Value", "value": str(value), "inline": True})
    if threshold is not None and threshold != "" and threshold != 0:
        embed["fields"].append({"name": "Threshold", "value": str(threshold), "inline": True})

    if extra_info:
        embed["fields"].append({
            "name": "Details",
            "value": f"```{str(extra_info)}```",
            "inline": False
        })

    if image_override:
        embed["image"] = {"url": image_override}

    if top_processes:
        embed["fields"].append({
            "name": "Top Processes",
            "value": f"```{top_processes}```",
            "inline": False
        })

    return embed
