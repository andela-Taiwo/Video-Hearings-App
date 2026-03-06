import pylibmagic
import os
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from rest_framework.exceptions import ValidationError
import magic
import hashlib
from utils.logger import get_logger

from .models import HearingDocument


logger = get_logger(__name__)


class AsyncDocumentUploadService:
    """
    Fully asynchronous document upload service with progress tracking
    and WebSocket notifications
    """

    # Upload status constants
    UPLOAD_STATUS = {
        "INITIATED": "initiated",
        "VALIDATING": "validating",
        "SAVING": "saving",
        "PROCESSING": "processing",
        "COMPLETED": "completed",
        "FAILED": "failed",
    }

    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.upload_progress: Dict[str, Dict] = {}

    async def handle_upload(
        self, file_data, filename, metadata: Dict[str, Any], user_id: int
    ) -> Dict[str, Any]:
        """
        Main async upload handler with progress tracking
        """
        upload_id = str(uuid.uuid4())

        try:
            # Initialize upload tracking
            await self._init_upload_tracking(upload_id, filename, metadata)

            # Validate file
            await self._update_status(upload_id, "VALIDATING", 10)
            validation_result = await self._validate_file(file_data, filename)
            if not validation_result["valid"]:
                raise ValidationError(validation_result["error"])

            # Generate secure filename
            await self._update_status(upload_id, "SAVING", 30)
            secure_filename = await self._generate_secure_filename(
                filename, metadata["hearing_id"], user_id
            )

            # Calculate checksum
            checksum = await self._calculate_checksum(file_data)

            # Save file to storage
            await self._update_status(upload_id, "SAVING", 50)
            file_path = await self._save_file_async(
                file_data, secure_filename, metadata["hearing_id"]
            )

            # Create database record
            await self._update_status(upload_id, "SAVING", 70)
            document = await self._create_document_record(
                file_path=file_path,
                original_filename=filename,
                file_size=len(file_data),
                content_type=validation_result["mime_type"],
                checksum=checksum,
                **metadata,
                user_id=user_id,
            )

            await self._update_status(upload_id, "PROCESSING", 90)
            # await self._trigger_processing(document.id)

            # Complete
            await self._update_status(
                upload_id,
                "COMPLETED",
                100,
                {
                    "document_id": document.id,
                    "url": document.file.url if document.file else None,
                },
            )

            return {
                "upload_id": upload_id,
                "document_id": document.id,
                "status": "completed",
                "message": "Document uploaded successfully",
            }

        except ValidationError as e:
            await self._update_status(upload_id, "FAILED", 0, {"error": str(e)})
            logger.error(f"Upload validation error for {upload_id}: {str(e)}")
            raise
        except Exception as e:
            await self._update_status(upload_id, "FAILED", 0, {"error": str(e)})
            logger.error(f"Upload error for {upload_id}: {str(e)}", exc_info=True)
            raise

    async def _init_upload_tracking(
        self, upload_id: str, filename: str, metadata: Dict
    ):
        """Initialize upload progress tracking"""
        self.upload_progress[upload_id] = {
            "filename": filename,
            "status": self.UPLOAD_STATUS["INITIATED"],
            "progress": 0,
            "metadata": metadata,
            "started_at": timezone.now().isoformat(),
            "last_updated": timezone.now().isoformat(),
        }

        # Send initial status via WebSocket
        await self._send_websocket_update(upload_id)

    async def _update_status(
        self, upload_id: str, status_key: str, progress: int, extra_data: Dict = None
    ):
        """Update upload status and send WebSocket notification"""
        if upload_id in self.upload_progress:
            self.upload_progress[upload_id].update(
                {
                    "status": self.UPLOAD_STATUS[status_key],
                    "progress": progress,
                    "last_updated": timezone.now().isoformat(),
                }
            )

            if extra_data:
                self.upload_progress[upload_id].update(extra_data)

            await self._send_websocket_update(upload_id)

    async def _send_websocket_update(self, upload_id: str):
        """Send real-time update via WebSocket"""
        try:
            if self.channel_layer and upload_id in self.upload_progress:
                await self.channel_layer.group_send(
                    f"upload_{upload_id}",
                    {
                        "type": "upload.progress",
                        "data": self.upload_progress[upload_id],
                    },
                )
        except Exception as e:
            logger.error(f"WebSocket update failed: {str(e)}")

    async def _validate_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate file asynchronously
        """
        result = {
            "valid": True,
            "error": None,
            "mime_type": None,
            "size": len(file_data),
        }

        # Check file size
        # [TODO]extract to settings.py
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 100 * 1024 * 1024)
        if len(file_data) > max_size:
            result["valid"] = False
            result["error"] = (
                f"File size exceeds maximum allowed ({max_size // (1024 * 1024)}MB)"
            )
            return result

        # Detect MIME type
        mime_type = magic.from_buffer(file_data[:2048], mime=True)
        result["mime_type"] = mime_type

        # Check allowed types
        # [TODO]extract to settings.py
        allowed_types = getattr(
            settings,
            "ALLOWED_UPLOAD_MIME_TYPES",
            [
                "application/pdf",
                "image/jpeg",
                "image/png",
                "image/tiff",
                "video/mp4",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
            ],
        )

        if mime_type not in allowed_types:
            result["valid"] = False
            result["error"] = f"File type '{mime_type}' not allowed"
            return result

        return result

    async def _generate_secure_filename(
        self, original_name: str, hearing_id: int, user_id: int
    ) -> str:
        """
        Generate secure filename asynchronously
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._generate_secure_filename_sync,
            original_name,
            hearing_id,
            user_id,
        )

    def _generate_secure_filename_sync(
        self, original_name: str, hearing_id: int, user_id: int
    ) -> str:
        """Synchronous filename generation"""
        ext = os.path.splitext(original_name)[1].lower()
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = "".join(
            c for c in os.path.basename(original_name) if c.isalnum() or c in " ._-"
        )[:50]
        return f"{unique_id}_{hearing_id}_{user_id}_{timestamp}_{clean_name}"

    async def _calculate_checksum(
        self, file_data: bytes, algorithm: str = "sha256"
    ) -> str:
        """
        Calculate file checksum asynchronously
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: hashlib.new(algorithm, file_data).hexdigest()
        )

    async def _save_file_async(
        self, file_data: bytes, filename: str, hearing_id: int
    ) -> str:
        """
        Save file to storage asynchronously
        """
        loop = asyncio.get_event_loop()

        # Create path
        now = timezone.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        relative_path = f"hearing_docs/{year}/{month}/{hearing_id}/{filename}"

        # Save in thread pool
        saved_path = await loop.run_in_executor(
            None, lambda: default_storage.save(relative_path, ContentFile(file_data))
        )

        return saved_path

    @database_sync_to_async
    def _create_document_record(self, **kwargs) -> HearingDocument:
        """
        Create database record asynchronously
        """
        return HearingDocument.objects.create(
            hearing_id=kwargs["hearing_id"],
            uploaded_by_id=kwargs["user_id"],
            doc_type=kwargs["doc_type"],
            file=kwargs["file_path"],
            file_name=kwargs["original_filename"],
            file_size=kwargs["file_size"],
            content_type=kwargs["content_type"],
            is_sealed=kwargs.get("is_sealed", False),
            checksum=kwargs["checksum"],
            processing_status="pending",
        )

    async def get_upload_status(self, upload_id: str) -> Optional[Dict]:
        """Get current upload status"""
        return self.upload_progress.get(upload_id)

    async def cancel_upload(self, upload_id: str) -> bool:
        """Cancel an ongoing upload"""
        if upload_id in self.upload_progress:
            self.upload_progress[upload_id]["status"] = self.UPLOAD_STATUS["FAILED"]
            self.upload_progress[upload_id]["error"] = "Upload cancelled by user"
            await self._send_websocket_update(upload_id)
            return True
        return False
