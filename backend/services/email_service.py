"""Email delivery service for sending books to e-reader devices via SMTP."""

import asyncio
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
import smtplib
from typing import Optional

from backend.domain.devices import SMTPSettings

MAX_KINDLE_FILE_SIZE = 50 * 1024 * 1024  # 50 MB Amazon limit


class EmailService:
    """Handles asynchronous SMTP connection and book file delivery."""

    def __init__(self, smtp_settings: Optional[SMTPSettings] = None):
        self.smtp_settings = smtp_settings or SMTPSettings()

    def _build_mime_message(
        self,
        sender: str,
        recipient: str,
        subject: str,
        file_path: Path,
        filename: Optional[str] = None,
        body_text: str = "Sent from xBookLibrary.",
    ) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject

        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        attach_name = filename or file_path.name
        file_bytes = file_path.read_bytes()
        part = MIMEApplication(file_bytes, Name=attach_name)
        part["Content-Disposition"] = f'attachment; filename="{attach_name}"'
        msg.attach(part)
        return msg

    def _sync_send(self, settings: SMTPSettings, msg: MIMEMultipart) -> None:
        if settings.use_ssl:
            server = smtplib.SMTP_SSL(settings.host, settings.port, timeout=30)
        else:
            server = smtplib.SMTP(settings.host, settings.port, timeout=30)

        try:
            if not settings.use_ssl and settings.use_tls:
                server.starttls()

            if settings.username and settings.password:
                server.login(settings.username, settings.password)

            server.send_message(msg)
        finally:
            try:
                server.quit()
            except Exception:
                pass

    def _sync_test_connection(self, settings: SMTPSettings) -> bool:
        if settings.use_ssl:
            server = smtplib.SMTP_SSL(settings.host, settings.port, timeout=10)
        else:
            server = smtplib.SMTP(settings.host, settings.port, timeout=10)

        try:
            if not settings.use_ssl and settings.use_tls:
                server.starttls()

            if settings.username and settings.password:
                server.login(settings.username, settings.password)
            return True
        finally:
            try:
                server.quit()
            except Exception:
                pass

    async def send_book_email(
        self,
        recipient: str,
        subject: str,
        file_path: Path,
        filename: Optional[str] = None,
        settings: Optional[SMTPSettings] = None,
    ) -> None:
        """Asynchronously dispatches an e-book attachment to an e-reader email address."""
        active_settings = settings or self.smtp_settings

        if not file_path.exists():
            raise FileNotFoundError(f"Book file does not exist at {file_path}")

        file_size = file_path.stat().st_size
        if file_size > MAX_KINDLE_FILE_SIZE:
            raise ValueError(f"Book file size ({file_size / (1024 * 1024):.1f} MB) exceeds the 50 MB Amazon Kindle limit.")

        sender = active_settings.sender_email or active_settings.username
        if not sender:
            raise ValueError("Sender email address is not configured in SMTP settings.")

        msg = self._build_mime_message(
            sender=sender,
            recipient=recipient,
            subject=subject,
            file_path=file_path,
            filename=filename,
        )

        await asyncio.to_thread(self._sync_send, active_settings, msg)

    async def test_connection(self, settings: Optional[SMTPSettings] = None) -> bool:
        """Tests SMTP server credentials and connectivity."""
        active_settings = settings or self.smtp_settings
        return await asyncio.to_thread(self._sync_test_connection, active_settings)
