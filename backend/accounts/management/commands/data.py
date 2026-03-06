# seed_data.py
import random
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import signals

from courts.models import Court, Courtroom
from cases.models import Case, CaseParty
from video_hearings.models import Hearing, HearingParticipant, HearingDocument

User = get_user_model()


class DataSeeder:
    """Seed database with realistic test data for the court management system"""

    def __init__(self):
        self.courts = []
        self.courtrooms = []
        self.users = {}
        self.cases = []
        self.hearings = []

        # UK Court names and jurisdictions
        self.court_data = [
            {
                "name": "Royal Courts of Justice",
                "jurisdiction": "High Court",
                "city": "London",
            },
            {
                "name": "Central Criminal Court",
                "jurisdiction": "Crown Court",
                "city": "London",
            },
            {
                "name": "Manchester Crown Court",
                "jurisdiction": "Crown Court",
                "city": "Manchester",
            },
            {
                "name": "Birmingham Civil Justice Centre",
                "jurisdiction": "County Court",
                "city": "Birmingham",
            },
            {
                "name": "Leeds Combined Court Centre",
                "jurisdiction": "Crown Court",
                "city": "Leeds",
            },
            {
                "name": "Cardiff Civil Justice Centre",
                "jurisdiction": "County Court",
                "city": "Cardiff",
            },
            {
                "name": "Glasgow Sheriff Court",
                "jurisdiction": "Sheriff Court",
                "city": "Glasgow",
            },
            {
                "name": "Belfast Crown Court",
                "jurisdiction": "Crown Court",
                "city": "Belfast",
            },
        ]

        # Common UK surnames for realistic names
        self.surnames = [
            "Smith",
            "Jones",
            "Williams",
            "Brown",
            "Taylor",
            "Davies",
            "Wilson",
            "Evans",
            "Thomas",
            "Johnson",
            "Roberts",
            "Walker",
            "Wright",
            "Robinson",
            "Thompson",
            "White",
            "Hughes",
            "Edwards",
            "Green",
            "Hall",
            "Wood",
            "Harris",
            "Lewis",
            "Martin",
            "Jackson",
            "Clarke",
            "Turner",
            "Hill",
            "Moore",
            "Cooper",
        ]

        # Common UK first names
        self.first_names = [
            "James",
            "Mary",
            "John",
            "Patricia",
            "Robert",
            "Jennifer",
            "Michael",
            "Linda",
            "William",
            "Elizabeth",
            "David",
            "Barbara",
            "Richard",
            "Susan",
            "Joseph",
            "Jessica",
            "Thomas",
            "Sarah",
            "Charles",
            "Karen",
            "Christopher",
            "Nancy",
            "Daniel",
            "Lisa",
            "Matthew",
            "Betty",
            "Anthony",
            "Margaret",
            "Mark",
            "Sandra",
        ]

        # Track used emails to avoid duplicates
        self.used_emails = set()

        # Case types
        self.case_types = [
            "Criminal",
            "Civil",
            "Family",
            "Commercial",
            "Employment",
            "Immigration",
            "Tax",
            "Chancery",
            "Administrative",
            "Tribunal",
        ]

        # Valid UserProfile roles (from the model)
        self.valid_profile_roles = [
            "judge",
            "lawyer",
            "clerk",
            "defendant",
            "witness",
            "prosecutor",
            "public",
            "admin",
        ]

        # Case titles/templates
        self.case_titles = {
            "Criminal": [
                "R v {}",
                "Crown Prosecution Service v {}",
                "DPP v {}",
            ],
            "Civil": [
                "{} v {}",
                "{} & Anor v {}",
                "{} (Claimant) v {} (Defendant)",
            ],
            "Family": [
                "Re {} (Child)",
                "{} v {} (Divorce)",
                "A Local Authority v {}",
            ],
            "Commercial": [
                "{} Ltd v {} plc",
                "{} (Trading) v {}",
                "{} International v {} Group",
            ],
        }

    def generate_unique_email(self, base_email):
        """Generate a unique email by adding a random suffix if needed"""
        if base_email not in self.used_emails:
            self.used_emails.add(base_email)
            return base_email

        # If email exists, add a random suffix
        name, domain = base_email.split("@")
        for _ in range(10):  # Try up to 10 times
            new_email = f"{name}{random.randint(1, 9999)}@{domain}"
            if new_email not in self.used_emails:
                self.used_emails.add(new_email)
                return new_email

        # If all else fails, use UUID
        new_email = f"{name}{uuid.uuid4().hex[:8]}@{domain}"
        self.used_emails.add(new_email)
        return new_email

    def create_user_with_profile(
        self, email, password, first_name, last_name, role_data=None, **extra_fields
    ):
        """Create a user and ensure profile is created - handles duplicate emails"""
        from accounts.models import UserProfile

        # Validate role
        if role_data and "role" in role_data:
            if role_data["role"] not in self.valid_profile_roles:
                print(
                    f"Warning: Invalid role '{role_data['role']}' for UserProfile. Using 'public' instead."
                )
                role_data["role"] = "public"

        # Generate unique email if needed
        unique_email = self.generate_unique_email(email)

        # Check if user already exists in DB (for idempotency)
        existing_user = User.objects.filter(email=unique_email).first()
        if existing_user:
            print(f"User {unique_email} already exists, skipping...")
            return existing_user

        # Create the user
        user = User.objects.create_user(
            email=unique_email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )

        # Prepare profile data
        profile_defaults = {
            "role": role_data.get("role", "public") if role_data else "public"
        }

        # Add court to profile defaults if provided (must be a Court instance)
        if role_data and "court" in role_data:
            profile_defaults["court"] = role_data["court"]

        # Add other fields
        if role_data:
            for key, value in role_data.items():
                if key not in ["role", "court"] and hasattr(UserProfile, key):
                    profile_defaults[key] = value

        # Create or update profile
        profile, created = UserProfile.objects.update_or_create(
            user=user, defaults=profile_defaults
        )

        return user

    def clear_existing_data(self):
        """Clear all existing data in the correct order"""
        print("Clearing existing data...")

        # Delete in reverse order of dependencies
        HearingDocument.objects.all().delete()
        print("  - Deleted hearing documents")

        HearingParticipant.objects.all().delete()
        print("  - Deleted hearing participants")

        Hearing.objects.all().delete()
        print("  - Deleted hearings")

        CaseParty.objects.all().delete()
        print("  - Deleted case parties")

        Case.objects.all().delete()
        print("  - Deleted cases")

        from accounts.models import UserProfile

        UserProfile.objects.all().delete()
        print("  - Deleted user profiles")

        # Delete non-superuser users
        User.objects.filter(is_superuser=False).delete()
        print("  - Deleted regular users")

        Courtroom.objects.all().delete()
        print("  - Deleted courtrooms")

        Court.objects.all().delete()
        print("  - Deleted courts")

        # Clear the used_emails set
        self.used_emails.clear()

        print("Existing data cleared successfully.")

    def create_courts_and_rooms(self):
        """Create courts and their courtrooms"""
        print("Creating courts and courtrooms...")

        for court_info in self.court_data:
            court_name = f"{court_info['name']} - {court_info['city']}"

            # Check if court already exists
            court, created = Court.objects.get_or_create(
                name=court_name,
                defaults={
                    "id": uuid.uuid4(),
                    "jurisdiction": court_info["jurisdiction"],
                    "address": f"{random.randint(1, 100)} {random.choice(['High', 'Queen', 'King', 'Victoria'])} Street, {court_info['city']}, UK",
                    "contact_info": {
                        "phone": f"+44 {random.randint(20, 29)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}",
                        "email": f"enquiries@{court_info['name'].lower().replace(' ', '')}.gov.uk",
                        "dx": f"DX {random.randint(10000, 99999)} {court_info['city']}",
                    },
                },
            )
            self.courts.append(court)

            if created:
                # Create 2-4 courtrooms per new court
                for i in range(random.randint(2, 4)):
                    courtroom = Courtroom.objects.create(
                        id=uuid.uuid4(),
                        court=court,
                        name=f"Court Room {i + 1}",
                        capacity=random.choice([20, 30, 50, 75, 100]),
                        video_platform_config={
                            "provider": "Zoom",
                            "meeting_enabled": True,
                            "recording_enabled": True,
                            "waiting_room": True,
                        },
                    )
                    self.courtrooms.append(courtroom)
            else:
                # Add existing courtrooms to the list
                courtrooms = Courtroom.objects.filter(court=court)
                self.courtrooms.extend(list(courtrooms))

        print(f"Using {len(self.courts)} courts with {len(self.courtrooms)} courtrooms")

    def create_users(self):
        """Create various user types with profiles"""
        print("Creating users...")

        # Check if admin already exists
        admin_user = User.objects.filter(email="admin@courts.gov.uk").first()
        if not admin_user:
            # Create superuser/admin
            admin_user = self.create_user_with_profile(
                email="admin@courts.gov.uk",
                password="admin123",
                first_name="Admin",
                last_name="User",
                is_staff=True,
                is_superuser=True,
                is_active=True,
                is_email_verified=True,
                is_admin_approved=True,
                is_verified=True,
                role_data={"role": "admin", "bio": "System Administrator"},
            )
        self.users["admin"] = admin_user

        # Create judges
        self.users["judges"] = list(User.objects.filter(profile__role="judge"))
        judges_needed = max(0, 5 - len(self.users["judges"]))

        for i in range(judges_needed):
            first = random.choice(self.first_names)
            last = random.choice(self.surnames)
            email = f"judge.{last.lower()}@courts.gov.uk"

            # Select a random court for this judge
            court = random.choice(self.courts)

            user = self.create_user_with_profile(
                email=email,
                password="judge123",
                first_name=first,
                last_name=last,
                is_active=True,
                is_email_verified=True,
                is_admin_approved=True,
                is_verified=True,
                role_data={
                    "role": "judge",
                    "court": court,
                    "bio": f"Presiding judge at {court.name}. {random.randint(5, 25)} years of judicial experience.",
                    "office_address": f"Chambers, {court.name}",
                },
            )

            self.users["judges"].append(user)

        # Create lawyers
        self.users["lawyers"] = list(User.objects.filter(profile__role="lawyer"))
        lawyers_needed = max(0, 8 - len(self.users["lawyers"]))

        law_firms = [
            "Smith & Co",
            "Jones LLP",
            "Williams Solicitors",
            "Brown & Partners",
            "Taylor Legal",
            "Davies Law",
            "Wilson & Wilson",
            "Evans Solicitors",
        ]

        for i in range(lawyers_needed):
            first = random.choice(self.first_names)
            last = random.choice(self.surnames)
            email = f"{first.lower()}.{last.lower()}@legal.co.uk"

            firm = random.choice(law_firms)
            specialization = random.choice(
                [
                    "Criminal Law",
                    "Civil Litigation",
                    "Family Law",
                    "Commercial Law",
                    "Employment Law",
                    "Immigration Law",
                    "Tax Law",
                    "Human Rights",
                ]
            )

            user = self.create_user_with_profile(
                email=email,
                password="lawyer123",
                first_name=first,
                last_name=last,
                is_active=True,
                is_email_verified=True,
                is_admin_approved=True,
                is_verified=True,
                role_data={
                    "role": "lawyer",
                    "bar_number": f"BAR{random.randint(10000, 99999)}",
                    "specialization": specialization,
                    "bio": f"Partner at {firm}. Specializing in {specialization}.",
                    "office_address": f"{firm}, {random.randint(1, 100)} High Street, London",
                },
            )

            self.users["lawyers"].append(user)

        # Create defendants/witnesses/prosecutors (public users with valid profile roles)
        self.users["parties"] = list(
            User.objects.filter(
                profile__role__in=["defendant", "witness", "prosecutor", "public"]
            )
        )
        parties_needed = max(0, 12 - len(self.users["parties"]))

        # Valid roles for regular parties (not lawyers/judges/staff)
        party_profile_roles = ["defendant", "witness", "prosecutor", "public"]

        for i in range(parties_needed):
            first = random.choice(self.first_names)
            last = random.choice(self.surnames)
            email = f"{first.lower()}.{last.lower()}@email.com"
            profile_role = random.choice(party_profile_roles)

            user = self.create_user_with_profile(
                email=email,
                password="party123",
                first_name=first,
                last_name=last,
                is_active=True,
                is_email_verified=True,
                is_admin_approved=True,
                is_verified=True,
                role_data={
                    "role": profile_role,
                    "bio": f"Private individual - {profile_role}",
                },
            )

            self.users["parties"].append(user)

        # Create court staff
        self.users["staff"] = list(
            User.objects.filter(profile__role__in=["clerk", "usher"])
        )
        staff_needed = max(0, 4 - len(self.users["staff"]))

        staff_roles = ["clerk", "usher"]
        for i in range(staff_needed):
            first = random.choice(self.first_names)
            last = random.choice(self.surnames)
            email = f"{first.lower()}.{last.lower()}@courts.gov.uk"

            court = random.choice(self.courts)
            role = random.choice(staff_roles)

            user = self.create_user_with_profile(
                email=email,
                password="staff123",
                first_name=first,
                last_name=last,
                is_active=True,
                is_email_verified=True,
                is_admin_approved=True,
                is_verified=True,
                role_data={
                    "role": role,
                    "court": court,
                    "bio": f"Court {role} at {court.name}",
                },
            )

            self.users["staff"].append(user)

        print(f"Total users: {User.objects.count()}")
        from accounts.models import UserProfile

        print(f"Total profiles: {UserProfile.objects.count()}")
        print(f"  - Judges: {len(self.users['judges'])}")
        print(f"  - Lawyers: {len(self.users['lawyers'])}")
        print(
            f"  - Parties (defendant/witness/prosecutor/public): {len(self.users['parties'])}"
        )
        print(f"  - Staff: {len(self.users['staff'])}")

    def create_cases(self):
        """Create cases with parties"""
        print("Creating cases...")

        status_choices = ["open", "closed", "appealed", "stayed"]
        weights = [0.6, 0.2, 0.1, 0.1]  # 60% open, 20% closed, etc.

        cases_needed = max(0, 15 - Case.objects.count())

        for i in range(cases_needed):
            case_type = random.choice(self.case_types)

            # Generate case number (UK format)
            year = random.randint(2019, 2024)
            if case_type == "Criminal":
                case_number = (
                    f"{year}{random.choice(['CR', 'T'])}{random.randint(1000, 9999)}"
                )
            elif case_type == "Civil":
                case_number = (
                    f"{year}{random.choice(['HC', 'CC'])}{random.randint(10000, 99999)}"
                )
            elif case_type == "Family":
                case_number = (
                    f"{year}{random.choice(['FD', 'FC'])}{random.randint(1000, 9999)}"
                )
            else:
                case_number = (
                    f"{year}{random.choice(['CH', 'QB'])}{random.randint(10000, 99999)}"
                )

            # Check if case number already exists
            if Case.objects.filter(case_number=case_number).exists():
                case_number = f"{case_number}-{uuid.uuid4().hex[:4].upper()}"

            # Generate title based on case type
            if len(self.users["parties"]) < 2:
                print("Not enough parties to create cases")
                continue

            parties_involved = random.sample(self.users["parties"], 2)

            if case_type in self.case_titles:
                title_template = random.choice(self.case_titles[case_type])
                if "{}" in title_template and title_template.count("{}") == 1:
                    title = title_template.format(parties_involved[0].last_name)
                else:
                    title = title_template.format(
                        parties_involved[0].last_name, parties_involved[1].last_name
                    )
            else:
                title = f"{parties_involved[0].last_name} vs {parties_involved[1].last_name}"

            # Select a judge for this case
            if not self.users["judges"]:
                continue
            judge = random.choice(self.users["judges"])

            # Create case
            case = Case.objects.create(
                id=uuid.uuid4(),
                case_number=case_number,
                title=title,
                case_type=case_type,
                status=random.choices(status_choices, weights=weights)[0],
                judge=judge,
            )

            # Add parties to case with appropriate CaseParty roles
            for idx, party in enumerate(parties_involved):
                if case_type == "Criminal":
                    # For criminal cases
                    if idx == 0:
                        role = "defendant"
                    else:
                        role = random.choice(["witness", "prosecutor"])
                elif case_type == "Civil":
                    # For civil cases - using valid CaseParty roles
                    role = "claimant" if idx == 0 else "respondent"
                elif case_type == "Family":
                    # For family cases
                    role = random.choice(["claimant", "respondent"])
                else:
                    role = random.choice(
                        ["claimant", "respondent", "defendant", "witness"]
                    )

                CaseParty.objects.get_or_create(
                    case=case,
                    user=party,
                    party_role=role,
                    defaults={"id": uuid.uuid4()},
                )

            # Add legal representatives
            if self.users["lawyers"]:
                num_lawyers = min(random.randint(1, 2), len(self.users["lawyers"]))
                for lawyer in random.sample(self.users["lawyers"], num_lawyers):
                    if case_type == "Criminal":
                        lawyer_role = random.choice(
                            ["defence_counsel", "prosecution_counsel"]
                        )
                    elif case_type == "Civil":
                        lawyer_role = random.choice(["claimant_counsel", "solicitor"])
                    else:
                        lawyer_role = random.choice(
                            ["defence_counsel", "claimant_counsel", "solicitor"]
                        )

                    CaseParty.objects.get_or_create(
                        case=case,
                        user=lawyer,
                        party_role=lawyer_role,
                        defaults={"id": uuid.uuid4()},
                    )

            # Add court staff to case
            if self.users["staff"]:
                num_staff = min(random.randint(0, 2), len(self.users["staff"]))
                if num_staff > 0:
                    for staff in random.sample(self.users["staff"], num_staff):
                        CaseParty.objects.get_or_create(
                            case=case,
                            user=staff,
                            party_role=staff.profile.role,  # 'clerk' or 'usher' are valid CaseParty roles
                            defaults={"id": uuid.uuid4()},
                        )

            self.cases.append(case)

        # Refresh cases list
        self.cases = list(Case.objects.all())
        print(f"Total cases: {len(self.cases)}")

    def create_hearings(self, num_hearings=20):
        """Create up to 20 hearings"""
        print(f"Creating up to {num_hearings} hearings...")

        hearing_types = [choice[0] for choice in Hearing.HearingType.choices]
        status_choices = [
            "scheduled",
            "in_progress",
            "completed",
            "cancelled",
            "postponed",
        ]
        status_weights = [
            0.3,
            0.2,
            0.3,
            0.1,
            0.1,
        ]  # 30% scheduled, 20% in progress, etc.

        now = timezone.now()

        hearings_needed = max(0, num_hearings - Hearing.objects.count())

        for i in range(hearings_needed):
            if not self.cases or not self.courtrooms:
                break

            case = random.choice(self.cases)
            courtroom = random.choice(self.courtrooms)
            hearing_type = random.choice(hearing_types)
            status = random.choices(status_choices, weights=status_weights)[0]

            # Calculate scheduled time based on status
            if status == "completed":
                scheduled_at = now - timedelta(days=random.randint(1, 60))
                started_at = scheduled_at + timedelta(minutes=random.randint(0, 30))
                ended_at = started_at + timedelta(minutes=random.randint(30, 180))
            elif status == "in_progress":
                scheduled_at = now - timedelta(minutes=random.randint(30, 90))
                started_at = scheduled_at + timedelta(minutes=random.randint(0, 15))
                ended_at = None
            elif status == "scheduled":
                scheduled_at = now + timedelta(days=random.randint(1, 30))
                started_at = None
                ended_at = None
            elif status == "postponed":
                scheduled_at = now + timedelta(days=random.randint(-60, -1))
                started_at = None
                ended_at = None
            else:  # cancelled
                scheduled_at = now + timedelta(days=random.randint(-30, -1))
                started_at = None
                ended_at = None

            # Create hearing name/description
            if status == "scheduled":
                name = f"Scheduled {hearing_type.replace('_', ' ').title()} - {case.case_number}"
            elif status == "in_progress":
                name = f"Ongoing {hearing_type.replace('_', ' ').title()} - {case.case_number}"
            else:
                name = f"{hearing_type.replace('_', ' ').title()} - {case.case_number}"

            description = f"{hearing_type.replace('_', ' ').title()} in the matter of {case.title}"

            # Create hearing
            hearing = Hearing.objects.create(
                id=uuid.uuid4(),
                name=name,
                description=description,
                case=case,
                courtroom=courtroom,
                hearing_type=hearing_type,
                status=status,
                scheduled_at=scheduled_at,
                started_at=started_at,
                ended_at=ended_at,
                session_id=f"session_{uuid.uuid4().hex[:8]}",
                session_url=f"https://courts.gov.uk/hearing/{uuid.uuid4().hex[:12]}",
                is_public=random.choice([True, False]),
            )

            # Add participants to hearing
            self._add_hearing_participants(hearing, case)

            # Add documents for completed/in_progress hearings
            if status in ["completed", "in_progress"]:
                self._add_hearing_documents(hearing)

            self.hearings.append(hearing)

        print(f"Total hearings: {Hearing.objects.count()}")

    def _add_hearing_participants(self, hearing, case):
        """Add participants to a hearing"""
        # Get all case parties
        case_parties = CaseParty.objects.filter(case=case).select_related("user")

        for case_party in case_parties:
            # Randomly decide if they attend (80% attendance rate)
            if random.random() < 0.8:
                connection_status = random.choice(
                    ["waiting", "connected", "disconnected"]
                )
                joined_at = None
                left_at = None

                if hearing.status == "completed":
                    joined_at = hearing.started_at + timedelta(
                        minutes=random.randint(0, 10)
                    )
                    left_at = hearing.ended_at - timedelta(
                        minutes=random.randint(0, 15)
                    )
                    connection_status = "disconnected"
                elif hearing.status == "in_progress":
                    joined_at = hearing.started_at + timedelta(
                        minutes=random.randint(0, 20)
                    )
                    connection_status = "connected"
                elif hearing.status == "scheduled":
                    connection_status = "waiting"

                HearingParticipant.objects.get_or_create(
                    hearing=hearing,
                    user=case_party.user,
                    role=case_party.party_role,
                    defaults={
                        "id": uuid.uuid4(),
                        "joined_at": joined_at,
                        "left_at": left_at,
                        "connection_status": connection_status,
                    },
                )

    def _add_hearing_documents(self, hearing):
        """Add mock documents to a hearing"""
        doc_types = ["motion", "evidence", "transcript", "order", "exhibit"]

        # Add 1-3 documents per hearing
        for _ in range(random.randint(1, 3)):
            doc_type = random.choice(doc_types)

            # Create mock file content
            file_name = (
                f"{doc_type}_{hearing.case.case_number}_{uuid.uuid4().hex[:8]}.pdf"
            )

            # Select uploader (judge or lawyer)
            uploader_pool = [hearing.case.judge] + self.users.get("lawyers", [])
            if not uploader_pool:
                continue

            # Determine admitted status based on document type
            # admitted field cannot be null, so always set a boolean value
            if doc_type in ["evidence", "exhibit"]:
                # Evidence and exhibits can be admitted or not
                admitted = random.choice([True, False])
            elif doc_type == "order":
                # Court orders are typically admitted/issued
                admitted = True
            elif doc_type == "transcript":
                # Transcripts are usually admitted as records
                admitted = True
            else:  # motion and others
                # Motions may or may not be admitted
                admitted = random.choice([True, False])

            # Determine sealed status
            is_sealed = (
                random.choice([True, False]) if doc_type == "evidence" else False
            )

            HearingDocument.objects.get_or_create(
                hearing=hearing,
                file_name=file_name,
                defaults={
                    "id": uuid.uuid4(),
                    "uploaded_by": random.choice(uploader_pool),
                    "doc_type": doc_type,
                    "file_size": random.randint(10000, 1000000),
                    "content_type": "application/pdf",
                    "is_sealed": is_sealed,
                    "admitted": admitted,  # Now always set to a boolean value
                },
            )

    def create_specific_hearing_scenarios(self):
        """Create some specific hearing scenarios for realism"""
        print("Creating specific hearing scenarios...")

        now = timezone.now()

        # Scenario 1: High-profile criminal trial in progress
        criminal_case = next((c for c in self.cases if c.case_type == "Criminal"), None)
        if criminal_case and self.users.get("judges") and self.users.get("lawyers"):
            hearing, created = Hearing.objects.get_or_create(
                name="R v Smith - Day 3 of Trial",
                case=criminal_case,
                defaults={
                    "id": uuid.uuid4(),
                    "description": "High-profile murder trial - Day 3",
                    "courtroom": random.choice(self.courtrooms),
                    "hearing_type": Hearing.HearingType.TRIAL,
                    "status": "in_progress",
                    "scheduled_at": now - timedelta(hours=2),
                    "started_at": now - timedelta(hours=1, minutes=45),
                    "session_id": f"session_{uuid.uuid4().hex[:8]}",
                    "session_url": "https://courts.gov.uk/hearing/highprofile123",
                    "is_public": True,
                },
            )

            if created:
                # Add participants
                for user in self.users["judges"][:1]:
                    HearingParticipant.objects.get_or_create(
                        hearing=hearing,
                        user=user,
                        role="judge",
                        defaults={
                            "id": uuid.uuid4(),
                            "joined_at": hearing.started_at,
                            "connection_status": "connected",
                        },
                    )

                for lawyer in self.users["lawyers"][:3]:
                    HearingParticipant.objects.get_or_create(
                        hearing=hearing,
                        user=lawyer,
                        role=random.choice(["defence_counsel", "prosecution_counsel"]),
                        defaults={
                            "id": uuid.uuid4(),
                            "joined_at": hearing.started_at
                            + timedelta(minutes=random.randint(0, 5)),
                            "connection_status": "connected",
                        },
                    )

        # Scenario 2: Family court hearing tomorrow
        family_case = next((c for c in self.cases if c.case_type == "Family"), None)
        if family_case and self.users.get("judges"):
            hearing, created = Hearing.objects.get_or_create(
                name="Child Arrangements Hearing",
                case=family_case,
                defaults={
                    "id": uuid.uuid4(),
                    "description": "Re: Smith children - Directions hearing",
                    "courtroom": random.choice(self.courtrooms),
                    "hearing_type": Hearing.HearingType.CHILD_ARRANGEMENTS,
                    "status": "scheduled",
                    "scheduled_at": now + timedelta(days=1, hours=10),
                    "session_id": f"session_{uuid.uuid4().hex[:8]}",
                    "session_url": "https://courts.gov.uk/hearing/family123",
                    "is_public": False,
                },
            )

            if created:
                HearingParticipant.objects.get_or_create(
                    hearing=hearing,
                    user=random.choice(self.users["judges"]),
                    role="judge",
                    defaults={"id": uuid.uuid4(), "connection_status": "waiting"},
                )

        print("Specific hearing scenarios created/verified.")

    @transaction.atomic
    def seed_all(self, clear_existing=False):
        """Run the complete seeding process"""
        print("\n" + "=" * 50)
        print("STARTING DATABASE SEEDING")
        print("=" * 50 + "\n")

        if clear_existing:
            self.clear_existing_data()

        # Order matters: Courts first, then users, then cases, then hearings
        self.create_courts_and_rooms()
        self.create_users()
        self.create_cases()
        self.create_hearings(20)  # Create up to 20 hearings
        self.create_specific_hearing_scenarios()

        print("\n" + "=" * 50)
        print("SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 50)
        print(f"\nSummary:")
        print(f"- Courts: {Court.objects.count()}")
        print(f"- Courtrooms: {Courtroom.objects.count()}")
        print(f"- Users: {User.objects.count()}")
        from accounts.models import UserProfile

        print(f"- User Profiles: {UserProfile.objects.count()}")
        print(f"- Cases: {Case.objects.count()}")
        from cases.models import CaseParty

        print(f"- Case Parties: {CaseParty.objects.count()}")
        print(f"- Hearings: {Hearing.objects.count()}")
        print(f"- Hearing Participants: {HearingParticipant.objects.count()}")
        print(f"- Hearing Documents: {HearingDocument.objects.count()}")


def run(clear_existing=False):
    """Function to run the seeder (for use with Django shell or management command)"""
    seeder = DataSeeder()
    seeder.seed_all(clear_existing=clear_existing)


if __name__ == "__main__":
    # This allows running directly: python seed_data.py
    import django
    import os
    import sys

    # Update this to your project's settings module
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "your_project.settings"
    )  # CHANGE THIS

    django.setup()

    # Check command line arguments
    clear = "--clear" in sys.argv

    run(clear_existing=clear)
