import requests
from datetime import datetime, timezone
from typing import Optional, Sequence

EVE_IMAGE_BASE = "https://images.evetech.net"


def eve_character_portrait(character_id: int, size: int = 256) -> str:
    return f"{EVE_IMAGE_BASE}/characters/{character_id}/portrait?size={size}"


def eve_type_render(type_id: int, size: int = 512) -> str:
    return f"{EVE_IMAGE_BASE}/types/{type_id}/render?size={size}"


# ------------------------------------------------------------------
# Alert level presentation
# ------------------------------------------------------------------
ALERT_STYLES = {
    "critical": {
        "emoji": "🚨",
        "color": 0x8B0000,  # dark red
        "title": "Critical capitals detected",
    },
    "high": {
        "emoji": "⚠️",
        "color": 0xE67E22,  # orange
        "title": "High-risk capitals detected",
    },
    "medium": {
        "emoji": "🟡",
        "color": 0xF1C40F,  # yellow
        "title": "Capitals detected",
    },
    "industrial": {
        "emoji": "🏭",
        "color": 0x3498DB,  # blue
        "title": "Capital industrial detected",
    },
    "unknown": {
        "emoji": "❔",
        "color": 0x95A5A6,  # grey
        "title": "Unknown capitals detected",
    },
}


def _truncate(s: str, max_len: int) -> str:
    if s is None:
        return ""
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def _rank_alert_level(level: str) -> int:
    # Higher is more severe
    return {"critical": 4, "high": 3, "medium": 2, "industrial": 1, "unknown": 0}.get(level or "unknown", 0)


# ------------------------------------------------------------------
# Single-character embed (kept for compatibility)
# ------------------------------------------------------------------
def build_captrack_embed(
    *,
    character_id: int,
    character_name: str,
    ship_type_name: str,
    ship_type_id: Optional[int] = None,
    system_name: Optional[str] = None,
    structure_name: Optional[str] = None,
    location: Optional[str] = None,
    alert_level: str = "unknown",
    title: Optional[str] = None,
    status_line: Optional[str] = None,
    color: Optional[int] = None,
    dashboard_url: Optional[str] = None,
) -> dict:
    style = ALERT_STYLES.get(alert_level, ALERT_STYLES["unknown"])
    embed_title = title or f"{style['emoji']} {style['title']}"
    embed_color = color if color is not None else style["color"]

    embed: dict = {
        "title": embed_title,
        "color": embed_color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "thumbnail": {"url": eve_character_portrait(character_id, 256)},
        "fields": [
            {"name": "Pilot", "value": character_name, "inline": True},
            {"name": "Ship", "value": ship_type_name, "inline": True},
            {"name": "Alert Level", "value": alert_level.capitalize(), "inline": True},
        ],
        "footer": {"text": "CapTrack • AllianceAuth"},
    }

    if dashboard_url:
        embed["url"] = dashboard_url

    if ship_type_id:
        embed["image"] = {"url": eve_type_render(ship_type_id, 512)}

    if location:
        embed["fields"].append({"name": "Location", "value": location, "inline": False})
    elif system_name:
        embed["fields"].append({"name": "System", "value": system_name, "inline": True})

    if structure_name:
        embed["fields"].append({"name": "Structure", "value": structure_name, "inline": False})

    if status_line:
        embed["fields"].append({"name": "Status", "value": status_line, "inline": False})

    return embed


# ------------------------------------------------------------------
# Consolidated embed (one per main)
# ------------------------------------------------------------------
def build_captrack_main_embed(
    *,
    main_character_id: int,
    main_character_name: str,
    entries: Sequence[dict],
    title: Optional[str] = None,
    dashboard_url: Optional[str] = None,
    snoozed_lines: Optional[Sequence[str]] = None,
    status_line: Optional[str] = None,
) -> dict:
    # Determine overall severity for styling
    max_level = "unknown"
    max_rank = -1
    for e in entries:
        lvl = e.get("alert_level") or e.get("risk") or "unknown"
        r = _rank_alert_level(lvl)
        if r > max_rank:
            max_rank = r
            max_level = lvl

    style = ALERT_STYLES.get(max_level, ALERT_STYLES["unknown"])
    embed_title = title or f"{style['emoji']} {style['title']} • {main_character_name}"

    # Build a compact per-alt listing
    # One field value max is 1024 chars; be safe.
    lines = []
    for e in entries:
        lvl = (e.get("alert_level") or e.get("risk") or "unknown").upper()
        ch_name = e.get("character_name") or "Unknown"
        ship = e.get("ship_type") or "Unknown ship"
        system = e.get("system") or "Unknown system"
        structure = e.get("structure") or ""
        structure_txt = f" — {structure}" if structure else ""
        lines.append(f"`{lvl:<10}` **{ch_name}** — {ship} — {system}{structure_txt}")

    body = _truncate("\n".join(lines), 1000)

    embed: dict = {
        "title": embed_title,
        "color": style["color"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "thumbnail": {"url": eve_character_portrait(main_character_id, 256)},
        "fields": [
            {"name": "Detected", "value": body or "—", "inline": False},
        ],
        "footer": {"text": "CapTrack • AllianceAuth"},
    }

    if dashboard_url:
        embed["url"] = dashboard_url

    if status_line:
        embed["fields"].append({"name": "Status", "value": status_line, "inline": False})

    if snoozed_lines:
        snoozed_body = _truncate("\n".join(snoozed_lines), 1000)
        embed["fields"].append({"name": "Snoozed", "value": snoozed_body, "inline": False})

    return embed


def send_discord_webhook(url: str, *, content: Optional[str] = None, embeds: Optional[list[dict]] = None) -> bool:
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
