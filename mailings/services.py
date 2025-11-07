from django.conf import settings
from django.core.mail import send_mail
from django.utils.timezone import now

from .models import Mailing, MailingAttempt


class MailingSender:
    def __init__(self, mailing: Mailing):
        self.mailing = mailing

    def send(self) -> int:
        recipients = list(self.mailing.recipients.all())
        if not recipients:
            return 0

        self.mailing.mark_running()

        attempts_count = 0
        for recipient in recipients:
            try:
                send_mail(
                    subject=self.mailing.message.subject,
                    message=self.mailing.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )
                status = MailingAttempt.STATUS_SUCCESS
                response = "Отправлено"
            except Exception as exc:  # noqa: BLE001
                status = MailingAttempt.STATUS_FAILED
                response = str(exc)

            MailingAttempt.objects.create(
                mailing=self.mailing,
                recipient=recipient,
                status=status,
                server_response=response,
            )
            attempts_count += 1

        if self.mailing.end_at <= now():
            self.mailing.mark_completed()

        return attempts_count
