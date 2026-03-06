import pytest
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from tests.hearings.factories import (
    UserFactory,
    UserProfileFactory,
    CourtFactory,
    CourtroomFactory,
    CaseFactory,
    HearingFactory,
    HearingParticipantFactory,
    HearingDocumentFactory,
)


@pytest.fixture
def api_client():
    """Return an API client"""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user():
    """Return a regular user"""
    return UserFactory()


@pytest.fixture
def admin_user():
    """Return an admin user"""
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def user_profile(user):
    """Return a user profile"""
    return UserProfileFactory(user=user)


@pytest.fixture
def court():
    """Return a court"""
    return CourtFactory()


@pytest.fixture
def courtroom(court):
    """Return a courtroom"""
    return CourtroomFactory(court=court)


@pytest.fixture
def case():
    """Return a case"""
    return CaseFactory()


@pytest.fixture
def hearing(case, courtroom):
    """Return a hearing"""
    return HearingFactory(case=case, courtroom=courtroom)


@pytest.fixture
def hearing_with_participants(hearing):
    """Return a hearing with participants"""
    HearingParticipantFactory.create_batch(3, hearing=hearing)
    return hearing


@pytest.fixture
def hearing_participant(hearing, user):
    """Return a hearing participant"""
    return HearingParticipantFactory(hearing=hearing, user=user)


@pytest.fixture
def hearing_document(hearing, user):
    """Return a hearing document"""
    return HearingDocumentFactory(hearing=hearing, uploaded_by=user)


@pytest.fixture
def mock_file():
    """Return a mock file for testing"""
    return SimpleUploadedFile(
        "test_file.pdf", b"file_content", content_type="application/pdf"
    )


# Factory fixtures for use in tests
@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def user_profile_factory():
    return UserProfileFactory


@pytest.fixture
def court_factory():
    return CourtFactory


@pytest.fixture
def courtroom_factory():
    return CourtroomFactory


@pytest.fixture
def case_factory():
    return CaseFactory


@pytest.fixture
def hearing_factory():
    return HearingFactory


@pytest.fixture
def participant_factory():
    return HearingParticipantFactory


@pytest.fixture
def document_factory():
    return HearingDocumentFactory
