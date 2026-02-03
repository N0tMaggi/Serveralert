import time

STATUS_IMAGES = {
    "CRITICAL": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Cross_red_circle.svg/480px-Cross_red_circle.svg.png",
    "WARNING": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Dialog-warning.svg/480px-Dialog-warning.svg.png",
    "NORMAL": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Check_green_circle.svg/480px-Check_green_circle.svg.png",
    "INFO": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Infobox_info_icon.svg/480px-Infobox_info_icon.svg.png",
    "UNKNOWN": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Infobox_info_icon.svg/480px-Infobox_info_icon.svg.png"
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

    # Determine image based on status
    image_url = STATUS_IMAGES.get(status, STATUS_IMAGES["INFO"])
    if status not in STATUS_IMAGES and status != "INFO":
        # Fallback for other statuses if any
        if "FAIL" in status or "DOWN" in status:
            image_url = STATUS_IMAGES["CRITICAL"]
        elif "OK" in status or "UP" in status or "RECOVERED" in status:
             image_url = STATUS_IMAGES["NORMAL"]

    embed = {
        "title": f"{title_prefix} - {detection_type}",
        "description": f"Status: **{status}**\n{separator}",
        "color": 3066993,
        "fields": [
            {"name": "Message", "value": message or "No message", "inline": False},
        ],
        "thumbnail": {"url": image_url},
        "footer": {"text": footer_text},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    }

    # Enhance System Info display
    if system_info and "|" in system_info:
        parts = system_info.split("|")
        for part in parts:
            if ":" in part:
                key, val = part.split(":", 1)
                embed["fields"].append({"name": key.strip(), "value": val.strip(), "inline": True})
            else:
                embed["fields"].append({"name": "System Info", "value": part.strip(), "inline": True})
    else:
        embed["fields"].append({"name": "System", "value": system_info, "inline": False})

    if status == "CRITICAL":
        embed["color"] = 15158332
    elif status == "WARNING":
        embed["color"] = 15105570
    elif status == "NORMAL":
        embed["color"] = 3066993 # Greenish/Blue

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

    if top_processes:
        embed["fields"].append({
            "name": "Top Processes",
            "value": f"```{top_processes}```",
            "inline": False
        })

    return embed
