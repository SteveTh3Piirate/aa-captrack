import logging

from celery import shared_task

from .services import (
    get_captrack_settings,
    cap_class_display_name,
    evaluate_alerting,
)

logger = logging.getLogger(__name__)

try:
    from .utils.discord import send_discord_webhook
except Exception:
    send_discord_webhook = None


def _discord_role_ping(settings_obj) -> str:
    if not settings_obj.discord_ping_role_id:
        return ""
    return f"<@&{settings_obj.discord_ping_role_id}>"


def _post_webhook(url: str, content: str, embed: dict | None = None):
    if not url or not send_discord_webhook:
        return
    try:
        # Newer signature (content kwarg) – if your helper supports it.
        send_discord_webhook(url, content=content, embed=embed)
    except TypeError:
        # Older signature fallback
        if embed is not None:
            send_discord_webhook(url, embed)
        else:
            send_discord_webhook(url, content)


@shared_task
def captrack_discord_alerts():
    """
    Settings-driven Discord alert task.

    Behavior preserved by defaults:
      - Discord shows ONLY alerting ships (alerting_only_discord=True)
      - Titans/Supers always alert
      - Others alert at thresholds_by_class (default 5)
    """
    settings_obj = get_captrack_settings()
    if not settings_obj.is_enabled or not settings_obj.discord_enabled:
        return

    # ---- Your existing data fetch / aggregation goes here ----
    # Expected structure:
    # alert_candidates = [
    #   {"main": "MainName", "pilot": "...", "cap_class": "dread", "count_under_main": 6, "system": "...", "region": "..."}
    # ]
    alert_candidates = []  # <-- your existing logic populates this

    # Filter + classify
    alerting = []
    has_critical = False
    for item in alert_candidates:
        cap_class = item.get("cap_class") or "unclassified"
        item["cap_class"] = cap_class
        item["cap_class_label"] = cap_class_display_name(cap_class)
        count_under_main = int(item.get("count_under_main") or 0)

        item["is_alerting"] = evaluate_alerting(cap_class, count_under_main)
        if item["is_alerting"]:
            alerting.append(item)
            if cap_class in (settings_obj.always_alert_classes or []):
                has_critical = True

    if settings_obj.alerting_only_discord:
        payload_items = alerting
    else:
        payload_items = alert_candidates

    if not payload_items:
        return

    # Build message
    ping = ""
    if settings_obj.discord_ping_policy == "all_alerts":
        ping = _discord_role_ping(settings_obj)
    elif settings_obj.discord_ping_policy == "critical_only" and has_critical:
        ping = _discord_role_ping(settings_obj)

    # Simple embed (you can swap this for your existing formatting)
    lines = []
    for it in payload_items:
        marker = "🚨" if it.get("is_alerting") else "•"
        cls = it.get("cap_class_label") or it.get("cap_class") or "Unclassified"
        main = it.get("main") or "Unknown"
        pilot = it.get("pilot") or "Unknown"
        count = it.get("count_under_main") or 0

        loc = ""
        if settings_obj.discord_include_system_region:
            sys = it.get("system") or ""
            reg = it.get("region") or ""
            if sys or reg:
                loc = f" ({sys}{' / ' if sys and reg else ''}{reg})"

        lines.append(f"{marker} **{cls}** x{count} — {pilot} [{main}]{loc}")

    embed = {
        "title": "CapTrack Alerts",
        "description": "\n".join(lines[:50]),
    }

    # Route webhooks
    url_alerts = settings_obj.discord_webhook_url_alerts or settings_obj.discord_webhook_url_critical
    url_critical = settings_obj.discord_webhook_url_critical or url_alerts

    # If we have critical ships, post to critical webhook too
    if has_critical and url_critical:
        _post_webhook(url_critical, ping, embed=embed)

    if url_alerts:
        _post_webhook(url_alerts, ping, embed=embed)
