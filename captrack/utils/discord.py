import requests
from datetime import datetime, timezone

EVE_IMAGE_BASE = "https://images.evetech.net"


def eve_character_portrait(character_id: int, size: int = 256) -> str:
    return f"{EVE_IMAGE_BASE}/characters/{character_id}/portrait?size={size}"


def eve_type_render(type_id: int, size: int = 512) -> str:
    return f"{EVE_IMAGE_BASE}/types/{type_id}/render?size={size}"


def build_captrack_embed(
    *,
    character_id: int,
    character_name: str,
    ship_type_name: str,
    ship_type_id: int | None = None,
    system_name: str | None = None,
    structure_name: str | None = None,
    title: str = "⚠️ Capital detected in blacklisted region",
    status_line: str | None = None,
    color: int = 15158332,  # red-ish
) -> dict:
    """
    Returns a single Discord embed dict with portrait thumbnail and optional ship render image.
    """
    embed: dict = {
        "title": title,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "thumbnail": {"url": eve_character_portrait(character_id, 256)},
        "fields": [
            {"name": "Pilot", "value": character_name, "inline": True},
            {"name": "Ship", "value": ship_type_name, "inline": True},
        ],
        "footer": {"text": "CapTrack • AllianceAuth"},
    }

    if ship_type_id:
        embed["image"] = {"url": eve_type_render(ship_type_id, 512)}

    if system_name:
        embed["fields"].append({"name": "System", "value": system_name, "inline": True})

    if structure_name:
        embed["fields"].append({"name": "Structure", "value": structure_name, "inline": False})

    if status_line:
        embed["fields"].append({"name": "Status", "value": status_line, "inline": False})

    return embed


def send_discord_webhook(url: str, *, content: str | None = None, embeds: list[dict] | None = None) -> bool:
    """
    Sends a Discord webhook with optional content and embeds.
    Returns True on success (200/204).
    """
    if not url:
        return False

    payload: dict = {}
    if content:
        payload["content"] = content
    if embeds:
        payload["embeds"] = embeds

    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code in (200, 204)
    except Exception:
        return False
