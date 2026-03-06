from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from .models import User, UserProfile


class CustomUserChangeForm(UserChangeForm):
    """Form for updating users in admin that excludes username field."""

    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field if it exists
        if "username" in self.fields:
            del self.fields["username"]


class CustomUserCreationForm(UserCreationForm):
    """Form for creating users in admin that excludes username field."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "username" in self.fields:
            del self.fields["username"]


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ["role", "bar_number", "court_id", "bio"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = [
        "email",
        "get_full_name",
        "get_role",
        "get_is_verified_badge",
        "is_active",
        "is_staff",
        "get_date_joined_display",
    ]
    list_filter = ["is_staff", "is_superuser", "is_verified", "profile__role"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]

    # REMOVE THIS LINE - it's causing the error
    # exclude = ('username', 'password1', 'password2', 'usable_password')

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone_number")}),
        (
            "Verification",
            {"fields": ("is_verified", "is_email_verified", "is_admin_approved")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at", "last_login", "date_joined"]
    inlines = [UserProfileInline]

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = "Full Name"

    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return "-"

    get_role.short_description = "Role"

    def get_is_verified_badge(self, obj):
        if obj.is_verified:
            return mark_safe('<span style="color: green;">✓ Verified</span>')
        return mark_safe('<span style="color: orange;">✗ Unverified</span>')

    def get_date_joined_display(self, obj):
        return obj.date_joined.strftime("%Y-%m-%d %H:%M")

    get_date_joined_display.short_description = "Joined"

    actions = ["approve_users"]

    def approve_users(self, request, queryset):
        for user in queryset:
            user.admin_approve()
        self.message_user(request, f"{queryset.count()} users approved.")

    approve_users.short_description = "Approve selected users"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user_email", "role_display", "bar_number", "court_id"]
    list_filter = [
        "role",
    ]
    search_fields = ["user__email", "bar_number", "court_id"]
    raw_id_fields = ["user"]

    fieldsets = (
        (None, {"fields": ("user", "role")}),
        (
            "Professional Info",
            {"fields": ("bar_number", "court_id", "specialization", "bio")},
        ),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ["created_at", "updated_at"]

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Email"

    def role_display(self, obj):
        return obj.get_role_display()

    role_display.short_description = "Role"
