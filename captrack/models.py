from django.db import models


class HomeConfig(models.Model):
    """Config for home system and allowed radius."""
    home_system_id = models.IntegerField()
    home_system_name = models.CharField(max_length=255)
    allowed_jumps = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.home_system_name} ({self.allowed_jumps} jumps)"


class TrackedCapital(models.Model):
    """Current known state of a capital ship for a character."""
    character_id = models.BigIntegerField()
    character_name = models.CharField(max_length=255)

    ship_type_id = models.IntegerField()
    ship_type_name = models.CharField(max_length=255)

    system_id = models.IntegerField(null=True, blank=True)
    system_name = models.CharField(max_length=255, null=True, blank=True)

    distance_from_home = models.IntegerField(null=True, blank=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.character_name} - {self.ship_type_name} @ {self.system_name}"


class MovementAlert(models.Model):
    """History of movement events that triggered alerts."""
    character_name = models.CharField(max_length=255)
    ship_type_name = models.CharField(max_length=255)

    old_system = models.CharField(max_length=255)
    new_system = models.CharField(max_length=255)

    distance_from_home = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.character_name} moved {self.ship_type_name} {self.old_system} → {self.new_system}"