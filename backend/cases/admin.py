from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Case, CaseParty


class CasePartyInline(admin.TabularInline):
    model = CaseParty
    extra = 1
    raw_id_fields = ["user"]
    fields = ["user", "party_role", "added_at"]
    readonly_fields = ["added_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = [
        "case_number",
        "title",
        "case_type",
        "status_colored",
        "judge_link",
        "party_count",
        "created_at_display",
    ]
    list_filter = ["status", "case_type", "created_at"]
    search_fields = [
        "case_number",
        "title",
        "judge__email",
        "judge__first_name",
        "judge__last_name",
    ]
    readonly_fields = ["created_at", "updated_at", "party_count_display"]
    raw_id_fields = ["judge"]
    inlines = [CasePartyInline]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("case_number", "title", "case_type", "status")},
        ),
        ("Judicial Assignment", {"fields": ("judge",)}),
        (
            "Statistics",
            {
                "fields": ("party_count_display", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_closed", "mark_as_appealed"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("judge")
            .prefetch_related("caseparty_set")
            .annotate(party_count=Count("caseparty"))
        )

    def status_colored(self, obj):
        colors = {
            "open": "green",
            "closed": "red",
            "appealed": "orange",
            "stayed": "blue",
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, "black"),
            obj.get_status_display(),
        )

    status_colored.short_description = "Status"
    status_colored.admin_order_field = "status"

    def judge_link(self, obj):
        """Link to the judge's admin change page"""
        if obj.judge:
            # Fix: Use the correct admin URL pattern name for your custom User model
            url = reverse("admin:accounts_user_change", args=[obj.judge.id])
            return format_html('<a href="{}">{}</a>', url, obj.judge.get_full_name())
        return "-"

    judge_link.short_description = "Judge"
    judge_link.admin_order_field = "judge__last_name"

    def party_count(self, obj):
        return getattr(obj, "party_count", obj.get_party_count())

    party_count.short_description = "Parties"
    party_count.admin_order_field = "party_count"

    def party_count_display(self, obj):
        count = getattr(obj, "party_count", obj.get_party_count())
        return f"{count} parties assigned"

    party_count_display.short_description = "Party Count"

    def created_at_display(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")

    created_at_display.short_description = "Created"
    created_at_display.admin_order_field = "created_at"

    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status=Case.Status.CLOSED)
        self.message_user(request, f"{updated} cases marked as closed.")

    mark_as_closed.short_description = "Mark selected cases as closed"

    def mark_as_appealed(self, request, queryset):
        updated = queryset.update(status=Case.Status.APPEALED)
        self.message_user(request, f"{updated} cases marked as appealed.")

    mark_as_appealed.short_description = "Mark selected cases as appealed"

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new case
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CaseParty)
class CasePartyAdmin(admin.ModelAdmin):
    list_display = ["case_link", "user_link", "party_role_display", "added_at"]
    list_filter = ["party_role", "added_at"]
    search_fields = [
        "case__case_number",
        "user__email",
        "user__first_name",
        "user__last_name",
    ]
    raw_id_fields = ["case", "user"]
    date_hierarchy = "added_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("case", "user")

    def case_link(self, obj):
        url = reverse("admin:cases_case_change", args=[obj.case.id])
        return format_html('<a href="{}">{}</a>', url, obj.case.case_number)

    case_link.short_description = "Case"
    case_link.admin_order_field = "case__case_number"

    def user_link(self, obj):
        if obj.user:
            # Fix: Use the correct admin URL pattern name for your custom User model
            url = reverse("admin:accounts_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
        return "-"

    user_link.short_description = "User"
    user_link.admin_order_field = "user__last_name"

    def party_role_display(self, obj):
        return obj.get_party_role_display()

    party_role_display.short_description = "Party Role"
