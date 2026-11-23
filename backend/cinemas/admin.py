from django.contrib import admin

from cinemas.models import Cinema


@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = ["name", "bundle_sizes"]
