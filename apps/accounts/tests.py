from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationTests(TestCase):
    def test_register_with_email_creates_user_with_hashed_password(self):
        client = Client()
        response = client.post(
            reverse("accounts:register"),
            {
                "email": "new@example.com",
                "phone_number": "",
                "full_name": "New User",
                "password": "Str0ng-Passw0rd!",
                "password_confirm": "Str0ng-Passw0rd!",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="new@example.com")
        self.assertNotEqual(user.password, "Str0ng-Passw0rd!")
        self.assertTrue(user.password.startswith("argon2$"))

    def test_register_requires_email_or_phone(self):
        client = Client()
        response = client.post(
            reverse("accounts:register"),
            {
                "email": "",
                "phone_number": "",
                "password": "Str0ng-Passw0rd!",
                "password_confirm": "Str0ng-Passw0rd!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(full_name="").exists())

    def test_register_rejects_mismatched_passwords(self):
        client = Client()
        response = client.post(
            reverse("accounts:register"),
            {
                "email": "mismatch@example.com",
                "password": "Str0ng-Passw0rd!",
                "password_confirm": "Different-Passw0rd!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="mismatch@example.com").exists())

    def test_register_rejects_weak_password(self):
        client = Client()
        response = client.post(
            reverse("accounts:register"),
            {"email": "weak@example.com", "password": "12345", "password_confirm": "12345"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="weak@example.com").exists())


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="login@example.com", password="Str0ng-Passw0rd!")

    def test_login_with_correct_credentials_succeeds(self):
        client = Client()
        response = client.post(
            reverse("accounts:login"), {"identifier": "login@example.com", "password": "Str0ng-Passw0rd!"}
        )
        self.assertEqual(response.status_code, 302)

    def test_login_with_wrong_password_gives_generic_error(self):
        client = Client()
        response = client.post(
            reverse("accounts:login"), {"identifier": "login@example.com", "password": "wrong-password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "اطلاعات ورود نادرست است")

    def test_login_with_nonexistent_identifier_gives_same_generic_error(self):
        """Enumeration protection: unknown identifier must not reveal that the account doesn't exist."""
        client = Client()
        response = client.post(
            reverse("accounts:login"), {"identifier": "doesnotexist@example.com", "password": "whatever"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "اطلاعات ورود نادرست است")

    def test_session_key_rotates_on_login(self):
        client = Client()
        client.get(reverse("accounts:login"))
        pre_login_key = client.session.session_key
        client.post(
            reverse("accounts:login"), {"identifier": "login@example.com", "password": "Str0ng-Passw0rd!"}
        )
        post_login_key = client.session.session_key
        self.assertNotEqual(pre_login_key, post_login_key)


class DashboardAccessTests(TestCase):
    def test_dashboard_requires_login(self):
        client = Client()
        response = client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_authenticated_user_can_view_dashboard(self):
        User.objects.create_user(email="dash@example.com", password="Str0ng-Passw0rd!")
        client = Client()
        client.login(username="dash@example.com", password="Str0ng-Passw0rd!")
        response = client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)


class CSRFTests(TestCase):
    def test_login_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("accounts:login"), {"identifier": "x@example.com", "password": "whatever"}
        )
        self.assertEqual(response.status_code, 403)
