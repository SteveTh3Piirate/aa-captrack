from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from collections import defaultdict

from .models import CapTrackSettings
from .services import get_capitals_in_blacklisted_regions


@login_required
@permission_required("captrack.view_captracksettings", raise_exception=True)
def dashboard(request):
    # Load the single settings row
    settings_obj = CapTrackSettings.objects.first()

    if settings_obj:
        blacklisted_regions = list(settings_obj.blacklisted_regions.all())
    else:
        blacklisted_regions = []

    # Pull all characters violating the blacklist rules
    violating_chars = get_capitals_in_blacklisted_regions(blacklisted_regions)

    # Group results by main character
    grouped = defaultdict(lambda: {"main": None, "alts": []})

    for entry in violating_chars:
        ownership = entry["ownership"]
        user = ownership.user
        main = user.profile.main_character

        grouped[main.id]["main"] = main
        grouped[main.id]["alts"].append(entry)

    # Convert dict → list so the template can iterate cleanly
    groups = list(grouped.values())

    context = {
        "blacklisted_regions": blacklisted_regions,
        "groups": groups,
    }

    return render(request, "captrack/dashboard.html", context)
