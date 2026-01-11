from django.conf import settings as django_settings

from .models import CapTrackSettings


def get_captrack_settings() -> CapTrackSettings:
    """
    Returns the singleton CapTrackSettings row (pk=1), creating it with safe defaults if missing.
    """
    settings_obj, _ = CapTrackSettings.objects.get_or_create(
        pk=1,
        defaults={
            "is_enabled": True,
            "class_display_names": {
                "titan": "Titan",
                "supercarrier": "Supercarrier",
                "dread": "Dreadnought",
                "lancer_dread": "Lancer Dreadnought",
                "carrier": "Carrier",
                "fax": "Force Auxiliary",
                "industrial": "Capital Industrial",
                "unclassified": "Unclassified",
            },
            "always_alert_classes": ["titan", "supercarrier"],
            "thresholds_by_class": {
                "dread": 5,
                "lancer_dread": 5,
                "carrier": 5,
                "fax": 5,
            },
            "snooze_durations_minutes": [60, 360, 1440],
            "discord_enabled": True,
            "discord_ping_policy": "critical_only",
            "alerting_only_discord": True,
            "include_tracked_only_in_dashboard": True,
            "dashboard_refresh_seconds": 60,
            "show_unclassified_bucket": True,
        },
    )
    return settings_obj


def cap_class_display_name(cap_class: str) -> str:
    s = get_captrack_settings()
    return s.class_display_names.get(cap_class, s.class_display_names.get("unclassified", "Unclassified"))


def is_alerting_class(cap_class: str) -> bool:
    s = get_captrack_settings()
    if cap_class in (s.ignore_classes or []):
        return False
    return cap_class in (s.always_alert_classes or []) or cap_class in (s.thresholds_by_class or {})


def evaluate_alerting(cap_class: str, count_under_main: int) -> bool:
    """
    Apply policy: always alert for some classes; threshold alert for others.
    """
    s = get_captrack_settings()
    if cap_class in (s.ignore_classes or []):
        return False

    if cap_class in (s.always_alert_classes or []):
        return True

    thresholds = s.thresholds_by_class or {}
    if cap_class in thresholds:
        try:
            threshold = int(thresholds[cap_class])
        except Exception:
            threshold = 999999
        return count_under_main >= threshold

    return False


def get_tracked_group_ids() -> list[int]:
    """
    Returns tracked capital group IDs, preferring settings if configured,
    otherwise falling back to module-level / Django settings constants.
    """
    s = get_captrack_settings()
    if s.tracked_group_ids:
        return [int(x) for x in s.tracked_group_ids if str(x).isdigit()]

    # Fallbacks (preserve existing behavior if your project uses one of these)
    if hasattr(django_settings, "CAPITAL_GROUP_IDS"):
        return list(getattr(django_settings, "CAPITAL_GROUP_IDS"))

    return []


def get_tracked_industrial_group_ids() -> list[int]:
    s = get_captrack_settings()
    if s.tracked_industrial_group_ids:
        return [int(x) for x in s.tracked_industrial_group_ids if str(x).isdigit()]

    if hasattr(django_settings, "INDUSTRIAL_GROUP_IDS"):
        return list(getattr(django_settings, "INDUSTRIAL_GROUP_IDS"))

    return []


def classify_ship_group(group_id: int) -> str:
    """
    This is a light wrapper around your existing classification rules.
    If your existing services.py already classifies, keep your mappings and
    normalize to stable keys:
      titan, supercarrier, dread, lancer_dread, carrier, fax, industrial, unclassified
    """
    # NOTE: preserve any existing mapping you already had
    # This is intentionally conservative: if your original file already contains
    # the full mapping logic, keep it and ensure it returns one of the keys above.

    # Placeholder example (you likely already have this logic in your current file):
    # return "unclassified"
    return "unclassified"
