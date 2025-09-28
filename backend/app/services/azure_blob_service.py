"""Azure Blob Storage helper service for storing finalized session recordings."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Optional

from azure.storage.blob import BlobServiceClient, ContentSettings


class AzureBlobStorageService:
    """Uploads finalized audio recordings to Azure Blob Storage with metadata."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        # Default container if none provided
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "recordings")

        self._blob_service_client: Optional[BlobServiceClient] = None
        self._container_client = None

        if self.is_configured:
            try:
                self._blob_service_client = self._create_blob_service_client()
            except Exception as exc:  # pragma: no cover - configuration failures logged for diagnostics
                self.logger.error(f"Failed to initialize Azure BlobServiceClient: {exc}")
                self._blob_service_client = None

    @property
    def is_configured(self) -> bool:
        """Return True when all required configuration settings are available."""
        return bool(self.account_name and self.account_key and self.container_name)

    def _create_blob_service_client(self) -> BlobServiceClient:
        if not self.account_name or not self.account_key:
            raise ValueError("Azure storage account configuration is incomplete")

        account_url = f"https://{self.account_name}.blob.core.windows.net"
        return BlobServiceClient(account_url=account_url, credential=self.account_key)

    def _ensure_container(self):
        if self._container_client is not None:
            return self._container_client

        if not self._blob_service_client:
            raise RuntimeError("Azure BlobServiceClient is unavailable; check configuration")

        container_client = self._blob_service_client.get_container_client(self.container_name)

        try:
            container_client.create_container()
            self.logger.info(f"Created Azure Blob container '{self.container_name}'")
        except Exception as exc:
            # Ignore container already exists errors; re-raise others
            from azure.core.exceptions import ResourceExistsError

            if isinstance(exc, ResourceExistsError):
                pass
            else:  # pragma: no cover - surface unexpected provisioning issues
                raise

        self._container_client = container_client
        return container_client

    async def upload_session_audio(
        self,
        session_id: str,
        wav_bytes: bytes,
        language: Optional[str],
        metadata: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Async wrapper to upload a WAV recording for a session.

        Returns the blob name on success, None when configuration is missing.
        """

        if not self.is_configured:
            self.logger.info("Azure blob storage is not configured; skipping upload")
            return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._upload_session_audio_sync(session_id, wav_bytes, language, metadata or {}),
        )

    # -------------------------
    # Internal helpers
    # -------------------------

    def _upload_session_audio_sync(
        self,
        session_id: str,
        wav_bytes: bytes,
        language: Optional[str],
        metadata: Dict[str, str],
    ) -> str:
        container_client = self._ensure_container()

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
        blob_name = f"recordings/{session_id}_{timestamp}.wav"

        blob_metadata = self._normalize_metadata({
            "session_id": session_id,
            "language": language or "unknown",
            "uploaded_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        })

        content_settings = ContentSettings(content_type="audio/wav")

        container_client.upload_blob(
            name=blob_name,
            data=wav_bytes,
            overwrite=True,
            metadata=blob_metadata,
            content_settings=content_settings,
        )

        self.logger.info(f"Uploaded session recording to Azure blob '{blob_name}' with metadata {blob_metadata}")
        return blob_name

    @staticmethod
    def _normalize_metadata(metadata: Dict[str, Optional[str]]) -> Dict[str, str]:
        """Azure metadata keys must be ASCII alphanumerics or dashes, lowercase recommended."""

        def sanitize_key(key: str) -> str:
            safe = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in key.lower())
            return safe[:1024]

        def sanitize_value(value: Optional[str]) -> str:
            return (value if value is not None else "").strip()[:2048]

        return {sanitize_key(k): sanitize_value(v) for k, v in metadata.items() if k}


# Global instance
azure_blob_service = AzureBlobStorageService()


