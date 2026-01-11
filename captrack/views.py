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

    Assumptions (unchanged from previous behavior):
    - Titans & Supercarriers always alert
    - Dreads / Lancers / Carriers / FAX alert only at threshold
    - Snooze is per pilot (by design)
    - Industrials are tracked only
    """

    settings_obj = get_captrack_settings()

    # ------------------------------------------------------------------
    # EXISTING DATA CONSTRUCTION
    #
    # This is intentionally left as-is.
    # Your real implementation already builds this structure.
    #
    # Expected structure:
    # mains = [
    #   {
    #     "main": <main_name>,
    #     "ships": [
    #        {
    #           "pilot": "...",
    #           "cap_class": "dread",
    #           "count_under_main": 6,
    #           ...
    #        }
    #     ]
    #   }
    # ]
    # ------------------------------------------------------------------

    mains = []  # <-- your existing logic populates this

    # ------------------------------------------------------------------
    # Apply settings-driven labels + alerting logic
    # ------------------------------------------------------------------
    for main in mains:
        for ship in main.get("ships", []):
            cap_class = ship.get("cap_class") or "unclassified"
            ship["cap_class"] = cap_class

            ship["cap_class_label"] = cap_class_display_name(cap_class)

            count_under_main = int(ship.get("count_under_main") or 0)
            ship["is_alerting"] = evaluate_alerting(cap_class, count_under_main)

    context = {
        "settings": settings_obj,
        "mains": mains,
    }

    return render(request, "captrack/dashboard.html", context)


# ----------------------------------------------------------------------
# Backwards compatibility
#
# captrack/urls.py expects: views.dashboard
# Do NOT remove unless you also update urls.py
# ----------------------------------------------------------------------
dashboard = captrack_dashboard
