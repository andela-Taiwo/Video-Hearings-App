from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from uuid import uuid4


class Case(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        APPEALED = "appealed", "Appealed"
        STAYED = "stayed", "Stayed"

    case_number = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=300)
    description = models.CharField(max_length=300, null=True, blank=True)
    case_type = models.CharField(max_length=50, db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="presiding_cases",
    )
    parties = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="CaseParty", related_name="cases"
    )
    filed_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["case_number", "status"]),
            models.Index(fields=["judge", "status"]),
        ]

    def __str__(self):
        return f"{self.case_number} - {self.title}"

    def get_party_count(self):
        return self.caseparty_set.count()

    def get_parties_by_role(self, role):
        return self.caseparty_set.filter(party_role=role).select_related("user")


class CaseParty(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    class PartyRole(models.TextChoices):
        """UK legal system party roles - Common usage"""

        # Criminal cases
        DEFENDANT = "defendant", "Defendant"
        PROSECUTOR = "prosecutor", "Prosecutor" 

        # Civil cases
        CLAIMANT = "claimant", "Claimant" 
        RESPONDENT = "respondent", "Respondent"

        # Legal representatives
        DEFENCE_COUNSEL = "defence_counsel", "Defence Counsel"
        PROSECUTION_COUNSEL = (
            "prosecution_counsel",
            "Prosecution Counsel",
        )  
        CLAIMANT_COUNSEL = (
            "claimant_counsel",
            "Claimant Counsel",
        )  
        SOLICITOR = "solicitor", "Solicitor" 

        # Court officials
        JUDGE = "judge", "Judge"
        MAGISTRATE = "magistrate", "Magistrate"
        CLERK = "clerk", "Court Clerk"
        USHER = "usher", "Court Usher"

        # Others
        JUROR = "juror", "Juror"
        WITNESS = "witness", "Witness"
        INTERPRETER = "interpreter", "Interpreter"

        OTHER = "other", "Other"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True
    )
    party_role = models.CharField(
        max_length=50, choices=PartyRole.choices, db_index=True
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["case", "user", "party_role"]
        indexes = [
            models.Index(fields=["case", "party_role"]),
            models.Index(fields=["user", "party_role"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.party_role} in {self.case.case_number}"
