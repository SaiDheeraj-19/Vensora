import logging
import os
from abc import abstractmethod
from typing import List, Optional
from app.core.providers.base import BaseProvider, ProviderHealth, HealthState
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class EmailProvider(BaseProvider):
    @abstractmethod
    async def send_email(self, to_addresses: List[str], subject: str, html_body: str) -> bool:
        pass

class SMTPEmailProvider(EmailProvider):
    """
    SMTP-based Email provider for system notifications and employee invitations.
    """
    def __init__(self):
        self.settings = get_settings()
        
        # [REQUIRED FROM COMPANY]
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_address = os.getenv("SMTP_FROM_ADDRESS", "noreply@vensora.example.com")
        
        self.enabled = bool(self.smtp_host and self.smtp_user and self.smtp_password)
        
        if not self.enabled:
            logger.warning("SMTP credentials not fully set. Email running in MOCK mode.")

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled:
            return ProviderHealth(HealthState.MOCK, "SMTP_HOST, SMTP_USER, SMTP_PASSWORD required from company")
            
        try:
            import smtplib
            # Synchronous check, wrapped conceptually for async interface
            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=5)
            server.ehlo()
            if self.smtp_port == 587:
                server.starttls()
            server.quit()
            return ProviderHealth(HealthState.HEALTHY)
        except Exception as e:
            return ProviderHealth(HealthState.UNAVAILABLE, str(e))

    async def send_email(self, to_addresses: List[str], subject: str, html_body: str) -> bool:
        if not self.enabled:
            logger.info(f"MOCK Email: Sent '{subject}' to {to_addresses}")
            return True
            
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_address
            msg["To"] = ", ".join(to_addresses)
            
            part = MIMEText(html_body, "html")
            msg.attach(part)
            
            # Since smtplib is blocking, we should theoretically use aiosmtplib or asyncio.to_thread
            # But we keep it simple for the provider pattern
            import asyncio
            
            def _send():
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                server.ehlo()
                if self.smtp_port == 587:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_address, to_addresses, msg.as_string())
                server.quit()

            await asyncio.to_thread(_send)
            logger.info(f"Email sent successfully to {to_addresses}")
            return True
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False
