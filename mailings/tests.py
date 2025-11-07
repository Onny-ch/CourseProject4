from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import MailingForm
from .models import Mailing, MailingAttempt, Message, Recipient
from .services import MailingSender

User = get_user_model()


class MailingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com", password="ComplexPass123", is_active=True
        )
        self.message = Message.objects.create(
            subject="Subject", body="Body", owner=self.user
        )
        self.recipient = Recipient.objects.create(
            email="client@example.com", full_name="Client", comment="", owner=self.user
        )

    def _create_mailing(self):
        mailing = Mailing.objects.create(
            start_at=timezone.now(),
            end_at=timezone.now() + timezone.timedelta(hours=1),
            message=self.message,
            owner=self.user,
        )
        mailing.recipients.add(self.recipient)
        return mailing

    def test_mailing_status_helpers(self):
        mailing = self._create_mailing()
        self.assertEqual(mailing.status, Mailing.STATUS_CREATED)
        mailing.mark_running()
        self.assertEqual(mailing.status, Mailing.STATUS_RUNNING)
        mailing.mark_completed()
        self.assertEqual(mailing.status, Mailing.STATUS_COMPLETED)

    @patch("mailings.services.send_mail", return_value=1)
    def test_mailing_sender_success(self, mocked_send_mail):
        mailing = self._create_mailing()
        sender = MailingSender(mailing)
        attempts = sender.send()

        self.assertEqual(attempts, 1)
        mocked_send_mail.assert_called_once()
        self.assertEqual(mailing.attempts.count(), 1)
        attempt = mailing.attempts.first()
        self.assertEqual(attempt.status, MailingAttempt.STATUS_SUCCESS)

    @patch("mailings.services.send_mail", side_effect=Exception("SMTP error"))
    def test_mailing_sender_failure(self, mocked_send_mail):
        mailing = self._create_mailing()
        sender = MailingSender(mailing)
        attempts = sender.send()

        self.assertEqual(attempts, 1)
        self.assertEqual(mailing.attempts.first().status, MailingAttempt.STATUS_FAILED)
        mocked_send_mail.assert_called_once()


class MailingViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="owner@example.com", password="ComplexPass123", is_active=True
        )
        self.message = Message.objects.create(
            subject="Subject", body="Body", owner=self.user
        )
        self.recipient = Recipient.objects.create(
            email="client@example.com", full_name="Client", comment="", owner=self.user
        )
        self.client.login(username="owner@example.com", password="ComplexPass123")

    def test_home_view_statistics(self):
        mailing = Mailing.objects.create(
            start_at=timezone.now(),
            end_at=timezone.now() + timezone.timedelta(hours=1),
            status=Mailing.STATUS_RUNNING,
            message=self.message,
            owner=self.user,
        )
        mailing.recipients.add(self.recipient)

        cache.clear()
        response = self.client.get(reverse("mailings:home"))
        self.assertContains(response, "Всего рассылок")
        self.assertContains(response, 'display-6">1</p>', count=3)

    def test_create_mailing_view_sets_owner(self):
        start_at = (timezone.now() + timezone.timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        end_at = (timezone.now() + timezone.timedelta(hours=2)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        response = self.client.post(
            reverse("mailings:mailing_create"),
            data={
                "start_at": start_at,
                "end_at": end_at,
                "status": Mailing.STATUS_CREATED,
                "message": self.message.pk,
                "recipients": [self.recipient.pk],
            },
        )
        self.assertRedirects(response, reverse("mailings:mailing_list"))
        mailing = Mailing.objects.get()
        self.assertEqual(mailing.owner, self.user)

    def test_mailing_attempt_list_filtered_for_owner(self):
        other_user = User.objects.create_user(
            email="other@example.com", password="ComplexPass123", is_active=True
        )
        mailing = Mailing.objects.create(
            start_at=timezone.now(),
            end_at=timezone.now() + timezone.timedelta(hours=1),
            message=self.message,
            owner=other_user,
        )
        mailing.recipients.add(self.recipient)
        MailingAttempt.objects.create(
            mailing=mailing,
            recipient=self.recipient,
            status=MailingAttempt.STATUS_SUCCESS,
            server_response="OK",
        )

        response = self.client.get(reverse("mailings:attempt_list"))
        self.assertContains(response, "Попытки отсутствуют")


class MailingFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com", password="ComplexPass123", is_active=True
        )
        self.message = Message.objects.create(
            subject="Subject", body="Body", owner=self.user
        )
        self.recipient = Recipient.objects.create(
            email="client@example.com", full_name="Client", comment="", owner=self.user
        )

    def test_clean_validates_dates(self):
        form = MailingForm(
            data={
                "start_at": (timezone.now() + timezone.timedelta(hours=2)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "end_at": (timezone.now() + timezone.timedelta(hours=1)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "status": Mailing.STATUS_CREATED,
                "message": self.message.pk,
                "recipients": [self.recipient.pk],
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Дата окончания должна быть позже даты начала", form.errors["end_at"]
        )
