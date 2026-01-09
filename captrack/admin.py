from django.contrib import admin
from .models import HomeConfig, TrackedCapital, MovementAlert


@admin.register(HomeConfig)
class HomeConfigAdmin(admin.ModelAdmin):
    list_display = ("home_system_name", "allowed_jumps")


@admin.register(TrackedCapital)
class TrackedCapitalAdmin(admin.ModelAdmin):
    list_display = (
        "character_name",
        "ship_type_name",
        "system_name",
        "distance_from_home",
        "last_seen",
    )
    search_fields = ("character_name", "ship_type_name", "system_name")


@admin.register(MovementAlert)
class MovementAlertAdmin(admin.ModelAdmin):
    list_display = (
        "character_name",
        "ship_type_name",
        "old_system",
        "new_system",
        "distance_from_home",
        "created_at",
    )
    search_fields = ("character_name", "ship_type_name", "old_system", "new_system")
    ordering = ("-created_at",)