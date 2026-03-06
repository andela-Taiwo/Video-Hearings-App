from django.contrib import admin
from .models import Court, Courtroom


class CourtroomInline(admin.TabularInline):
    model = Courtroom
    extra = 1
    fields = ["name", "capacity", "video_platform_config"]


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ["name", "jurisdiction", "courtroom_count", "created_at"]
    list_filter = ["jurisdiction", "created_at"]
    search_fields = ["name", "jurisdiction", "address"]
    inlines = [CourtroomInline]
    readonly_fields = ["created_at"]
    fieldsets = (
        ("Basic Information", {"fields": ("name", "jurisdiction", "address")}),
        (
            "Contact Information",
            {
                "fields": ("contact_info",),
                "classes": ("wide",),
                "description": "JSON field for phone, email, website, etc.",
            },
        ),
        ("Metadata", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def courtroom_count(self, obj):
        return obj.courtrooms.count()

    courtroom_count.short_description = "Courtrooms"


@admin.register(Courtroom)
class CourtroomAdmin(admin.ModelAdmin):
    list_display = ["name", "court", "capacity", "has_video_config"]
    list_filter = ["court", "capacity"]
    search_fields = ["name", "court__name"]
    raw_id_fields = ["court"]

    def has_video_config(self, obj):
        return bool(obj.video_platform_config)

    has_video_config.boolean = True
    has_video_config.short_description = "Video Config"
