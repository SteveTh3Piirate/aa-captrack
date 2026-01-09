from django.contrib import admin
from .models import EveRegion, EveConstellation, EveSolarSystem, EveType

@admin.register(EveRegion)
class EveRegionAdmin(admin.ModelAdmin):
    search_fields = ["name"]

@admin.register(EveConstellation)
class EveConstellationAdmin(admin.ModelAdmin):
    search_fields = ["name"]

@admin.register(EveSolarSystem)
class EveSolarSystemAdmin(admin.ModelAdmin):
    search_fields = ["name"]

@admin.register(EveType)
class EveTypeAdmin(admin.ModelAdmin):
    search_fields = ["name"]