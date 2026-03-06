import pytest
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.test")
django.setup()

from django.db import models
from django.utils import timezone

from datetime import timedelta
import uuid

from video_hearings.models import Hearing, HearingParticipant, HearingDocument


@pytest.mark.django_db
class TestHearingModel:
    """Test cases for Hearing model"""

    def test_create_hearing(self, hearing_factory):
        """Test creating a hearing with basic fields"""
        hearing = hearing_factory()

        assert hearing.id is not None
        assert isinstance(hearing.id, uuid.UUID)
        assert hearing.status == Hearing.Status.SCHEDULED
        assert hearing.hearing_type in dict(Hearing.HearingType.choices)
        assert hearing.scheduled_at is not None
        assert hearing.created_at is not None
        assert hearing.updated_at is not None

    def test_hearing_str_method(self, hearing_factory, case_factory):
        """Test the string representation of Hearing"""
        case = case_factory(case_number="ABC123")
        hearing = hearing_factory(case=case, hearing_type=Hearing.HearingType.TRIAL)

        expected_str = f"Hearing {hearing.id} - ABC123 - trial"
        assert str(hearing) == expected_str

    def test_hearing_default_status(
        self, court_factory, case_factory, courtroom_factory, user_factory
    ):
        """Test that default status is SCHEDULED"""
        judge = user_factory(email="judge@court.gov")
        court = court_factory()
        courtroom = courtroom_factory(court=court)
        case = case_factory(judge=judge)

        hearing = Hearing.objects.create(
            case=case,
            courtroom=courtroom,
            scheduled_at=timezone.now() + timedelta(days=7),
            name="Test Hearing",
            hearing_type=Hearing.HearingType.TRIAL,
            # status is not specified
        )

        # Refresh from database to ensure we have the saved value
        hearing.refresh_from_db()

        # Assert that status is SCHEDULED (the default)
        assert hearing.status == Hearing.Status.SCHEDULED

    def test_hearing_status_choices(self, hearing_factory):
        """Test all possible status choices"""
        for status in Hearing.Status.values:
            hearing = hearing_factory(status=status)
            hearing.full_clean()  # Should not raise
            assert hearing.status == status

    def test_hearing_type_choices(self, hearing_factory):
        """Test various hearing type choices"""
        test_types = [
            Hearing.HearingType.TRIAL,
            Hearing.HearingType.ARRAIGNMENT,
            Hearing.HearingType.CIVIL_TRIAL,
            Hearing.HearingType.FDR,
            Hearing.HearingType.COA_CIVIL,
        ]

        for hearing_type in test_types:
            hearing = hearing_factory(hearing_type=hearing_type)
            hearing.full_clean()
            assert hearing.hearing_type == hearing_type

    def test_hearing_ordering(self, hearing_factory):
        """Test that hearings are ordered by scheduled_at descending"""
        now = timezone.now()
        hearing1 = hearing_factory(scheduled_at=now - timedelta(days=2))
        hearing2 = hearing_factory(scheduled_at=now)
        hearing3 = hearing_factory(scheduled_at=now - timedelta(days=1))

        hearings = list(Hearing.objects.all())
        assert hearings[0] == hearing2  # Most recent first
        assert hearings[1] == hearing3
        assert hearings[2] == hearing1

    def test_active_manager(self, hearing_factory):
        """Test ActiveHearingManager returns only active hearings"""
        # Create hearings with different statuses
        active_statuses = ["scheduled", "in_progress", "postponed", "recessed"]
        inactive_statuses = ["completed", "cancelled"]

        for status in active_statuses:
            hearing_factory(status=status)

        for status in inactive_statuses:
            hearing_factory(status=status)

        active_hearings = Hearing.active.all()
        assert active_hearings.count() == len(active_statuses)

        for hearing in active_hearings:
            assert hearing.status in active_statuses

    def test_courtroom_relationship(self, hearing_factory, courtroom_factory):
        """Test relationship with Courtroom model"""
        courtroom = courtroom_factory(name="Courtroom 1")
        hearing = hearing_factory(courtroom=courtroom)

        assert hearing.courtroom == courtroom
        assert hearing in courtroom.hearing_set.all()

    def test_case_relationship(self, hearing_factory, case_factory):
        """Test relationship with Case model"""
        case = case_factory()
        hearing = hearing_factory(case=case)

        assert hearing.case == case
        assert hearing in case.hearings.all()

    def test_optional_fields_blank(self, hearing_factory):
        """Test that optional fields can be blank"""
        hearing = hearing_factory(
            name="",
            description=None,
            hearing_type=None,
            started_at=None,
            ended_at=None,
            session_id="",
            session_url="",
            recording_url="",
        )

        assert hearing.name == ""
        assert hearing.description is None
        assert hearing.hearing_type is None
        assert hearing.started_at is None
        hearing.full_clean()  # Should not raise

    def test_timestamps_auto_set(self, hearing_factory):
        """Test that created_at and updated_at are auto-set"""
        hearing = hearing_factory()
        assert hearing.created_at is not None
        assert hearing.updated_at is not None

        original_updated = hearing.updated_at
        hearing.name = "Updated Name"
        hearing.save()

        assert hearing.updated_at > original_updated


@pytest.mark.django_db
class TestHearingParticipantModel:
    """Test cases for HearingParticipant model"""

    def test_create_participant(self, participant_factory):
        """Test creating a hearing participant"""
        participant = participant_factory()

        assert participant.id is not None
        assert isinstance(participant.id, uuid.UUID)
        assert (
            participant.connection_status == HearingParticipant.ConnectionStatus.WAITING
        )
        assert participant.join_token is not None
        assert participant.created_at is not None

    def test_participant_str_method(
        self, participant_factory, user_factory, hearing_factory
    ):
        """Test string representation of HearingParticipant"""
        user = user_factory(email="test@example.com")
        hearing = hearing_factory()
        participant = participant_factory(
            user=user, hearing=hearing, role=HearingParticipant.PartyRole.JUDGE
        )

        expected_str = f"test@example.com - judge - {hearing.id}"
        assert str(participant) == expected_str

    def test_connection_status_choices(self, participant_factory):
        """Test all connection status choices"""
        for status in HearingParticipant.ConnectionStatus.values:
            participant = participant_factory(connection_status=status)
            participant.full_clean()
            assert participant.connection_status == status

    def test_party_role_choices(self, participant_factory):
        """Test various party role choices"""
        test_roles = [
            HearingParticipant.PartyRole.JUDGE,
            HearingParticipant.PartyRole.DEFENDANT,
            HearingParticipant.PartyRole.CLAIMANT_COUNSEL,
            HearingParticipant.PartyRole.WITNESS,
            HearingParticipant.PartyRole.SOLICITOR,
        ]

        for role in test_roles:
            participant = participant_factory(role=role)
            participant.full_clean()
            assert participant.role == role

    def test_join_token_uniqueness(self, participant_factory):
        """Test that join_token is unique"""
        participant1 = participant_factory()
        participant2 = participant_factory()

        assert participant1.join_token != participant2.join_token

    def test_optional_timestamps(self, participant_factory):
        """Test that joined_at and left_at can be null"""
        participant = participant_factory(joined_at=None, left_at=None)

        assert participant.joined_at is None
        assert participant.left_at is None

        # Update with timestamps
        now = timezone.now()
        participant.joined_at = now
        participant.left_at = now + timedelta(hours=1)
        participant.save()

        assert participant.joined_at == now
        assert participant.left_at == now + timedelta(hours=1)


@pytest.mark.django_db
class TestHearingDocumentModel:
    """Test cases for HearingDocument model"""

    def test_create_document(self, document_factory):
        """Test creating a hearing document"""
        document = document_factory()

        assert document.id is not None
        assert isinstance(document.id, uuid.UUID)
        assert document.doc_type in dict(HearingDocument.DocType.choices)
        assert document.uploaded_at is not None
        assert document.is_sealed is False
        assert document.admitted is False

    def test_document_str_method(self, document_factory, hearing_factory):
        """Test string representation of HearingDocument"""
        hearing = hearing_factory()
        document = document_factory(
            hearing=hearing,
            doc_type=HearingDocument.DocType.EVIDENCE,
            file_name="evidence.pdf",
        )

        expected_str = f"evidence - {hearing.id} - evidence.pdf"
        assert str(document) == expected_str

    def test_save_sets_file_name(self, document_factory, mock_file):
        """Test that save method sets file_name from file if not provided"""
        document = document_factory(
            file=mock_file,
            file_name="",  # Explicitly empty
        )

        assert document.file_name == mock_file.name

    def test_doc_type_choices(self, document_factory):
        """Test all document type choices"""
        for doc_type in HearingDocument.DocType.values:
            document = document_factory(doc_type=doc_type)
            document.full_clean()
            assert document.doc_type == doc_type

    def test_file_upload_path(self, document_factory, mock_file):
        """Test that file is uploaded to correct path"""
        document = document_factory(file=mock_file)

        # Check that upload_to pattern is applied
        assert "hearing_docs" in document.file.name
        assert str(timezone.now().year) in document.file.name
        assert str(timezone.now().month) in document.file.name


@pytest.mark.django_db
class TestModelRelationships:
    """Test relationships between models"""

    def test_hearing_participants_relationship(
        self, hearing_factory, participant_factory
    ):
        """Test one-to-many relationship from Hearing to HearingParticipant"""
        hearing = hearing_factory()
        participants = [
            participant_factory(
                hearing=hearing, role=HearingParticipant.PartyRole.JUDGE
            ),
            participant_factory(
                hearing=hearing, role=HearingParticipant.PartyRole.DEFENDANT
            ),
            participant_factory(
                hearing=hearing, role=HearingParticipant.PartyRole.CLAIMANT_COUNSEL
            ),
        ]

        assert hearing.participants.count() == 3
        assert set(hearing.participants.all()) == set(participants)

    def test_hearing_documents_relationship(self, hearing_factory, document_factory):
        """Test one-to-many relationship from Hearing to HearingDocument"""
        hearing = hearing_factory()
        documents = [
            document_factory(hearing=hearing, doc_type=HearingDocument.DocType.MOTION),
            document_factory(
                hearing=hearing, doc_type=HearingDocument.DocType.EVIDENCE
            ),
            document_factory(hearing=hearing, doc_type=HearingDocument.DocType.ORDER),
        ]

        assert hearing.documents.count() == 3
        assert set(hearing.documents.all()) == set(documents)

    def test_cascade_delete_participants(self, hearing_factory, participant_factory):
        """Test that deleting a hearing deletes its participants"""
        hearing = hearing_factory()
        participant = participant_factory(hearing=hearing)

        participant_id = participant.id
        hearing.delete()

        assert not HearingParticipant.objects.filter(id=participant_id).exists()

    def test_protect_delete_for_documents(self, hearing_factory, document_factory):
        """Test that documents are protected from deletion when hearing exists"""
        hearing = hearing_factory()
        document = document_factory(hearing=hearing)

        # Should not be able to delete hearing while documents exist
        with pytest.raises(models.ProtectedError):
            hearing.delete()
