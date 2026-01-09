from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from .models import TrackedCapital, MovementAlert


@login_required
@permission_required("captrack.view_trackedcapital", raise_exception=True)
def dashboard(request):
    capitals = TrackedCapital.objects.order_by("-last_seen")
    alerts = MovementAlert.objects.order_by("-created_at")[:50]

    context = {
        "capitals": capitals,
        "alerts": alerts,
    }
    return render(request, "captrack/dashboard.html", context)