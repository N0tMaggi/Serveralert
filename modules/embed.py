import time


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

    embed = {
        "title": f"{title_prefix} - {detection_type}",
        "description": f"Status: {status}\n{separator}",
        "color": 3066993,
        "fields": [
            {"name": "Message", "value": message or "No message", "inline": False},
            {"name": "System", "value": system_info, "inline": False},
        ],
        "footer": {"text": footer_text},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    }

    if status == "CRITICAL":
        embed["color"] = 15158332
    elif status == "WARNING":
        embed["color"] = 15105570

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
