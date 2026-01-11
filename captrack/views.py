from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import (
    get_captrack_settings,
    cap_class_display_name,
    evaluate_alerting,
)


@login_required
def captrack_dashboard(request):
    """
    Dashboard view with threshold logic driven by CapTrackSettings.

    NOTE: This file assumes your existing view was already building:
      - a list of pilots grouped by main
      - counts per class under the same main
      - snooze filtering (per pilot, by design)
    The only change is that "alerting" is computed via evaluate_alerting()
    and labels via cap_class_display_name().
    """
    settings_obj = get_captrack_settings()

    # ---- Your existing data construction would be here ----
    # We keep variables generic so you can splice with minimal disruption.
    # Example structure expected downstream:
    # mains = [
    #   {
    #     "main": <main_name>,
    #     "ships": [
    #        {"pilot": ..., "cap_class": "dread", "count_under_main": 6, ...}
    #     ]
    #   }
    # ]

    mains = []  # <-- your existing logic populates this

    # Apply settings-driven label + alerting
    for main in mains:
        for ship in main.get("ships", []):
            cap_class = ship.get("cap_class") or "unclassified"
            ship["cap_class"] = cap_class
            ship["cap_class_label"] = cap_class_display_name(cap_class)

            count_under_main = ship.get("count_under_main") or 0
            ship["is_alerting"] = evaluate_alerting(cap_class, int(count_under_main))

    context = {
        "settings": settings_obj,
        "mains": mains,
    }
    return render(request, "captrack/dashboard.html", context)
