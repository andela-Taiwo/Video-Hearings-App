from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid

from cases.models import Case
from courts.models import Courtroom


class ActiveHearingManager(models.Manager):
    """Manager that returns only active hearings"""

    ACTIVE_STATUSES = ["scheduled", "in_progress", "postponed", "recessed"]

    def get_queryset(self):
        return super().get_queryset().filter(status__in=self.ACTIVE_STATUSES)


class Hearing(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled"
        IN_PROGRESS = "in_progress"
        RECESSED = "recessed"
        COMPLETED = "completed"
        CANCELLED = "cancelled"
        POSTPONED = "postponed"

    class HearingType(models.TextChoices):
        """
        Comprehensive list of UK court hearing types
        Covers Criminal, Civil, Family, and Tribunals
        """

        # CRIMINAL COURT HEARINGS
        ARRAIGNMENT = "arraignment", _("Arraignment")
        BAIL = "bail", _("Bail Hearing")
        BAIL_APPLICATION = "bail_application", _("Bail Application")
        BAIL_VARIATION = "bail_variation", _("Bail Variation")
        CASE_MANAGEMENT = "case_management", _("Case Management Hearing")
        PLEA = "plea", _("Plea Hearing")
        PLEA_TRIAL_PREPARATION = "ptph", _("Plea and Trial Preparation Hearing")
        TRIAL = "trial", _("Trial")
        SENTENCING = "sentencing", _("Sentencing Hearing")
        COMMITTAL = "committal", _("Committal for Sentence")
        APPEAL = "appeal", _("Appeal Hearing")
        MENTION = "mention", _("Mention Hearing")
        PRE_TRIAL_REVIEW = "ptr", _("Pre-Trial Review")
        DIRECTIONS = "directions", _("Directions Hearing")
        CASE_STATED = "case_stated", _("Case Stated")
        CONFISCATION = "confiscation", _("Confiscation Hearing")
        BREACH = "breach", _("Breach Hearing")
        REVIEW = "review", _("Review Hearing")
        REMAND = "remand", _("Remand Hearing")
        EXTRAdition = "extradition", _("Extradition Hearing")

        # MAGISTRATES COURT SPECIFIC
        FIRST_HEARING = "first_hearing", _("First Hearing")
        MODE_OF_TRIAL = "mode_of_trial", _("Mode of Trial Hearing")
        ALLOCATION = "allocation", _("Allocation Hearing")
        SENDING_FOR_TRIAL = "sending_for_trial", _("Sending for Trial")
        YOUTH_COURT = "youth_court", _("Youth Court Hearing")

        # CIVIL COURT HEARINGS
        CIVIL_TRIAL = "civil_trial", _("Civil Trial")
        CIVIL_CASE_MANAGEMENT = "civil_ccmc", _("Civil Case Management Conference")
        INTERIM = "interim", _("Interim Hearing")
        SUMMARY_JUDGMENT = "summary_judgment", _("Summary Judgment Hearing")
        INJUNCTION = "injunction", _("Injunction Hearing")
        POSSESSION = "possession", _("Possession Hearing")
        SMALL_CLAIMS = "small_claims", _("Small Claims Hearing")
        FAST_TRACK_TRIAL = "fast_track_trial", _("Fast Track Trial")
        MULTI_TRACK_TRIAL = "multi_track_trial", _("Multi-Track Trial")
        DISPOSAL = "disposal", _("Disposal Hearing")
        PRE_TRIAL_CHECK = "pre_trial_check", _("Pre-Trial Check")
        COSTS = "costs", _("Costs Hearing")
        ASSESSMENT = "assessment", _("Damages Assessment")
        ACKNOWLEDGMENT = "acknowledgment", _("Acknowledgment of Service Hearing")

        # FAMILY COURT HEARINGS
        FIRST_DIRECTIONS = "first_directions", _("First Directions Appointment")
        FDR = "fdr", _("Financial Dispute Resolution")
        FINANCIAL_FINAL = "financial_final", _("Final Financial Hearing")
        CHILD_ARRANGEMENTS = "child_arrangements", _("Child Arrangements Hearing")
        CAFCASS = "cafcass", _("CAFCASS Meeting")
        CARE_ORDER = "care_order", _("Care Order Hearing")
        SUPERVISION_ORDER = "supervision_order", _("Supervision Order Hearing")
        ADOPTION = "adoption", _("Adoption Hearing")
        EMERGENCY_PROTECTION = (
            "emergency_protection",
            _("Emergency Protection Order Hearing"),
        )
        CONTACT = "contact", _("Contact Hearing")
        FACT_FINDING = "fact_finding", _("Fact Finding Hearing")
        ISSUES_RESOLUTION = "issues_resolution", _("Issues Resolution Hearing")
        DISPUTE_RESOLUTION = "dispute_resolution", _("Dispute Resolution Appointment")
        CASE_MANAGEMENT_FAMILY = (
            "case_management_family",
            _("Case Management Hearing (Family)"),
        )

        # TRIBUNAL HEARINGS
        TRIBUNAL_FIRST = "tribunal_first", _("First Tier Tribunal")
        TRIBUNAL_UPPER = "tribunal_upper", _("Upper Tribunal")
        TRIBUNAL_CASE_MANAGEMENT = "tribunal_cm", _("Tribunal Case Management")
        EMPLOYMENT = "employment", _("Employment Tribunal")
        IMMIGRATION = "immigration", _("Immigration Hearing")
        SOCIAL_SECURITY = "social_security", _("Social Security Appeal")
        MENTAL_HEALTH = "mental_health", _("Mental Health Tribunal")
        SPECIAL_EDUCATION = "sen", _("Special Educational Needs Tribunal")
        LANDS = "lands", _("Lands Tribunal")
        TAX = "tax", _("Tax Tribunal")

        # CROWN COURT SPECIFIC
        PTPH_CROWN = "ptph_crown", _("Plea and Trial Preparation Hearing (Crown)")
        PCMH = "pcmh", _("Pre-Trial and Case Management Hearing")
        GROUND_RULES = "ground_rules", _("Ground Rules Hearing")
        VULNERABLE_WITNESS = "vulnerable_witness", _("Vulnerable Witness Hearing")
        SPECIAL_MEASURES = "special_measures", _("Special Measures Hearing")

        # HIGH COURT SPECIFIC
        CHANCERY = "chancery", _("Chancery Division Hearing")
        QUEENS_BENCH = "queens_bench", _("Queen's Bench Division Hearing")
        FAMILY_DIVISION = "family_division", _("Family Division Hearing")
        ADMINISTRATIVE = "administrative", _("Administrative Court Hearing")
        COMMERCIAL = "commercial", _("Commercial Court Hearing")
        TECHNOLOGY_CONSTRUCTION = "tcc", _("Technology & Construction Court Hearing")
        ADMIRALTY = "admiralty", _("Admiralty Court Hearing")

        # COURT OF APPEAL
        COA_CIVIL = "coa_civil", _("Court of Appeal (Civil Division)")
        COA_CRIMINAL = "coa_criminal", _("Court of Appeal (Criminal Division)")
        COA_PERMISSION = "coa_permission", _("Permission to Appeal Hearing")

        # SUPREME COURT
        SUPREME_COURT = "supreme_court", _("UK Supreme Court Hearing")

        # SPECIALIST HEARINGS
        INQUEST = "inquest", _("Inquest Hearing")
        CORONERS = "coroners", _("Coroner's Court Hearing")
        COURT_MARTIAL = "court_martial", _("Court Martial")
        ECCLESIASTICAL = "ecclesiastical", _("Ecclesiastical Court Hearing")

        # ENFORCEMENT
        CHARGING_ORDER = "charging_order", _("Charging Order Hearing")
        ATTACHMENT_EARNINGS = "attachment_earnings", _("Attachment of Earnings Hearing")
        THIRD_PARTY_DEBT = "third_party_debt", _("Third Party Debt Order Hearing")
        COMMITTAL_ENFORCEMENT = "committal_enforcement", _("Committal for Non-Payment")
        BAILIFF = "bailiff", _("Bailiff Hearing")

        # MEDIATION AND ALTERNATIVE
        MEDIATION = "mediation", _("Mediation Appointment")
        ARBITRATION = "arbitration", _("Arbitration Hearing")
        EARLY_NEUTRAL = "early_neutral", _("Early Neutral Evaluation")

        HYBRID_HEARING = "hybrid", _("Hybrid Hearing")

    objects = models.Manager()

    active = ActiveHearingManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    case = models.ForeignKey(Case, on_delete=models.PROTECT, related_name="hearings")
    courtroom = models.ForeignKey(Courtroom, on_delete=models.PROTECT)
    hearing_type = models.CharField(
        max_length=50,
        choices=HearingType.choices,
        default=HearingType.HYBRID_HEARING,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    session_id = models.CharField(max_length=200, blank=True)
    session_url = models.URLField(blank=True)
    recording_url = models.URLField(blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["case", "status"]),
        ]

    def __str__(self):
        return f"Hearing {self.id} - {self.case.case_number} - {self.hearing_type}"


class HearingParticipant(models.Model):
    class ConnectionStatus(models.TextChoices):
        WAITING = "waiting"
        CONNECTED = "connected"
        DISCONNECTED = "disconnected"
        RECONNECTING = "reconnecting"

    class PartyRole(models.TextChoices):
        """UK legal system party roles - Common usage"""

        # Criminal cases
        DEFENDANT = "defendant", "Defendant"
        PROSECUTOR = "prosecutor", "Prosecutor"  # CPS

        # Civil cases
        CLAIMANT = "claimant", "Claimant"  # Person bringing claim
        RESPONDENT = "respondent", "Respondent"  # Person defending claim

        # Legal representatives
        DEFENCE_COUNSEL = "defence_counsel", "Defence Counsel"  # Barrister for defence
        PROSECUTION_COUNSEL = (
            "prosecution_counsel",
            "Prosecution Counsel",
        )  # Barrister for prosecution
        CLAIMANT_COUNSEL = (
            "claimant_counsel",
            "Claimant Counsel",
        )  # Barrister for claimant
        SOLICITOR = "solicitor", "Solicitor"  # Solicitor

        # Court officials
        JUDGE = "judge", "Judge"
        MAGISTRATE = "magistrate", "Magistrate"
        CLERK = "clerk", "Court Clerk"
        USHER = "usher", "Court Usher"

        # Others
        JUROR = "juror", "Juror"
        WITNESS = "witness", "Witness"
        INTERPRETER = "interpreter", "Interpreter"
        PUBLIC = "public", "Public"

        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hearing = models.ForeignKey(
        Hearing, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=50,
        choices=PartyRole.choices,
        default=PartyRole.OTHER,
        null=True,
        blank=True,
    )
    join_token = models.UUIDField(default=uuid.uuid4, unique=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    connection_status = models.CharField(
        max_length=20,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.WAITING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["hearing", "user", "role"]
        indexes = [
            models.Index(fields=["join_token"]),
            models.Index(fields=["connection_status"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.role} - {self.hearing.id}"


class HearingDocument(models.Model):
    class DocType(models.TextChoices):
        MOTION = "motion"
        EVIDENCE = "evidence"
        TRANSCRIPT = "transcript"
        ORDER = "order"
        EXHIBIT = "exhibit"
        WARRANT = "warrant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hearing = models.ForeignKey(
        Hearing, on_delete=models.PROTECT, related_name="documents"
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    file = models.FileField(upload_to="hearing_docs/%Y/%m/")
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    is_sealed = models.BooleanField(default=False)
    admitted = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["hearing", "doc_type"]),
            models.Index(fields=["uploaded_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.file and not self.file_name:
            self.file_name = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.doc_type} - {self.hearing.id} - {self.file_name}"
