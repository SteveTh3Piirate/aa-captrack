from django.db import models
from eveuniverse.models import EveRegion


class CapTrackSettings(models.Model):
    """
    Stores configuration for CapTrack, including which regions
    are considered blacklisted for capital ship presence.
    """
    id = models.BigAutoField(primary_key=True)

    blacklisted_regions = models.ManyToManyField(
        EveRegion,
        blank=True,
        help_text="Select regions to blacklist for capital tracking."
    )

    webhook_url = models.URLField(
        blank=True,
        null=True,
        help_text="Discord webhook URL for cap notifications."
    )

    class Meta:
        verbose_name = "CapTrack settings"
        verbose_name_plural = "CapTrack settings"

    def __str__(self):
        return "CapTrack Settings"
