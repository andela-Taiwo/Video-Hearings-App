import pytest
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.test")
django.setup()

from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, Mock, MagicMock
# import uuid

from video_hearings.models import Hearing, HearingParticipant
# from accounts.models import User

@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis connection for all tests"""
    with patch('redis.Redis') as mock_redis:
        # Create a mock Redis instance
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        # Mock common Redis methods
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis_instance.set.return_value = True
        mock_redis_instance.delete.return_value = 1
        mock_redis_instance.exists.return_value = 0
        
        yield mock_redis

@pytest.mark.django_db
class TestHearingAPI:
    """Test cases for Hearing API endpoints"""

    def setup_method(self):
        """Setup for each test method"""
        self.client = APIClient()
        self.hearings_url = reverse("hearing-list")

    def teardown_method(self):
        """Clean up after each test"""
        # Clear the database
        Hearing.objects.all().delete()

    def test_list_hearings(self, api_client, hearing_factory):
        """Test GET /api/v1/hearings/"""
        # Create some hearings
        hearing_factory.create_batch(3)

        response = api_client.get(self.hearings_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("count") == 3

    def test_create_hearing_success(
        self, api_client, case_factory, courtroom_factory, court_factory
    ):
        """Test POST /api/v1/hearings/ - successful creation"""
        case = case_factory()
        courtroom = courtroom_factory()
        court = court_factory()
        scheduled_at = (timezone.now() + timedelta(days=1)).isoformat()

        data = {
            "case_id": str(case.id),
            "courtroom_id": str(courtroom.id),
            "scheduled_at": scheduled_at,
            "name": "Test Hearing",
            "description": "Test Description",
            "hearing_type": "trial",
            "participants": [
                {
                    "email": "judge@court.gov",
                    "role": "judge",
                    "first_name": "Judge",
                    "last_name": "Smith",
                    "court_id": str(court.id),
                },
                {
                    "email": "defendant@example.com",
                    "role": "defendant",
                    "first_name": "John",
                    "last_name": "Doe",
                },
            ],
        }

        response = api_client.post(self.hearings_url, data, format="json")
        print(response.data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Test Hearing"
        assert len(response.data["participants"]) == 2

    def test_create_hearing_missing_participants(
        self, api_client, case_factory, courtroom_factory
    ):
        """Test POST /api/v1/hearings/ - fails without participants"""
        case = case_factory()
        courtroom = courtroom_factory()

        data = {
            "case_id": str(case.id),
            "courtroom_id": str(courtroom.id),
            "scheduled_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "participants": [],
            "name": "hearing-001",
        }

        response = api_client.post(self.hearings_url, data, format="json")
        print(response.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "participant" in response.data.get("error")

    def test_retrieve_hearing(self, api_client, hearing_factory):
        """Test GET /api/v1/hearings/{id}/"""
        hearing = hearing_factory()
        url = reverse("hearing-detail", kwargs={"pk": hearing.id})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(hearing.id)

    def test_update_hearing(self, api_client, hearing_factory):
        """Test PUT /api/v1/hearings/{id}/"""
        hearing = hearing_factory(name="Old Name")
        url = reverse("hearing-detail", kwargs={"pk": hearing.id})
        print(hearing.case.id, "HEARINNGNG", hearing.courtroom.id)
        data = {
            "name": "Updated Name",
            "description": "Updated Description",
            "case_id": str(hearing.case.id),
            "courtroom_id": str(hearing.courtroom.id),
            "scheduled_at": hearing.scheduled_at.isoformat(),
        }

        response = api_client.put(url, data, format="json")
        print(response.data)
        assert response.status_code == status.HTTP_200_OK

        assert response.data["name"] == "Updated Name"

    def test_partial_update_hearing(self, api_client, hearing_factory):
        """Test PATCH /api/v1/hearings/{id}/"""
        hearing = hearing_factory(name="Old Name")
        url = reverse("hearing-detail", kwargs={"pk": hearing.id})

        data = {"name": "Patched Name"}

        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Patched Name"

    def test_delete_hearing(self, api_client, hearing_factory):
        """Test DELETE /api/v1/hearings/{id}/"""
        hearing = hearing_factory()
        url = reverse("hearing-detail", kwargs={"pk": hearing.id})

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Should be soft deleted (status changed to cancelled)
        hearing.refresh_from_db()
        assert hearing.status == "cancelled"

    def test_add_participants(self, api_client, hearing_factory):
        """Test POST /api/v1/hearings/{id}/add_participants/"""
        hearing = hearing_factory()
        url = reverse("hearing-add-participants", kwargs={"pk": hearing.id})

        data = {
            "participants": [
                {
                    "email": "new.participant@example.com",
                    "role": "witness",
                    "first_name": "New",
                    "last_name": "Witness",
                }
            ]
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert hearing.participants.count() == 1

    def test_remove_participants(
        self, api_client, hearing_with_participants, participant_factory
    ):
        """Test DELETE /api/v1/hearings/{id}/participants/"""
        hearing = hearing_with_participants
        participant = hearing.participants.first()
        url = reverse("hearing-remove-participants", kwargs={"pk": hearing.id})

        data = {"participant_ids": [str(participant.id)]}

        response = api_client.delete(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["removed_count"] == 1
        assert hearing.participants.count() == 2  # Started with 3, removed 1

    def test_reschedule_hearing(self, api_client, hearing_factory):
        """Test POST /api/v1/hearings/{id}/reschedule/"""
        hearing = hearing_factory()
        url = reverse("hearing-reschedule", kwargs={"pk": hearing.id})
        new_time = (timezone.now() + timedelta(days=14)).isoformat()

        data = {"scheduled_at": new_time, "reason": "Judge unavailable"}

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        hearing.refresh_from_db()
        assert hearing.scheduled_at.isoformat() == new_time

    def test_cancel_hearing(self, api_client, hearing_factory):
        """Test POST /api/v1/hearings/{id}/cancel/"""
        hearing = hearing_factory()
        url = reverse("hearing-cancel", kwargs={"pk": hearing.id})

        data = {"reason": "Case settled"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        hearing.refresh_from_db()
        assert hearing.status == "cancelled"

    def test_upcoming_hearings(self, api_client, hearing_factory):
        """Test GET /api/v1/hearings/upcoming/"""
        now = timezone.now()

        # Create upcoming hearings
        hearing_factory(
            scheduled_at=now + timedelta(days=1), status=Hearing.Status.SCHEDULED
        )
        hearing_factory(
            scheduled_at=now + timedelta(days=3), status=Hearing.Status.SCHEDULED
        )
        hearing_factory(
            scheduled_at=now + timedelta(days=10), status=Hearing.Status.SCHEDULED
        )  # Outside 7 days

        url = reverse("hearing-upcoming")
        response = api_client.get(url, {"days": 7})

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("count") == 2

    def test_hearings_by_date_range(self, api_client, hearing_factory):
        """Test GET /api/v1/hearings/by_date_range/"""
        now = timezone.now()

        # Create hearings
        hearing_factory(scheduled_at=now + timedelta(days=5))
        hearing_factory(scheduled_at=now + timedelta(days=15))
        hearing_factory(scheduled_at=now + timedelta(days=25))

        start_date = (now + timedelta(days=1)).date().isoformat()
        end_date = (now + timedelta(days=10)).date().isoformat()

        url = reverse("hearing-by-date-range")
        response = api_client.get(url, {"start": start_date, "end": end_date})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_hearings_by_date_range_missing_params(self, api_client):
        """Test date range endpoint with missing parameters"""
        url = reverse("hearing-by-date-range")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "start and end dates are required" in response.data["error"]
