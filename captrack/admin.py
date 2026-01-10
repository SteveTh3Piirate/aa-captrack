from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.core.exceptions import ValidationError

from .models import CapTrackSettings
from eveuniverse.models import EveRegion


@admin.register(CapTrackSettings)
class CapTrackSettingsAdmin(admin.ModelAdmin):
    autocomplete_fields = ("blacklisted_regions",)
    fields = ("blacklisted_regions", "webhook_url", "test_webhook_button")
    readonly_fields = ("test_webhook_button",)

    def test_webhook_button(self, obj):
        if not obj.pk:
            return "Save settings first."
        return (
            '<a class="button" href="test-webhook/">Send Test Webhook</a>'
        )
    test_webhook_button.allow_tags = True
    test_webhook_button.short_description = "Webhook Test"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/test-webhook/",
                self.admin_site.admin_view(self.test_webhook_view),
                name="captrack_test_webhook",
            )
        ]
        return custom + urls

    def test_webhook_view(self, request, object_id):
        obj = self.get_object(request, object_id)

        try:
            obj.send_test_webhook()  # your existing method
            self.message_user(request, "Webhook sent successfully.", messages.SUCCESS)
        except ValidationError as e:
            self.message_user(request, f"Webhook failed: {e}", messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Unexpected error: {e}", messages.ERROR)

        return redirect(f"../../")