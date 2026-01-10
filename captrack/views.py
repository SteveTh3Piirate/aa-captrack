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

    # Real Corptools-powered capital discovery
    violating_chars = get_capitals_in_blacklisted_regions(blacklisted_regions)

    # Group by main character
    grouped = defaultdict(lambda: {"main": None, "alts": []})

    for char in violating_chars:
        user = char.user
        main = user.profile.main_character

        grouped[main.id]["main"] = main
        grouped[main.id]["alts"].append(char)

    context = {
        "blacklisted_regions": blacklisted_regions,
        "groups": grouped.values(),   # <-- send grouped data to template
    }

    return render(request, "captrack/dashboard.html", context)