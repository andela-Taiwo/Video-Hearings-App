import os
import uuid
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import ValidationError
from ..models import Hearing, HearingParticipant, HearingDocument
from utils.logger import get_logger
from utils.redis_cache import RedisCache
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from courts.models import Courtroom, Court
from cases.models import Case

logger = get_logger(__name__)
User = get_user_model()


class HearingService:
    """Service layer for Hearing business logic"""

    CACHE_TTL = 3600  # 1 hour
    CACHE_PREFIX = "hearing"

    def __init__(self):
        self.cache = RedisCache(prefix=self.CACHE_PREFIX, timeout=self.CACHE_TTL)

    def get_hearing(self, hearing_id):
        """Get hearing"""
        cache_key = f"hearing_{hearing_id}"
        hearing = self.cache.get(cache_key)

        if not hearing:
            try:
                hearing = Hearing.objects.get(id=hearing_id)
                self.cache.set(cache_key, hearing, HearingService.CACHE_TTL)
            except Hearing.DoesNotExist:
                return None

        return hearing

    def get_hearings_by_case(self, case_id):
        """Get all hearings for a case with caching"""
        cache_key = f"case:{case_id}:hearings"

        hearings = self.cache.get(cache_key)
        if hearings is not None:
            return hearings

        hearings = list(
            Hearing.objects.filter(case_id=case_id).order_by("-scheduled_at")
        )
        self.cache.set(cache_key, hearings, 300)
        return hearings

    def invalidate_hearing_cache(self, hearing_id):
        """Invalidate hearing cache"""
        self.cache.invalidate(self.CACHE_PREFIX)

    def create_hearing(self, **kwargs):
        """Create a hearing and add participants

        Args:
            case_id: ID of the case
            courtroom_id: ID of the courtroom
            scheduled_at: Scheduled date/time for hearing
            participants: List of participant dicts with:
                - email: Required, user's email
                - role: Required, participant's role in hearing
                - first_name: Optional, for new users
                - last_name: Optional, for new users
                - phone_number: Optional, for new users
                - bar_number: Optional, for lawyers
                - court_id: Optional, for judges/clerk

        Returns:
            Created Hearing object

        Raises:
            ValidationError: If required data is missing
        """

        participants = kwargs.get("participants", [])
        if not participants:
            raise ValidationError("At least one participant is required")

        with transaction.atomic():
            # Create the hearing
            hearing = Hearing.objects.create(
                case_id=kwargs.get("case_id"),
                courtroom_id=kwargs.get("courtroom_id"),
                scheduled_at=kwargs.get("scheduled_at"),
                status=Hearing.Status.SCHEDULED,
                name=kwargs.get("name"),
                description=kwargs.get("description"),
                hearing_type=kwargs.get("hearing_type"),
            )

            hearing = self.add_participants(hearing, participants)

            logger.info(f"Hearing {hearing.id} created ")

        self.cache.invalidate()

        logger.info(
            f"Hearing {hearing.id} created with {len(participants)} participants "
        )

        return hearing

    def _map_hearing_role_to_profile_role(self, hearing_role):
        """Map hearing participant role to user profile role"""
        role_mapping = {
            "judge": UserProfile.Role.JUDGE,
            "lawyer": UserProfile.Role.LAWYER,
            "defendant": UserProfile.Role.DEFENDANT,
            "prosecutor": UserProfile.Role.PROSECUTOR,
            "witness": UserProfile.Role.WITNESS,
            "clerk": UserProfile.Role.CLERK,
            "public": UserProfile.Role.PUBLIC,
        }
        return role_mapping.get(hearing_role, UserProfile.Role.PUBLIC)

    def _update_user_profile(self, user, data):
        """Update existing user profile with role-specific fields"""
        try:
            profile = user.profile

            # Update role if it's more specific
            new_role = self._map_hearing_role_to_profile_role(data.get("role"))
            if (
                profile.role == UserProfile.Role.PUBLIC
                and new_role != UserProfile.Role.PUBLIC
            ):
                profile.role = new_role

            # Update bar_number for lawyers
            if data.get("bar_number"):
                profile.bar_number = data.get("bar_number")

            # Update court for judges/clerks
            if data.get("court_id"):
                try:
                    court = Court.objects.get(id=data.get("court_id"))
                    profile.court = court
                except Court.DoesNotExist:
                    logger.warning(
                        f"Court with id {data.get('court_id')} not found for user {user.id}"
                    )

            profile.save()
            logger.info(f"Updated profile for user {user.id}")

        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            self._create_user_profile(user, data)

    def add_participants(self, hearing, participants_data, send_invites=True):
        """
        Add participants to a hearing

        Args:
            hearing: Hearing instance
            participants_data: List of participant data dictionaries
            send_invites: Whether to send invitation emails

        Returns:
            Updated hearing instance and stats
        """
        if not isinstance(participants_data, list):
            participants_data = [participants_data]

        stats = {"created": 0, "existing": 0, "failed": 0, "participants": []}

        participant_objects = []
        for index, participant_data in enumerate(participants_data):
            try:
                result = self._process_single_participant(hearing, participant_data)

                if result and result.get("participant"):
                    participant_objects.append(result["participant"])
                    stats[result["status"]] += 1
                    stats["participants"].append(
                        {
                            "email": result["email"],
                            "role": result["role"],
                            "status": result["status"],
                            "user_id": result["user_id"],
                        }
                    )
            except Exception as e:
                stats["failed"] += 1
                logger.error(f"Failed to add participant {index}: {str(e)}")
                if len(participants_data) == 1:
                    raise ValidationError(str(e))

        # Invalidate cache
        self.cache.invalidate()

        logger.info(
            f"Added {len(participant_objects)} participants to hearing {hearing.id}. "
            f"Stats: {stats}"
        )

        return hearing

    def _process_single_participant(self, hearing, participant_data):
        """Process a single participant"""

        email = participant_data.get("email", "").lower().strip()
        if not email:
            raise ValidationError("Email is required for participant")

        role = participant_data.get("role")
        if not role:
            raise ValidationError("Role is required for participant")

        # Get or create user
        user = User.objects.filter(email=email).first()
        status = "existing"

        if not user:
            # Create new user
            user = self._create_new_user(participant_data)
            status = "created"

            # Create user profile with role-specific fields
            self._create_user_profile(user, participant_data)
        else:
            # Update existing user profile if needed
            self._update_user_profile(user, participant_data)

        # Add participant to hearing
        participant = self._add_participant(
            hearing,
            {
                "email": email,
                "role": role,
                "user": user,  # Pass the user object directly
                "send_invite": participant_data.get("send_invite", True),
            },
        )

        return {
            "participant": participant,
            "status": status,
            "email": email,
            "role": role,
            "user_id": user.id,
        }

    def _create_new_user(self, data):
        """Create a new user from participant data"""
        return User.objects.create_user(
            email=data["email"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            phone_number=data.get("phone_number", ""),
            is_active=True,
            is_verified=False,
            is_email_verified=False,
            is_admin_approved=False,
        )

    def _create_user_profile(self, user, data):
        """Create user profile with role-specific fields"""
        role = self._map_hearing_role_to_profile_role(data.get("role"))

        profile_data = {"user": user, "role": role}

        # Add bar number for lawyers
        if data.get("bar_number"):
            profile_data["bar_number"] = data["bar_number"]

        # Add court for judges/clerks
        if data.get("court_id"):
            try:
                court = Court.objects.get(id=data["court_id"])
                profile_data["court"] = court
            except Court.DoesNotExist:
                logger.warning(
                    f"Court with id {data['court_id']} not found, skipping court assignment"
                )

        # Add specialization if provided
        if data.get("specialization"):
            profile_data["specialization"] = data["specialization"]

        try:
            profile = UserProfile.objects.create(**profile_data)
            return profile
        except ValidationError as e:
            logger.error(f"Profile validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Profile validation error: {str(e)}")
            raise

    def _map_hearing_role_to_profile_role(self, hearing_role):
        """Map hearing role to profile role"""
        mapping = {
            "judge": "judge",
            "magistrate": "judge",
            "defendant": "defendant",
            "prosecutor": "prosecutor",
            "defence_counsel": "lawyer",
            "prosecution_counsel": "lawyer",
            "claimant_counsel": "lawyer",
            "solicitor": "lawyer",
            "barrister": "lawyer",
            "witness": "witness",
            "juror": "public",
            "clerk": "clerk",
            "usher": "public",
            "claimant": "public",
            "respondent": "public",
            "other": "public",
        }
        return mapping.get(hearing_role, "public")

    def _send_participant_invitations(self, participants):
        """Send invitation emails to participants"""
        for participant in participants:
            # Implement your email sending logic here
            # e.g., send_participant_invitation.delay(participant.id)
            pass

    def remove_participants(
        self,
        hearing_id,
        participant_ids=None,
        participant_emails=None,
        roles=None,
        user_ids=None,
    ):
        """
        Remove participants from a hearing.

        Args:
            hearing_id: ID of the hearing
            participant_ids: Optional list of specific participant IDs to remove
            participant_emails: Optional list of participant emails to remove
            roles: Optional list of roles to remove
            user_ids: Optional list of user IDs to remove

        Returns:
            Dictionary with removal statistics
        """
        from django.db.models import Q

        # Get the hearing or raise 404
        try:
            hearing = Hearing.objects.get(id=hearing_id)
        except Hearing.DoesNotExist:
            raise ValidationError(f"Hearing with id {hearing_id} does not exist")

        # Build the filter for participants to remove
        filter_q = Q(hearing=hearing)

        if participant_ids:
            filter_q &= Q(id__in=participant_ids)

        if participant_emails:
            filter_q &= Q(
                user__email__in=[email.lower().strip() for email in participant_emails]
            )

        if roles:
            filter_q &= Q(role__in=roles)

        if user_ids:
            filter_q &= Q(user_id__in=user_ids)

        # If no criteria specified, don't remove anything
        if not any([participant_ids, participant_emails, roles, user_ids]):
            return {
                "success": False,
                "message": "No removal criteria specified",
                "removed_count": 0,
                "removed_participants": [],
            }

        # Get participants to be removed
        participants_to_remove = HearingParticipant.objects.filter(filter_q)
        removed_count = participants_to_remove.count()

        if removed_count == 0:
            return {
                "success": True,
                "message": "No matching participants found to remove",
                "removed_count": 0,
                "removed_participants": [],
            }

        # Store participant info for response before deletion
        removed_participants = list(
            participants_to_remove.values(
                "id",
                "user__id",
                "user__email",
                "user__first_name",
                "user__last_name",
                "role",
            )
        )

        # Delete the participants
        participants_to_remove.delete()

        # Invalidate cache
        self.cache.invalidate()

        logger.info(
            f"Removed {removed_count} participants from hearing {hearing_id}: "
            f"{[p['user__email'] for p in removed_participants]}"
        )

        return {
            "success": True,
            "message": f"Successfully removed {removed_count} participant(s)",
            "removed_count": removed_count,
            "removed_participants": removed_participants,
        }

    def _queue_schedule_email(self, user):
        """Queue sendd email for meeting partticipants"""
        # send hearing schedule email
        pass

    @staticmethod
    def generate_participant_tokens(hearing):
        """Generate join tokens for all participants"""
        participants = hearing.participants.all()
        for participant in participants:
            if not participant.join_token:
                participant.join_token = uuid.uuid4()
                participant.save()

    def delete_hearing(self, hearing_id, soft_delete=True):
        """Soft delete by default"""
        hearing = Hearing.objects.get(id=hearing_id)
        if soft_delete:
            hearing.status = "cancelled"
            hearing.save()
        else:
            hearing.delete()
        return hearing

    def reschedule_hearing(self, hearing_id, new_time, reason=""):
        hearing = Hearing.objects.get(id=hearing_id)
        hearing.scheduled_at = new_time
        hearing.save()
        # Log rescheduling reason
        if reason:
            logger.info(f"Hearing scheduled for the: {reason}")
        logger.info(f"Hearing scheduled successfully")
        return hearing

    def cancel_hearing(self, hearing_id, reason=""):
        hearing = Hearing.objects.get(id=hearing_id)
        hearing.status = "cancelled"
        hearing.save()
        return hearing

    def get_upcoming_hearings(self, days=7):
        end_date = timezone.now() + timedelta(days=days)
        return Hearing.objects.filter(
            scheduled_at__gte=timezone.now(),
            scheduled_at__lte=end_date,
            status="scheduled",
        ).order_by("scheduled_at")

    def get_hearings_by_date_range(self, start_date, end_date):
        return Hearing.objects.filter(
            scheduled_at__date__gte=start_date, scheduled_at__date__lte=end_date
        ).order_by("scheduled_at")

    @transaction.atomic
    def update_hearing(self, hearing_id, user=None, **data):
        """
        Update an existing hearing with comprehensive validation and side effects

        Args:
            hearing_id: ID of the hearing to update
            user: User performing the update (for audit)
            **data: Fields to update including:
                - case_id: New case ID
                - courtroom_id: New courtroom ID
                - scheduled_at: New scheduled time
                - hearing_type: Type of hearing
                - status: New status
                - notes: Additional notes
                - metadata: JSON metadata
                - name: Hearing name/title
                - participants: Participant changes
                - completion_notes: Notes for completion
                - cancellation_reason: Reason for cancellation
                - postponement_reason: Reason for postponement

        Returns:
            Updated Hearing instance

        Raises:
            ValidationError: If validation fails
        """
        try:
            hearing = (
                Hearing.objects.select_related("case", "courtroom")
                .prefetch_related("participants__user")
                .get(id=hearing_id)
            )
        except Hearing.DoesNotExist:
            raise ValidationError(f"Hearing with id {hearing_id} does not exist")

        # Validate status transition
        new_status = data.get("status", hearing.status)
        self._validate_status_transition(hearing.status, new_status, data)

        # Check if courtroom is available if changing time or courtroom
        if "courtroom_id" in data or "scheduled_at" in data:
            self._validate_courtroom_availability(
                courtroom_id=data.get("courtroom_id", hearing.courtroom_id),
                scheduled_at=data.get("scheduled_at", hearing.scheduled_at),
                exclude_hearing_id=hearing.id,
            )

        # Validate case exists if changing
        if "case_id" in data:
            if not Case.objects.filter(id=data["case_id"]).exists():
                raise ValidationError(f"Case with id {data['case_id']} does not exist")

        # Validate courtroom exists if changing
        if "courtroom_id" in data:
            if not Courtroom.objects.filter(id=data["courtroom_id"]).exists():
                raise ValidationError(
                    f"Courtroom with id {data['courtroom_id']} does not exist"
                )

        # Handle participant updates if provided
        if "participants" in data:
            participants_data = data.pop("participants")
            self._update_participants(hearing, participants_data)

        # Handle special status transitions
        if new_status == "completed" and hearing.status != "completed":
            hearing.completed_at = timezone.now()

        if new_status == "cancelled" and hearing.status != "cancelled":
            hearing.status = "canceled"

        if new_status == "postponed" and hearing.status != "postponed":
            new_time = data.get("new_scheduled_at") or data.get("scheduled_at")
            if not new_time:
                raise ValidationError("New scheduled time is required for postponement")

            hearing.scheduled_at = new_time

        # Update basic fields
        updatable_fields = [
            "case_id",
            "courtroom_id",
            "scheduled_at",
            "hearing_type",
            "notes",
            "metadata",
            "name",
        ]

        for field in updatable_fields:
            if field in data and data[field] is not None:
                setattr(hearing, field, data[field])

        # Update status if provided
        if "status" in data:
            hearing.status = data["status"]

        # Save the hearing
        hearing.save()

        # Clear cache
        self.cache.delete(f"hearing_{hearing_id}")

        # [TODO] send notificatiosn

        return hearing

    def _validate_status_transition(self, current_status, new_status, data):
        """Validate if status transition is allowed"""
        # Cannot change completed or cancelled hearings
        if (
            current_status in ["completed", "cancelled"]
            and new_status != current_status
        ):
            raise ValidationError(f"Cannot change status of a {current_status} hearing")

        # Specific transition validations
        if new_status == "completed" and current_status != "in_progress":
            raise ValidationError(
                "Only hearings 'in_progress' can be marked as completed"
            )

        if new_status == "cancelled" and current_status in ["completed"]:
            raise ValidationError(
                f"Cannot cancel a hearing that is already {current_status}"
            )

        if new_status == "postponed":
            if not data.get("new_scheduled_at") and not data.get("scheduled_at"):
                raise ValidationError(
                    "New scheduled time is required when postponing a hearing"
                )

    def _validate_courtroom_availability(
        self, courtroom_id, scheduled_at, exclude_hearing_id=None
    ):
        """Check if courtroom is available at the given time"""
        # Allow buffer time between hearings (e.g., 30 minutes)
        time_buffer = timedelta(minutes=30)
        buffer_start = scheduled_at - time_buffer
        buffer_end = scheduled_at + time_buffer

        # Check for conflicting hearings
        conflicting = Hearing.objects.filter(
            courtroom_id=courtroom_id,
            scheduled_at__range=[buffer_start, buffer_end],
            status__in=["scheduled", "in_progress"],
        ).exclude(status="cancelled")

        if exclude_hearing_id:
            conflicting = conflicting.exclude(id=exclude_hearing_id)

        if conflicting.exists():
            hearing = conflicting.first()
            raise ValidationError(
                f"Courtroom is not available at {scheduled_at}. "
                f"Conflicts with hearing ID {hearing.id} scheduled at {hearing.scheduled_at}"
            )

    def _update_participants(self, hearing, participants_data):
        """Handle participant updates (add, update, remove)"""
        for participant_op in participants_data:
            action = participant_op.get("action", "add")

            if action == "add":
                self._add_participant(hearing, participant_op)

            elif action == "update":
                self._update_participant(hearing, participant_op)

            elif action == "remove":
                self._remove_participant(hearing, participant_op)

    def _add_participant(self, hearing, participant_data):
        """
        Add a new participant to the hearing

        Args:
            hearing: Hearing instance
            participant_data: Dictionary containing:
                - user: User instance (required)
                - role: Participant role (required)
                - email: Email (for logging)
                - send_invite: Whether to send invitation
        """

        user = participant_data.get("user")
        role = participant_data.get("role")
        email = participant_data.get("email")
        send_invite = participant_data.get("send_invite", True)

        if not user or not role:
            raise ValidationError("User and role are required")

        # Check if participant already exists
        existing_participant = HearingParticipant.objects.filter(
            hearing=hearing, user=user
        ).first()

        if existing_participant:
            print(
                f"Participant already exists: {user.email} with role {existing_participant.role}"
            )

            # Update role if different
            if existing_participant.role != role:
                existing_participant.role = role
                existing_participant.save(update_fields=["role"])
                print(f"Updated participant role to {role}")

            return existing_participant

        # Create new participant
        try:
            participant = HearingParticipant.objects.create(
                hearing=hearing, user=user, role=role, join_token=uuid.uuid4()
            )

            print(
                f"Created participant: {participant.id} for user {user.email} with role {role}"
            )

            # [TODO] email notificatiob
            # Send invitation if required
            # if send_invite:
            #     self._send_participant_invite(participant)

            return participant

        except Exception as e:
            print(f"Error creating participant: {e}")
            import traceback

            traceback.print_exc()
            raise ValidationError(f"Failed to create participant: {str(e)}")

    def _update_participant(self, hearing, participant_data):
        """Update an existing participant"""
        participant_id = participant_data.get("id")
        if not participant_id:
            raise ValidationError("Participant ID is required for update action")

        try:
            participant = HearingParticipant.objects.get(
                id=participant_id, hearing=hearing
            )
        except HearingParticipant.DoesNotExist:
            raise ValidationError(f"Participant with id {participant_id} not found")

        # Update fields
        if "role" in participant_data:
            participant.role = participant_data["role"]

        participant.save()

    def _remove_participant(self, hearing, participant_data):
        """Remove a participant from the hearing"""
        participant_id = participant_data.get("id")
        if not participant_id:
            raise ValidationError("Participant ID is required for remove action")

        HearingParticipant.objects.filter(id=participant_id, hearing=hearing).delete()
