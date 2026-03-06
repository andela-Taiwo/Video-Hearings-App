import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta
import uuid

from video_hearings.models import Hearing, HearingParticipant, HearingDocument
from cases.models import Case
from courts.models import Courtroom, Court
from accounts.models import User, UserProfile


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True
    is_verified = True
    is_email_verified = True
    is_admin_approved = True


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)
    role = UserProfile.Role.PUBLIC
    phone_number = factory.Faker("phone_number")


class CourtFactory(DjangoModelFactory):
    class Meta:
        model = Court

    name = factory.Sequence(lambda n: f"Court {n}")

    address = factory.Faker("address")
    jurisdiction = factory.Faker("word")
    # phone = factory.Faker('phone_number')
    # email = factory.Faker('email')


class JudgeFactory(UserFactory):
    """Factory for creating judge users"""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"judge{n}@court.gov")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class CaseFactory(DjangoModelFactory):
    class Meta:
        model = Case

    case_number = factory.Sequence(lambda n: f"CASE{n:06d}")
    title = factory.Faker("sentence")
    description = factory.Faker("paragraph")
    # Add a judge - required field
    judge = factory.SubFactory(JudgeFactory)
    # Add other required fields based on your Case model
    status = "active"  # or whatever default status your Case model uses
    filed_date = factory.LazyFunction(timezone.now)


class CourtroomFactory(DjangoModelFactory):
    class Meta:
        model = Courtroom

    court = factory.SubFactory(CourtFactory)
    name = factory.Sequence(lambda n: f"Courtroom {n}")
    # room_number = factory.Sequence(lambda n: str(n))
    # has_video_conferencing = True
    capacity = factory.Faker("random_int", min=10, max=100)


class HearingFactory(DjangoModelFactory):
    class Meta:
        model = Hearing

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("sentence")
    description = factory.Faker("paragraph")
    case = factory.SubFactory(CaseFactory)
    courtroom = factory.SubFactory(CourtroomFactory)
    hearing_type = factory.Iterator(
        [choice[0] for choice in Hearing.HearingType.choices]
    )
    status = Hearing.Status.SCHEDULED
    scheduled_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    started_at = None
    ended_at = None
    session_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    session_url = factory.Faker("url")
    recording_url = factory.Faker("url")
    is_public = False


class HearingParticipantFactory(DjangoModelFactory):
    class Meta:
        model = HearingParticipant

    id = factory.LazyFunction(uuid.uuid4)
    hearing = factory.SubFactory(HearingFactory)
    user = factory.SubFactory(UserFactory)
    role = factory.Iterator(
        [choice[0] for choice in HearingParticipant.PartyRole.choices]
    )
    join_token = factory.LazyFunction(uuid.uuid4)
    joined_at = None
    left_at = None
    connection_status = HearingParticipant.ConnectionStatus.WAITING


class HearingDocumentFactory(DjangoModelFactory):
    class Meta:
        model = HearingDocument

    id = factory.LazyFunction(uuid.uuid4)
    hearing = factory.SubFactory(HearingFactory)
    uploaded_by = factory.SubFactory(UserFactory)
    doc_type = factory.Iterator(
        [choice[0] for choice in HearingDocument.DocType.choices]
    )
    file = factory.django.FileField(filename="test_document.pdf")
    file_name = factory.Faker("file_name", extension="pdf")
    file_size = factory.Faker("random_int", min=1024, max=10485760)
    content_type = "application/pdf"
    is_sealed = False
    admitted = False
