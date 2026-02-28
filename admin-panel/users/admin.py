from django.contrib import admin

from users.models import AppUser, Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "legal_form", "email", "created_at")
    list_display_links = ("name",)
    search_fields = ("name", "email")
    list_filter = ("legal_form",)
    readonly_fields = ("created_at",)


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "role",
        "company",
        "is_active",
        "created_at",
    )
    list_display_links = ("email",)
    search_fields = ("email",)
    list_filter = ("role", "is_active", "company")
    readonly_fields = ("created_at", "password_hash")
