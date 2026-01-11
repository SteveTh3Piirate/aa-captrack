from django.db import models

class Character(models.Model):
    character_id = models.BigIntegerField(unique=True)
    character_name = models.CharField(max_length=255)

    def __str__(self):
        return self.character_name


class CharacterOwnership(models.Model):
    # Minimal shape: enough for your OneToOneField + the template/admin lookups
    character = models.OneToOneField(Character, on_delete=models.CASCADE)

    def __str__(self):
        return f"Ownership({self.character})"
