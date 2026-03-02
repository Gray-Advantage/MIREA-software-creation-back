from django.contrib import admin

from .models import Adjustment, EmployeeProfile, QRSession, Schedule, TimeEntry


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "position",
        "rate_type",
        "rate_amount",
        "currency",
        "user",
    )
    list_display_links = ("full_name",)
    search_fields = ("full_name", "position")
    list_filter = ("rate_type", "currency")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Adjustment)
class AdjustmentAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "type", "amount", "date", "comment")
    list_filter = ("type", "date")
    search_fields = ("comment",)
    readonly_fields = ("created_at",)


@admin.register(QRSession)
class QRSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "token",
        "company",
        "is_active",
        "expires_at",
        "created_at",
    )
    list_filter = ("is_active", "company")
    readonly_fields = ("created_at",)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "date", "start_time", "end_time")
    list_filter = ("date",)
    search_fields = ("employee__full_name",)


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "date", "check_in", "check_out")
    list_filter = ("date",)
    readonly_fields = ("created_at",)
