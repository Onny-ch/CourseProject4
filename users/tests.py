from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.tokens import default_token_generator
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from mailings.models import Mailing, MailingAttempt, Message, Recipient

User = get_user_model()


class UserManagerTests(TestCase):
    def test_create_user_requires_email(self):
        with self.assertRaisesMessage(ValueError, "Email обязателен для регистрации"):
            User.objects.create_user(email="", password="pass12345")

    def test_create_user_and_superuser_flags(self):
        user = User.objects.create_user(email="user@example.com", password="pass12345")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        superuser = User.objects.create_superuser(
            email="admin@example.com", password="pass12345"
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


class RegistrationFlowTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_registration_creates_active_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("users:register"),
            data={
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "User",
                "password1": "ComplexPass123",
                "password2": "ComplexPass123",
            },
        )
        self.assertRedirects(response, reverse("users:login"))
        user = User.objects.get(email="new@example.com")
        self.assertTrue(user.is_active)

    def test_confirm_email_activates_user(self):
        user = User.objects.create_user(
            email="inactive@example.com", password="pass12345", is_active=False
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.get(reverse("users:confirm_email", args=[uid, token]))
        self.assertRedirects(response, reverse("users:login"))
        user.refresh_from_db()
        self.assertTrue(user.is_active)


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "ComplexPass123"
        self.user = User.objects.create_user(
            email="login@example.com", password=self.password, is_active=True
        )

    def test_login_with_email(self):
        response = self.client.post(
            reverse("users:login"),
            data={"username": self.user.email, "password": self.password},
        )
        self.assertRedirects(response, reverse("users:profile"))


class ProfileAndManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="owner@example.com", password="ComplexPass123", is_active=True
        )
        self.client.login(username=self.user.email, password="ComplexPass123")

    def test_profile_context_contains_statistics(self):
        message = Message.objects.create(
            subject="Subject", body="Body", owner=self.user
        )
        recipient = Recipient.objects.create(
            email="client@example.com",
            full_name="Client",
            comment="",
            owner=self.user,
        )
        mailing = Mailing.objects.create(
            start_at=timezone.now(),
            end_at=timezone.now() + timezone.timedelta(hours=2),
            status=Mailing.STATUS_CREATED,
            message=message,
            owner=self.user,
        )
        mailing.recipients.add(recipient)
        MailingAttempt.objects.create(
            mailing=mailing,
            recipient=recipient,
            status=MailingAttempt.STATUS_SUCCESS,
            server_response="OK",
        )

        response = self.client.get(reverse("users:profile"))
        self.assertContains(response, "Рассылок")
        self.assertEqual(response.context["mailings_count"], 1)
        self.assertEqual(response.context["attempts_success"], 1)

    def test_manager_can_block_user(self):
        manager = User.objects.create_user(
            email="manager@example.com", password="ComplexPass123", is_active=True
        )
        permissions = Permission.objects.filter(
            codename__in=["change_user", "view_user"]
        )
        manager.user_permissions.add(*permissions)
        self.client.logout()
        self.client.login(username="manager@example.com", password="ComplexPass123")

        target = User.objects.create_user(
            email="target@example.com", password="ComplexPass123", is_active=True
        )
        response = self.client.post(reverse("users:user_block", args=[target.pk]))
        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertFalse(target.is_active)
