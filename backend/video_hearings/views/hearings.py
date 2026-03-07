from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination, CursorPagination
from collections import OrderedDict
from .base import BaseHearingViewSet
from ..serializers import (
    AddParticipantsSerializer,
    HearingSerializer,
    CreateHearingSerializer,
    UpdateHearingSerializer,
    HearingParticipantSerializer,
    CreateHearingParticipantSerializer,
    DeleteParticipantsSerializer,
)
from ..services.hearing_service import HearingService
from ..filters import HearingFilter
from ..models import Hearing


class HearingPagination(PageNumberPagination):
    """Custom pagination for hearings"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        """Customize paginated response with additional metadata"""
        return Response(
            OrderedDict(
                [
                    ("page", self.page.number),
                    ("total_pages", self.page.paginator.num_pages),
                    ("page_size", self.page.paginator.per_page),
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )


class HearingViewSet(BaseHearingViewSet):
    """
    ViewSet for managing hearings
    """

    queryset = Hearing.objects.all()
    serializer_class = HearingSerializer
    filterset_class = HearingFilter
    service_class = HearingService
    permission_classes = []
    search_fields = ["name"]
    pagination_class = HearingPagination

    # serializer to use for each action
    serializer_classes = {
        "create": CreateHearingSerializer,
        "update": UpdateHearingSerializer,
        "partial_update": UpdateHearingSerializer,
        "list": HearingSerializer,
        "retrieve": HearingSerializer,
        "add_participants": AddParticipantsSerializer,
        "remove_participants": DeleteParticipantsSerializer,
    }

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        return self.serializer_classes.get(self.action, super().get_serializer_class())

    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related"""
        queryset = (
            super()
            .get_queryset()
            .select_related("case", "courtroom")
            .prefetch_related("participants__user", "documents")
        )

        # Add permission filtering
        # [TODO] Implement Permisssions

        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        """
        Create a hearing with participants

        POST /api/hearings/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            hearing = self.service.create_hearing(**serializer.validated_data)
            response_serializer = HearingSerializer(
                hearing, context={"request": request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return self.handle_service_error(e)

    def list(self, request, *args, **kwargs):
        """
        List hearings with pagination, filtering, and searching

        GET /api/hearings/?page=1&page_size=20&search=term&case=123
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Apply pagination
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Update a hearing

        PUT /api/hearings/{id}/
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            hearing = self.service.update_hearing(
                instance.id, **serializer.validated_data
            )
            response_serializer = HearingSerializer(
                hearing, context={"request": request}
            )
            return Response(response_serializer.data)
        except Exception as e:
            return self.handle_service_error(e)

    def retrieve(self, request, *args, **kwargs):
        hearing = self.service.get_hearing(kwargs["pk"])
        if not hearing:
            return Response(
                {"error": "Hearing not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(hearing)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete a hearing

        DELETE /api/hearings/{id}/
        """
        instance = self.get_object()

        try:
            self.service.delete_hearing(instance.id)
            return Response(
                {"message": "Hearing deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return self.handle_service_error(e)

    @action(detail=True, methods=["post"])
    def add_participants(self, request, pk=None):
        """
        Add participants to an existing hearing

        POST /api/hearings/{id}/add_participants/
        """
        hearing = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            participants = self.service.add_participants(
                hearing, serializer.validated_data.get("participants", [])
            )
            response_serializer = HearingSerializer(
                participants,
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return self.handle_service_error(e)

    @action(detail=True, methods=["delete"], url_path="participants")
    def remove_participants(self, request, pk=None):
        """
        Remove one or more participants from a hearing.

        DELETE /api/hearings/{hearing_id}/participants/

        Request body (JSON):
        {
            "participant_ids": [1, 2, 3],                    # Delete by participant IDs
            "participant_emails": ["email@example.com"],      # Delete by email
            "roles": ["defendant", "witness"],                # Delete by role
            "user_ids": [10, 11]                               # Delete by user IDs
        }

        You can combine multiple criteria. Returns summary of deleted participants.
        """
        hearing = self.get_object()

        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        try:
            result = self.service.remove_participants(
                hearing_id=hearing.id,
                participant_ids=validated_data.get("participant_ids"),
                participant_emails=validated_data.get("participant_emails"),
                roles=validated_data.get("roles"),
                user_ids=validated_data.get("user_ids"),
            )

            if result["removed_count"] > 0:
                return Response(
                    {
                        "message": result["message"],
                        "removed_count": result["removed_count"],
                        "removed_participants": result.get("removed_participants", []),
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "message": "No matching participants found to delete",
                        "removed_count": 0,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:
            return self.handle_service_error(e)

    @action(detail=True, methods=["post"])
    def reschedule(self, request, pk=None):
        """
        Reschedule a hearing

        POST /api/hearings/{id}/reschedule/
        {
            "scheduled_at": "2024-04-01T10:00:00Z",
            "reason": "Judge unavailable"
        }
        """
        hearing = self.get_object()
        new_time = request.data.get("scheduled_at")
        reason = request.data.get("reason", "")

        if not new_time:
            return Response(
                {"error": "scheduled_at is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            hearing = self.service.reschedule_hearing(hearing.id, new_time, reason)
            response_serializer = HearingSerializer(hearing)
            return Response(response_serializer.data)
        except Exception as e:
            return self.handle_service_error(e)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancel a hearing

        POST /api/hearings/{id}/cancel/
        {
            "reason": "Case settled"
        }
        """
        hearing = self.get_object()
        reason = request.data.get("reason", "")

        try:
            hearing = self.service.cancel_hearing(hearing.id, reason)
            response_serializer = HearingSerializer(hearing)
            return Response(response_serializer.data)
        except Exception as e:
            return self.handle_service_error(e)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """
        Get upcoming hearings

        GET /api/hearings/upcoming/?days=7
        """
        days = int(request.query_params.get("days", 7))

        try:
            hearings = self.service.get_upcoming_hearings(days)
            page = self.paginate_queryset(hearings)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(hearings, many=True)
            return Response(serializer.data)
        except Exception as e:
            return self.handle_service_error(e)

    @action(detail=False, methods=["get"])
    def by_date_range(self, request):
        """
        Get hearings within a date range

        GET /api/hearings/by_date_range/?start=2024-03-01&end=2024-03-31
        """
        start_date = request.query_params.get("start")
        end_date = request.query_params.get("end")

        if not start_date or not end_date:
            return Response(
                {"error": "start and end dates are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            hearings = self.service.get_hearings_by_date_range(start_date, end_date)
            serializer = self.get_serializer(hearings, many=True)
            return Response(serializer.data)
        except Exception as e:
            return self.handle_service_error(e)
