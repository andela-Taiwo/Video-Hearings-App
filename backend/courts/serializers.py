from rest_framework import serializers
from .models import Court, Courtroom


class CourtroomSerializer(serializers.ModelSerializer):
    court_name = serializers.ReadOnlyField(source="court.name")

    class Meta:
        model = Courtroom
        fields = [
            "id",
            "court",
            "court_name",
            "name",
            "capacity",
            "video_platform_config",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_video_platform_config(self, value):
        """Validate video platform configuration"""
        required_fields = ["provider", "api_key", "api_secret"]
        if not isinstance(value, dict):
            raise serializers.ValidationError("Must be a valid JSON object")

        provider = value.get("provider")
        if provider and provider not in ["zoom", "teams", "webex", "custom"]:
            raise serializers.ValidationError("Invalid video provider")

        return value


class CourtSerializer(serializers.ModelSerializer):
    courtrooms = CourtroomSerializer(many=True, read_only=True)
    courtroom_count = serializers.IntegerField(
        source="courtrooms.count", read_only=True
    )

    class Meta:
        model = Court
        fields = [
            "id",
            "name",
            "jurisdiction",
            "address",
            "contact_info",
            "courtrooms",
            "courtroom_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_contact_info(self, value):
        """Validate contact information structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Contact info must be a valid JSON object"
            )

        if (
            "phone" in value
            and not value["phone"].replace("+", "").replace("-", "").isdigit()
        ):
            raise serializers.ValidationError("Invalid phone number format")

        if "email" in value and "@" not in value["email"]:
            raise serializers.ValidationError("Invalid email format")

        return value


class CourtroomCapacityUpdateSerializer(serializers.Serializer):
    capacity = serializers.IntegerField(min_value=1, max_value=1000)


class CourtBulkCreateSerializer(serializers.Serializer):
    courts = CourtSerializer(many=True)
