from rest_framework import serializers
from django.utils import timezone
from .models import Hearing, HearingParticipant, HearingDocument
from cases.serializers import CaseDetailSerializer
from courts.serializers import CourtroomSerializer
from rest_framework import serializers
from django.core.validators import EmailValidator
from django.contrib.auth import get_user_model
from rest_framework import serializers

from cases.models import Case
from courts.models import Courtroom

User = get_user_model()


# =============================================
#  DOCUMENT SERIALIZERS
# ===============================================
class HearingDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.ReadOnlyField(source="uploaded_by.email")

    class Meta:
        model = HearingDocument
        fields = [
            "id",
            "hearing",
            "doc_type",
            "file",
            "file_name",
            "file_size",
            "content_type",
            "is_sealed",
            "admitted",
            "uploaded_at",
            "uploaded_by",
            "uploaded_by_email",
        ]
        read_only_fields = [
            "id",
            "uploaded_at",
            "file_name",
            "file_size",
            "content_type",
        ]

    def validate_file(self, value):
        # Add file validation
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size cannot exceed {max_size // (1024 * 1024)}MB"
            )

        # Validate file type
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "video/mp4"]
        if hasattr(value, "content_type") and value.content_type not in allowed_types:
            raise serializers.ValidationError("File type not allowed")

        return value


class HearingStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Hearing.Status.choices)

    def validate_status(self, value):
        hearing = self.context.get("hearing")
        if hearing:
            # Add status transition validation
            allowed_transitions = {
                "scheduled": ["in_progress", "cancelled", "postponed"],
                "in_progress": ["recessed", "completed"],
                "recessed": ["in_progress", "completed"],
                "completed": [],
                "cancelled": [],
                "postponed": ["scheduled"],
            }

            if value not in allowed_transitions.get(hearing.status, []):
                raise serializers.ValidationError(
                    f"Cannot transition from {hearing.status} to {value}"
                )
        return value


class HearingDocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = HearingDocument
        fields = ["doc_type", "file", "is_sealed"]


# ==================================================================
#                HEARRINGS SERIALIZERS
# ==================================================================
class HearingParticipantSerializer(serializers.ModelSerializer):
    """Serializer for hearing participants"""

    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = HearingParticipant
        fields = [
            "id",
            "user",
            "user_name",
            "user_email",
            "role",
            "joined_at",
            "left_at",
        ]
        read_only_fields = ["id", "joined_at", "left_at"]

    def to_representation(self, instance):
        """Remove null fields from the response"""
        data = super().to_representation(instance)

        # Remove fields with None values
        return {key: value for key, value in data.items() if value is not None}


class HearingSerializer(serializers.ModelSerializer):
    """Main Hearing serializer for read operations"""

    case_number = serializers.CharField(source="case.case_number", read_only=True)
    courtroom_name = serializers.CharField(source="courtroom.name", read_only=True)
    case = CaseDetailSerializer(read_only=True)
    participants = HearingParticipantSerializer(many=True, read_only=True)
    participant_count = serializers.IntegerField(
        source="participants.count", read_only=True
    )

    class Meta:
        model = Hearing
        fields = [
            "id",
            "case",
            "case_number",
            "courtroom",
            "courtroom_name",
            "name",
            "description",
            "hearing_type",
            "status",
            "scheduled_at",
            "ended_at",
            "created_at",
            "updated_at",
            "participants",
            "participant_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "ended_at"]

    def to_representation(self, instance):
        """Remove null fields from the response"""
        data = super().to_representation(instance)

        # Remove fields with None values
        return {key: value for key, value in data.items() if value is not None}


class DeleteParticipantsSerializer(serializers.Serializer):
    """Serializer for validating participant deletion requests"""

    participant_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=False
    )
    participant_emails = serializers.ListField(
        child=serializers.EmailField(), required=False, allow_empty=False
    )
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=HearingParticipant.PartyRole.choices),
        required=False,
        allow_empty=False,
    )
    user_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=False
    )

    def validate(self, data):
        if not any(
            [
                data.get("participant_ids"),
                data.get("participant_emails"),
                data.get("roles"),
                data.get("user_ids"),
            ]
        ):
            raise serializers.ValidationError(
                "At least one deletion criterion must be provided"
            )
        return data


class CreateHearingParticipantSerializer(serializers.Serializer):
    """Serializer for creating hearing participants"""

    user_id = serializers.IntegerField(required=True)
    role = serializers.CharField(required=True, max_length=50)

    def validate_role(self, value):
        """Validate that the role is one of the allowed values"""
        allowed_roles = [
            "judge",
            "plaintiff",
            "defendant",
            "lawyer",
            "witness",
            "clerk",
            "prosecutor",
        ]
        if value.lower() not in allowed_roles:
            raise serializers.ValidationError(
                f"Role must be one of: {', '.join(allowed_roles)}"
            )
        return value.lower()

    def validate_user_id(self, value):
        """Validate that the user exists"""
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"User with id {value} does not exist")
        return value


class AddParticipantSerializer(serializers.Serializer):
    """Serializer for adding a single participant to a hearing"""

    email = serializers.EmailField(
        required=True, help_text="Participant's email address"
    )
    role = serializers.ChoiceField(
        choices=HearingParticipant.PartyRole.choices,
        required=True,
        help_text="Participant's role in the hearing",
    )
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="First name (required for new users)",
    )
    last_name = serializers.CharField(
        required=False, allow_blank=True, help_text="Last name (required for new users)"
    )
    phone_number = serializers.CharField(
        required=False, allow_blank=True, help_text="Phone number (optional)"
    )
    bar_number = serializers.CharField(
        required=False, allow_blank=True, help_text="Bar number (required for lawyers)"
    )
    court_id = serializers.UUIDField(
        required=False, help_text="Court ID (required for judges and clerks)"
    )
    send_invite = serializers.BooleanField(
        required=False, default=True, help_text="Send invitation email to participant"
    )

    def validate(self, data):
        """Cross-field validation"""
        role = data.get("role")
        email = data.get("email")

        # Validate required fields based on role
        if role in ["defence_counsel", "prosecution_counsel", "claimant_counsel"]:
            if not data.get("bar_number"):
                raise serializers.ValidationError(
                    {"bar_number": f"Bar number is required for {role}"}
                )

        if role in ["judge", "magistrate", "clerk"]:
            if not data.get("court_id"):
                raise serializers.ValidationError(
                    {"court_id": f"Court ID is required for {role}"}
                )

        # For new users, first_name and last_name are required
        if email:
            user = User.objects.filter(email=email).first()

            if not user:
                if not data.get("first_name") or not data.get("last_name"):
                    raise serializers.ValidationError(
                        "First name and last name are required for new users"
                    )

        return data


class AddParticipantsSerializer(serializers.Serializer):
    """Serializer for adding multiple participants to a hearing"""

    # IMPORTANT: Use many=True, NOT ListField
    participants = AddParticipantSerializer(many=True)

    send_bulk_invites = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Send invitation emails to all new participants",
    )

    def validate_participants(self, value):
        """Validate the participants list"""
        if not value:
            raise serializers.ValidationError("At least one participant is required")

        # Check for duplicate emails
        emails = [p.get("email") for p in value if p.get("email")]
        if len(emails) != len(set(emails)):
            duplicate_emails = [email for email in emails if emails.count(email) > 1]
            raise serializers.ValidationError(
                f"Duplicate email addresses found: {', '.join(set(duplicate_emails))}"
            )

        return value


class CreateHearingSerializer(serializers.Serializer):
    """Serializer for creating a new hearing"""

    case_id = serializers.UUIDField(required=True)
    courtroom_id = serializers.UUIDField(required=True)
    scheduled_at = serializers.DateTimeField(required=True)
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    hearing_type = serializers.CharField(required=False)
    participants = AddParticipantSerializer(many=True, required=False, default=[])

    def validate_case_id(self, value):
        """Validate that the case exists"""
        if not Case.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Case with id {value} does not exist")
        return value

    def validate_courtroom_id(self, value):
        """Validate that the courtroom exists"""
        if not Courtroom.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f"Courtroom with id {value} does not exist"
            )
        return value

    def validate_scheduled_at(self, value):
        """Validate that scheduled_at is in the future"""
        if value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        return value

    def validate_participants(self, value):
        """Validate participants list for duplicates"""
        if not value:
            return value
        print(value, "VALUE")
        seen = set()
        duplicates = []
        for idx, participant in enumerate(value):
            key = (participant.get("user_id"), participant.get("role"))
            if key in seen:
                duplicates.append(
                    f"User {participant.get('user_id')} with role '{participant.get('role')}' appears multiple times"
                )
            seen.add(key)

        if duplicates:
            raise serializers.ValidationError(
                f"Duplicate participants found: {', '.join(duplicates)}"
            )

        return value

    def validate(self, data):
        """
        Cross-field validation
        Check if courtroom is available at the scheduled time
        """
        courtroom_id = data.get("courtroom_id")
        scheduled_at = data.get("scheduled_at")

        # Check courtroom availability
        conflicting_hearings = Hearing.objects.filter(
            courtroom_id=courtroom_id,
            scheduled_at__date=scheduled_at.date(),
            status__in=["scheduled", "in_progress"],
        ).exclude(status="cancelled")

        # Allow some buffer time between hearings (e.g., 30 minutes)
        time_buffer = timezone.timedelta(minutes=30)
        for hearing in conflicting_hearings:
            time_diff = abs(hearing.scheduled_at - scheduled_at)
            if time_diff < time_buffer:
                raise serializers.ValidationError(
                    f"Courtroom is not available at this time. "
                    f"Conflicts with hearing ID {hearing.id} scheduled at {hearing.scheduled_at}"
                )

        return data


class UpdateHearingParticipantSerializer(serializers.Serializer):
    """Serializer for updating hearing participants"""

    id = serializers.IntegerField(
        required=False, help_text="ID of existing participant (for updates)"
    )
    user_id = serializers.IntegerField(required=False, help_text="ID of the user")
    role = serializers.CharField(
        required=False, max_length=50, help_text="Role in hearing"
    )
    action = serializers.ChoiceField(
        choices=["add", "update", "remove"],
        required=False,
        default="add",
        help_text="Action to perform: add, update, or remove participant",
    )

    def validate_role(self, value):
        """Validate that the role is one of the allowed values"""
        if value:
            allowed_roles = [
                "judge",
                "plaintiff",
                "defendant",
                "lawyer",
                "witness",
                "clerk",
                "prosecutor",
            ]
            if value.lower() not in allowed_roles:
                raise serializers.ValidationError(
                    f"Role must be one of: {', '.join(allowed_roles)}"
                )
            return value.lower()
        return value

    def validate_user_id(self, value):
        """Validate that the user exists"""
        if value and not User.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"User with id {value} does not exist")
        return value

    def validate(self, data):
        """Cross-field validation for participant updates"""
        action = data.get("action", "add")

        if action == "remove":
            if not data.get("id"):
                raise serializers.ValidationError(
                    "Participant ID is required for remove action"
                )
        elif action == "update":
            if not data.get("id"):
                raise serializers.ValidationError(
                    "Participant ID is required for update action"
                )
            if not data.get("user_id") and not data.get("role"):
                raise serializers.ValidationError(
                    "At least one of user_id or role is required for update"
                )
        elif action == "add":
            if not data.get("user_id") or not data.get("role"):
                raise serializers.ValidationError(
                    "Both user_id and role are required for add action"
                )

        return data


class UpdateHearingSerializer(serializers.Serializer):
    """
    Serializer for updating an existing hearing

    Supports partial updates and participant management (add/update/remove)
    All fields are optional to allow partial updates (PATCH requests)
    """

    case_id = serializers.UUIDField(
        required=False, help_text="ID of the associated case"
    )
    courtroom_id = serializers.UUIDField(
        required=False,
        help_text="ID of the courtroom where the hearing will take place",
    )
    name = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    scheduled_at = serializers.DateTimeField(
        required=False,
        help_text="Scheduled date and time for the hearing (ISO 8601 format)",
    )
    hearing_type = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Type of hearing (e.g., 'preliminary', 'trial', 'sentencing')",
    )
    status = serializers.ChoiceField(
        choices=[
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("postponed", "Postponed"),
        ],
        required=False,
        help_text="Current status of the hearing",
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        style={"base_template": "textarea.html"},
        help_text="Additional notes about the hearing",
    )
    metadata = serializers.JSONField(
        required=False, help_text="Additional metadata as JSON"
    )
    participants = UpdateHearingParticipantSerializer(
        many=True,
        required=False,
        help_text="List of participant changes (add/update/remove)",
    )

    # Fields for status transitions
    completion_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Notes when completing a hearing",
    )
    cancellation_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Reason for cancellation",
    )
    postponement_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Reason for postponement",
    )
    new_scheduled_at = serializers.DateTimeField(
        required=False, write_only=True, help_text="New scheduled time when postponing"
    )

    def validate_case_id(self, value):
        """Validate that the case exists"""
        if value and not Case.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Case with id {value} does not exist")
        return value

    def validate_courtroom_id(self, value):
        """Validate that the courtroom exists"""
        if value and not Courtroom.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f"Courtroom with id {value} does not exist"
            )
        return value

    def validate_scheduled_at(self, value):
        """Validate that scheduled_at is in the future (if being updated)"""
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "Scheduled time must be in the future. Use status 'postponed' for rescheduling past hearings."
            )
        return value

    def validate_status(self, value):
        """Validate status transitions"""
        if (
            self.instance
            and self.instance.status == "completed"
            and value != "completed"
        ):
            raise serializers.ValidationError(
                "Cannot change status of a completed hearing"
            )
        if self.instance and self.instance.status == "cancelled":
            raise serializers.ValidationError(
                "Cannot change status of a cancelled hearing"
            )
        return value

    def validate_participants(self, value):
        """Validate participant operations"""
        if not value:
            return value

        # Check for duplicate operations on same participant
        seen_ids = set()
        seen_adds = set()
        duplicates = []

        for participant in value:
            action = participant.get("action", "add")
            participant_id = participant.get("id")

            if action == "remove" or action == "update":
                if participant_id in seen_ids:
                    duplicates.append(
                        f"Multiple operations on participant ID {participant_id}"
                    )
                seen_ids.add(participant_id)
            elif action == "add":
                key = (participant.get("user_id"), participant.get("role"))
                if key in seen_adds:
                    duplicates.append(
                        f"Multiple add operations for User {participant.get('user_id')} with role '{participant.get('role')}'"
                    )
                seen_adds.add(key)

        if duplicates:
            raise serializers.ValidationError(
                f"Duplicate participant operations: {', '.join(duplicates)}"
            )

        return value

    def validate(self, data):
        """
        Cross-field validation for hearing updates
        """
        instance = self.instance

        # Status transition validations
        status = data.get("status", instance.status if instance else None)

        if status == "completed":
            if instance and instance.status != "in_progress":
                raise serializers.ValidationError(
                    "Only hearings 'in_progress' can be marked as completed"
                )
            if not data.get("completion_notes") and not data.get("notes"):
                raise serializers.ValidationError(
                    "Completion notes are required when completing a hearing"
                )

        elif status == "cancelled":
            if instance and instance.status in ["completed", "cancelled"]:
                raise serializers.ValidationError(
                    f"Cannot cancel a hearing that is already {instance.status}"
                )

        elif status == "postponed":
            if not data.get("new_scheduled_at"):
                raise serializers.ValidationError(
                    "New scheduled time is required when postponing a hearing"
                )
            if data.get("new_scheduled_at") <= timezone.now():
                raise serializers.ValidationError(
                    "New scheduled time must be in the future"
                )

        # Courtroom availability check if changing time or courtroom
        if data.get("courtroom_id") or data.get("scheduled_at"):
            courtroom_id = data.get(
                "courtroom_id", instance.courtroom_id if instance else None
            )
            scheduled_at = data.get(
                "scheduled_at", instance.scheduled_at if instance else None
            )

            if courtroom_id and scheduled_at:
                # Check for conflicts excluding current instance
                conflicting_hearings = (
                    Hearing.objects.filter(
                        courtroom_id=courtroom_id,
                        scheduled_at__date=scheduled_at.date(),
                        status__in=["scheduled", "in_progress"],
                    )
                    .exclude(id=instance.id if instance else None)
                    .exclude(status="cancelled")
                )

                # Allow buffer time between hearings (e.g., 30 minutes)
                time_buffer = timezone.timedelta(minutes=30)
                for hearing in conflicting_hearings:
                    time_diff = abs(hearing.scheduled_at - scheduled_at)
                    if time_diff < time_buffer:
                        raise serializers.ValidationError(
                            f"Courtroom is not available at this time. "
                            f"Conflicts with hearing ID {hearing.id} scheduled at {hearing.scheduled_at}"
                        )

        # If postponing, update scheduled_at with new value
        if data.get("status") == "postponed" and data.get("new_scheduled_at"):
            data["scheduled_at"] = data.pop("new_scheduled_at")

        return data

    def to_representation(self, instance):
        """
        Transform validated data back to a representation
        """
        from .serializers import HearingSerializer

        return HearingSerializer(instance, context=self.context).data

    class Meta:
        ref_name = "UpdateHearing"
        fields = [
            "case_id",
            "courtroom_id",
            "scheduled_at",
            "hearing_type",
            "status",
            "notes",
            "metadata",
            "participants",
            "completion_notes",
            "cancellation_reason",
            "postponement_reason",
            "new_scheduled_at",
        ]
