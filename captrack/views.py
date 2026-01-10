from django.shortcuts import render
from .models import BlacklistedRegion
from .services import get_capitals_in_blacklisted_regions

def dashboard(request):
    blacklisted_regions = BlacklistedRegion.objects.all()
    groups = get_capitals_in_blacklisted_regions()

    return render(
        request,
        "captrack/dashboard.html",
        {
            "blacklisted_regions": blacklisted_regions,
            "groups": groups,
        }
    )
