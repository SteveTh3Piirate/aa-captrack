from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect

from .models import CapTrackSettings, CapTrackSettingsAudit


@admin.register(CapTrackSettingsAudit)
class CapTrackSettingsAuditAdmin(admin.ModelAdmin):
    list_display = ("changed_at", "changed_by")
    readonly_fields = ("changed_at", "changed_by", "diff")
    search_fields = ("changed_by__username",)
    ordering = ("-changed_at",)


@admin.register(CapTrackSettings)
class CapTrackSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("General", {"fields": ("is_enabled",)}),
        ("Tracking", {"fields": ("tracked_group_ids", "tracked_industrial_group_ids")}),
        ("Classification & Labels", {"fields": ("class_display_names", "show_unclassified_bucket")}),
        ("Alert Rules", {"fields": ("always_alert_classes", "thresholds_by_class", "ignore_classes", "include_tracked_only_in_dashboard")}),
        ("Discord", {"fields": ("discord_enabled", "discord_webhook_url_critical", "discord_webhook_url_alerts", "discord_ping_policy", "discord_ping_role_id", "discord_message_mode", "discord_include_system_region", "discord_include_dashboard_link", "dashboard_base_url", "alerting_only_discord")}),
        ("Snooze", {"fields": ("snooze_scope", "snooze_durations_minutes")}),
        ("Dashboard", {"fields": ("dashboard_refresh_seconds", "dashboard_default_collapsed", "dashboard_remember_collapse_state")}),
    )

    def has_add_permission(self, request):
        # Singleton: only allow add if no settings exist
        return not CapTrackSettings.objects.exists()

    def save_model(self, request, obj, form, change):
        # Save and write an audit record with changed_by
        super().save_model(request, obj, form, change)
        # Attach changed_by to the latest audit entry if present and missing
        latest = obj.audit_entries.first()
        if latest and latest.changed_by_id is None:
            latest.changed_by = request.user
            latest.save(update_fields=["changed_by"])

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("send-test-alerts/", self.admin_site.admin_view(self.send_test_alerts), name="captrack_send_test_alerts"),
            path("send-test-critical/", self.admin_site.admin_view(self.send_test_critical), name="captrack_send_test_critical"),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["captrack_test_buttons"] = True
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["captrack_test_buttons"] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def _send_test(self, request, critical: bool):
        # Lazy import to avoid circulars
        try:
            from .tasks import _post_webhook, _discord_role_ping
        except Exception as e:
            messages.error(request, f"Unable to import Discord sender: {e}")
            return redirect("..")

        settings_obj = CapTrackSettings.objects.first()
        if not settings_obj:
            messages.error(request, "No CapTrackSettings row found. Create/save settings first.")
            return redirect("..")

        if not settings_obj.discord_enabled:
            messages.warning(request, "Discord is disabled in settings.")
            return redirect("..")

        url = settings_obj.discord_webhook_url_critical if critical else (settings_obj.discord_webhook_url_alerts or settings_obj.discord_webhook_url_critical)
        if not url:
            messages.error(request, "No Discord webhook URL set in settings.")
            return redirect("..")

        ping = ""
        if settings_obj.discord_ping_policy == "all_alerts":
            ping = _discord_role_ping(settings_obj)
        elif settings_obj.discord_ping_policy == "critical_only" and critical:
            ping = _discord_role_ping(settings_obj)

        embed = {
            "title": "CapTrack Test Message (Critical)" if critical else "CapTrack Test Message (Alerts)",
            "description": "This is a test message from CapTrack admin settings.",
        }

        _post_webhook(url, ping, embed=embed)
        messages.success(request, "Test message sent.")
        return redirect("..")

    def send_test_alerts(self, request):
        return self._send_test(request, critical=False)

    def send_test_critical(self, request):
        return self._send_test(request, critical=True)
