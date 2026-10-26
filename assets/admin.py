from django.contrib import admin

from .models import Asset, AssetHistory, Category, Location

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["full_path", "parent"]
    search_fields = ["name"]

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["tag", "name", "category", "location", "status", "assigned_to"]
    list_filter = ["status", "category", "location"]
    search_fields = ["tag", "name", "serial_number"]
    readonly_fields = ["tag", "created_at", "updated_at"]

@admin.register(AssetHistory)
class AssetHistoryAdmin(admin.ModelAdmin):
    list_display = ["asset", "event_type", "old_value", "new_value", "user", "timestamp"]
    list_filter = ["event_type"]