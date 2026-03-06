from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Case, CaseParty
from courts.serializers import CourtSerializer
from django.db.models import Count

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "first_name", "last_name"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class CasePartySerializer(serializers.ModelSerializer):
    user_details = UserBasicSerializer(source="user", read_only=True)
    user_email = serializers.ReadOnlyField(source="user.email")
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = CaseParty
        fields = [
            "id",
            "case",
            "user",
            "user_details",
            "user_email",
            "user_name",
            "party_role",
            "added_at",
        ]
        read_only_fields = ["id", "added_at"]

    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def validate(self, data):
        """Validate that the user isn't already added with same role"""
        case = data.get("case")
        user = data.get("user")
        party_role = data.get("party_role")

        if case and user and party_role:
            if CaseParty.objects.filter(
                case=case, user=user, party_role=party_role
            ).exists():
                raise serializers.ValidationError(
                    f"User {user.email} is already a {party_role} in this case"
                )
        return data


class CaseListSerializer(serializers.ModelSerializer):
    judge_name = serializers.SerializerMethodField()
    party_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "case_number",
            "title",
            "case_type",
            "status",
            "status_display",
            "judge",
            "judge_name",
            "party_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_judge_name(self, obj):
        return obj.judge.get_full_name()


class CaseDetailSerializer(serializers.ModelSerializer):
    judge_details = UserBasicSerializer(source="judge", read_only=True)
    parties = CasePartySerializer(source="caseparty_set", many=True, read_only=True)
    parties_by_role = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "case_number",
            "title",
            "case_type",
            "status",
            "status_display",
            "judge",
            "judge_details",
            "parties",
            "parties_by_role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_parties_by_role(self, obj):
        """Group parties by role"""
        parties = obj.caseparty_set.all().select_related("user")
        result = {}
        for party in parties:
            role = party.party_role
            if role not in result:
                result[role] = []
            result[role].append(
                {
                    "id": party.user.id,
                    "name": party.user.get_full_name(),
                    "email": party.user.email,
                    "added_at": party.added_at,
                }
            )
        return result


class CaseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["case_number", "title", "case_type", "status", "judge"]

    def validate_case_number(self, value):
        """Validate case number format"""
        if not value.strip():
            raise serializers.ValidationError("Case number cannot be empty")

        # Check if case number already exists (excluding current instance)
        queryset = Case.objects.filter(case_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Case with this number already exists")

        return value

    def validate(self, data):
        """Additional validation"""
        if data.get("status") == Case.Status.CLOSED and not self.instance:
            # Additional checks for closing a case
            pass
        return data

    def to_representation(self, instance):
        """Remove null fields from the response"""
        data = super().to_representation(instance)

        # Remove fields with None values
        return {key: value for key, value in data.items() if value is not None}


class CaseStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Case.Status.choices)
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        case = self.context.get("case")
        if case:
            # Define allowed transitions
            allowed_transitions = {
                Case.Status.OPEN: [Case.Status.CLOSED, Case.Status.STAYED],
                Case.Status.CLOSED: [Case.Status.APPEALED],
                Case.Status.APPEALED: [Case.Status.CLOSED],
                Case.Status.STAYED: [Case.Status.OPEN, Case.Status.CLOSED],
            }

            if value not in allowed_transitions.get(case.status, []):
                raise serializers.ValidationError(
                    f"Cannot transition from {case.status} to {value}"
                )
        return value


class CasePartyAddSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    party_role = serializers.ChoiceField(choices=CaseParty.PartyRole.choices)

    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value

    def validate(self, data):
        case = self.context.get("case")
        user_id = data.get("user_id")
        party_role = data.get("party_role")

        if case and user_id and party_role:
            if CaseParty.objects.filter(
                case=case, user_id=user_id, party_role=party_role
            ).exists():
                raise serializers.ValidationError(
                    f"User is already a {party_role} in this case"
                )
        return data
