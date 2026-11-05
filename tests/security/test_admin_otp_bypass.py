"""El admin no se abre sin segundo factor, sea cual sea la ruta de entrada."""

from django.contrib import admin
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django_otp.admin import OTPAdminAuthenticationForm, OTPAdminSite
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.accounts.models import User
from config.admin_site import VocesAdminSite

PASSWORD = "clave-sintetica-123"


class AdminOtpBypassTests(TestCase):
    def setUp(self):
        cache.clear()
        self.index = reverse("admin:index")
        self.login_url = reverse("admin:login")
        self.staff = User.objects.create_superuser("jefa@example.com", "Jefa", PASSWORD)
        self.device = TOTPDevice.objects.create(
            user=self.staff, name="sintetico", confirmed=True
        )

    def creds(self, **extra):
        data = {"username": "jefa@example.com", "password": PASSWORD, "next": self.index}
        data.update(extra)
        return data

    def assert_not_in_admin(self):
        self.assertNotEqual(self.client.get(self.index).status_code, 200)

    def test_site_is_voces_otp_site(self):
        self.assertIsInstance(admin.site, VocesAdminSite)
        self.assertIsInstance(admin.site, OTPAdminSite)
        self.assertEqual(admin.site.name, "admin")
        self.assertIs(admin.site.login_form, OTPAdminAuthenticationForm)

    def test_missing_token_does_not_open_admin(self):
        response = self.client.post(self.login_url, self.creds())
        self.assertEqual(response.status_code, 200)
        self.assert_not_in_admin()

    def test_empty_token_does_not_open_admin(self):
        response = self.client.post(self.login_url, self.creds(otp_token=""))
        self.assertEqual(response.status_code, 200)
        self.assert_not_in_admin()

    def test_wrong_token_does_not_open_admin(self):
        self.client.post(
            self.login_url,
            self.creds(otp_device=self.device.persistent_id, otp_token="000000"),
        )
        self.assert_not_in_admin()

    def test_valid_token_opens_admin(self):
        d = self.device
        token = str(TOTP(d.bin_key, d.step, d.t0, d.digits, d.drift).token())
        response = self.client.post(
            self.login_url,
            self.creds(otp_device=d.persistent_id, otp_token=token.zfill(d.digits)),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(self.index).status_code, 200)

    def test_user_without_device_cannot_enter(self):
        self.device.delete()
        self.client.post(self.login_url, self.creds())
        self.client.post(self.login_url, self.creds(otp_token="123456"))
        self.assert_not_in_admin()

    def test_public_login_does_not_open_admin(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "jefa@example.com", "password": PASSWORD},
        )
        self.assertIn(response.status_code, (200, 302))
        self.assert_not_in_admin()
