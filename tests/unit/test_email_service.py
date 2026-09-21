"""Unit tests for EmailService with mocked SMTP servers."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.domain.devices import SMTPSettings
from backend.services.email_service import EmailService, MAX_KINDLE_FILE_SIZE


@pytest.fixture
def sample_book_file(tmp_path: Path) -> Path:
    f = tmp_path / "Foundation.epub"
    f.write_bytes(b"dummy-epub-content-for-testing")
    return f


@pytest.mark.asyncio
async def test_send_book_email_success(sample_book_file: Path):
    settings = SMTPSettings(
        host="smtp.example.com",
        port=587,
        username="user@example.com",
        password="secretpassword",
        sender_email="user@example.com",
        use_tls=True,
    )
    svc = EmailService(smtp_settings=settings)

    mock_smtp = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp):
        await svc.send_book_email(
            recipient="mykindle@kindle.com",
            subject="Foundation",
            file_path=sample_book_file,
            filename="Foundation - Isaac Asimov.epub",
        )

        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user@example.com", "secretpassword")
        mock_smtp.send_message.assert_called_once()
        sent_msg = mock_smtp.send_message.call_args[0][0]
        assert sent_msg["To"] == "mykindle@kindle.com"
        assert sent_msg["From"] == "user@example.com"
        assert sent_msg["Subject"] == "Foundation"


@pytest.mark.asyncio
async def test_send_book_email_missing_sender(sample_book_file: Path):
    settings = SMTPSettings(
        host="smtp.example.com",
        sender_email="",
        username="",
    )
    svc = EmailService(smtp_settings=settings)

    with pytest.raises(ValueError, match="Sender email address is not configured"):
        await svc.send_book_email(
            recipient="mykindle@kindle.com",
            subject="Foundation",
            file_path=sample_book_file,
        )


@pytest.mark.asyncio
async def test_send_book_email_file_size_exceeded(tmp_path: Path):
    large_file = tmp_path / "huge_book.pdf"
    large_file.write_bytes(b"0" * 100)  # small placeholder on disk

    settings = SMTPSettings(sender_email="sender@example.com")
    svc = EmailService(smtp_settings=settings)

    with patch("pathlib.Path.stat") as mock_stat:
        mock_stat_res = MagicMock()
        mock_stat_res.st_size = MAX_KINDLE_FILE_SIZE + 1024
        mock_stat.return_value = mock_stat_res

        with pytest.raises(ValueError, match="exceeds the 50 MB Amazon Kindle limit"):
            await svc.send_book_email(
                recipient="mykindle@kindle.com",
                subject="Huge Book",
                file_path=large_file,
            )


@pytest.mark.asyncio
async def test_test_connection_success():
    settings = SMTPSettings(
        host="smtp.example.com",
        username="user@example.com",
        password="secretpassword",
        use_tls=True,
    )
    svc = EmailService(smtp_settings=settings)

    mock_smtp = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp):
        success = await svc.test_connection(settings)
        assert success is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user@example.com", "secretpassword")
