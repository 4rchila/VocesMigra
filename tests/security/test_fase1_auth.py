"""Fase 1, tareas 1.1–1.3: límite de intentos, registro sin enumeración y admin con 2FA."""

import re

from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.accounts import ratelimit
from apps.accounts.models import User

PASSWORD = "clave-sintetica-123"
NEW_PASSWORD = "Otra-clave-sintetica-456"
REAL_LIMITS = override_settings(RATELIMITS=ratelimit.DEFAULT_RATELIMITS)


def registration_data(**overrides):
    data = {
        "email": "nueva@example.com",
        "alias": "NuevaCuenta",
        "password1": NEW_PASSWORD,
        "password2": NEW_PASSWORD,
    }
    data.update(overrides)
    return data


@REAL_LIMITS
class LoginRateLimitTests(TestCase):
    url = reverse("accounts:login")

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("cuenta@example.com", "CuentaUno", PASSWORD)

    def fail(self, email="cuenta@example.com", ip="198.51.100.7"):
        return self.client.post(
            self.url, {"username": email, "password": "mal"}, REMOTE_ADDR=ip
        )

    def test_blocks_after_five_failures_even_with_correct_password(self):
        for _ in range(5):
            self.assertEqual(self.fail().status_code, 200)
        response = self.client.post(
            self.url,
            {"username": "cuenta@example.com", "password": PASSWORD},
            REMOTE_ADDR="198.51.100.7",
        )
        self.assertEqual(response.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_lock_is_per_ip_so_victim_can_still_log_in(self):
        for _ in range(5):
            self.fail()
        response = self.client.post(
            self.url,
            {"username": "cuenta@example.com", "password": PASSWORD},
            REMOTE_ADDR="203.0.113.9",
        )
        self.assertEqual(response.status_code, 302)

    def test_same_response_for_existing_and_unknown_account(self):
        for _ in range(5):
            self.fail(email="nadie@example.com")
        self.assertEqual(self.fail(email="nadie@example.com").status_code, 429)

    def test_ip_limit_covers_many_accounts(self):
        for i in range(20):
            self.fail(email=f"otro{i}@example.com")
        self.assertEqual(self.fail(email="nuevo@example.com").status_code, 429)

    def test_success_resets_account_counter(self):
        for _ in range(4):
            self.fail()
        self.client.post(
            self.url,
            {"username": "cuenta@example.com", "password": PASSWORD},
            REMOTE_ADDR="198.51.100.7",
        )
        self.client.post(reverse("accounts:logout"))
        for _ in range(4):
            self.assertEqual(self.fail().status_code, 200)

    def test_cache_keys_do_not_contain_email_or_ip(self):
        key = ratelimit._key("login-account-ip", "cuenta@example.com", "198.51.100.7")
        self.assertNotIn("cuenta", key)
        self.assertNotIn("198.51", key)


@REAL_LIMITS
class RegisterRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_blocks_sixth_registration_from_same_ip(self):
        url = reverse("accounts:register")
        for i in range(5):
            self.client.post(
                url,
                registration_data(email=f"n{i}@example.com", alias=f"Nueva{i}"),
                REMOTE_ADDR="198.51.100.7",
            )
        response = self.client.post(
            url,
            registration_data(email="n9@example.com", alias="Nueva9"),
            REMOTE_ADDR="198.51.100.7",
        )
        self.assertEqual(response.status_code, 429)
        self.assertFalse(User.objects.filter(email="n9@example.com").exists())


class ClientIpTests(TestCase):
    def request(self, xff):
        return RequestFactory().get("/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR=xff)

    @override_settings(TRUSTED_PROXY_COUNT=0)
    def test_ignores_forwarded_header_without_trusted_proxy(self):
        self.assertEqual(ratelimit.client_ip(self.request("1.2.3.4")), "10.0.0.1")

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_spoofed_first_entry_is_ignored_behind_one_proxy(self):
        request = self.request("6.6.6.6, 198.51.100.7")
        self.assertEqual(ratelimit.client_ip(request), "198.51.100.7")


class RegistrationWithoutEnumerationTests(TestCase):
    url = reverse("accounts:register")
    OWNER_PASSWORD = "Clave-de-la-duena-789"

    def chosen_password(self):
        return {"new_password1": self.OWNER_PASSWORD, "new_password2": self.OWNER_PASSWORD}

    def activation_path(self, index=0):
        link = re.search(r"https?://\S+/activar/\S+", mail.outbox[index].body).group(0)
        return link.split("testserver", 1)[1]

    def test_preregistration_password_is_discarded_on_activation(self):
        # Ataque: alguien registra el correo de la víctima con su contraseña A.
        self.client.post(self.url, registration_data(password1="Atacante-A-123", password2="Atacante-A-123"))
        victim = self.client_class()
        response = victim.post(self.activation_path(), self.chosen_password())
        self.assertEqual(response.status_code, 302)
        attacker = self.client_class()
        response = attacker.post(
            reverse("accounts:login"),
            {"username": "nueva@example.com", "password": "Atacante-A-123"},
        )
        self.assertNotIn("_auth_user_id", attacker.session)
        user = User.objects.get(email="nueva@example.com")
        self.assertFalse(user.check_password("Atacante-A-123"))
        self.assertTrue(user.check_password(self.OWNER_PASSWORD))

    def test_activation_requires_valid_matching_password(self):
        self.client.post(self.url, registration_data())
        response = self.client.post(
            self.activation_path(), {"new_password1": "12345678", "new_password2": "12345678"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.get(email="nueva@example.com").is_active)

    def test_activation_page_shows_alias_to_the_owner(self):
        self.client.post(self.url, registration_data())
        self.assertContains(self.client.get(self.activation_path()), "NuevaCuenta")

    def test_new_and_existing_email_get_identical_response(self):
        User.objects.create_user("usada@example.com", "Usada", PASSWORD)
        new = self.client.post(self.url, registration_data())
        dup = self.client.post(
            self.url, registration_data(email="USADA@example.com", alias="OtroAlias")
        )
        self.assertEqual(new.status_code, dup.status_code)
        self.assertEqual(new["Location"], dup["Location"])
        done = self.client.get(new["Location"])
        self.assertContains(done, "Revisa tu correo")

    def test_owner_of_existing_email_gets_notice_not_activation(self):
        User.objects.create_user("usada@example.com", "Usada", PASSWORD)
        self.client.post(self.url, registration_data(email="usada@example.com", alias="Otro"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["usada@example.com"])
        self.assertIn("ya tienes una", mail.outbox[0].body)
        self.assertNotIn("/activar/", mail.outbox[0].body)
        self.assertEqual(User.objects.count(), 1)

    def test_activation_link_activates_once_and_logs_in(self):
        self.client.post(self.url, registration_data())
        link = re.search(r"https?://\S+/activar/\S+", mail.outbox[0].body).group(0)
        path = link.split("testserver", 1)[1]

        self.assertEqual(self.client.get(path).status_code, 200)
        user = User.objects.get(email="nueva@example.com")
        self.assertFalse(user.is_active, "GET no debe activar la cuenta")

        response = self.client.post(path, self.chosen_password())
        self.assertRedirects(response, reverse("accounts:profile"), fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

        self.client.post(reverse("accounts:logout"))
        self.assertEqual(self.client.post(path, self.chosen_password()).status_code, 400)

    def test_tampered_token_is_rejected(self):
        self.client.post(self.url, registration_data())
        link = re.search(r"/cuenta/activar/[^/]+/", mail.outbox[0].body).group(0)
        self.assertEqual(
            self.client.post(link + "token-falso/", self.chosen_password()).status_code, 400
        )
        self.assertFalse(User.objects.get(email="nueva@example.com").is_active)

    def test_unactivated_account_cannot_log_in_and_gets_generic_error(self):
        self.client.post(self.url, registration_data())
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "nueva@example.com", "password": NEW_PASSWORD},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Correo o contraseña incorrectos.")

    def test_re_registering_unactivated_email_resends_activation(self):
        self.client.post(self.url, registration_data())
        self.client.post(self.url, registration_data(alias="OtroAlias"))
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("/activar/", mail.outbox[1].body)
        self.assertEqual(User.objects.count(), 1)


class AdminTwoFactorTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin_index = reverse("admin:index")
        self.staff = User.objects.create_superuser("jefa@example.com", "Jefa", PASSWORD)

    def test_default_admin_path_is_404(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)
        self.assertEqual(self.admin_index, "/" + settings.ADMIN_URL)

    def test_password_alone_does_not_open_admin(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.admin_index)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_password_plus_totp_opens_admin(self):
        device = TOTPDevice.objects.create(user=self.staff, name="sintetico", confirmed=True)
        totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
        response = self.client.post(
            reverse("admin:login"),
            {
                "username": "jefa@example.com",
                "password": PASSWORD,
                "otp_device": device.persistent_id,
                "otp_token": str(totp.token()).zfill(device.digits),
                "next": self.admin_index,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(self.admin_index).status_code, 200)

    def test_wrong_totp_is_rejected(self):
        device = TOTPDevice.objects.create(user=self.staff, name="sintetico", confirmed=True)
        response = self.client.post(
            reverse("admin:login"),
            {
                "username": "jefa@example.com",
                "password": PASSWORD,
                "otp_device": device.persistent_id,
                "otp_token": "000000",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(self.admin_index).status_code, 302)

    @REAL_LIMITS
    def test_admin_login_is_rate_limited(self):
        for _ in range(5):
            self.client.post(reverse("admin:login"), {"username": "x@example.com", "password": "mal"})
        response = self.client.post(
            reverse("admin:login"), {"username": "jefa@example.com", "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 429)


class PurgeUnactivatedAccountsTests(TestCase):
    def test_deletes_only_expired_never_used_inactive_accounts(self):
        from datetime import timedelta

        from django.core.management import call_command
        from django.utils import timezone

        old = timezone.now() - timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT + 60)
        stale = User.objects.create_user("vieja@example.com", "Vieja", PASSWORD, is_active=False)
        fresh = User.objects.create_user("fresca@example.com", "Fresca", PASSWORD, is_active=False)
        banned = User.objects.create_user("baneada@example.com", "Baneada", PASSWORD, is_active=False)
        User.objects.filter(pk__in=[stale.pk, banned.pk]).update(date_joined=old)
        User.objects.filter(pk=banned.pk).update(last_login=old)

        call_command("purge_unactivated_accounts", stdout=open("/dev/null", "w"))

        remaining = set(User.objects.values_list("email", flat=True))
        self.assertEqual(remaining, {"fresca@example.com", "baneada@example.com"})


class VercelAndAliasTests(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(CLIENT_IP_HEADER="HTTP_X_VERCEL_FORWARDED_FOR", TRUSTED_PROXY_COUNT=1)
    def test_client_ip_prefers_provider_header_over_spoofable_xff(self):
        from django.test import RequestFactory

        from apps.accounts.ratelimit import client_ip

        request = RequestFactory().get(
            "/", HTTP_X_FORWARDED_FOR="6.6.6.6", HTTP_X_VERCEL_FORWARDED_FOR="203.0.113.7"
        )
        self.assertEqual(client_ip(request), "203.0.113.7")

    @override_settings(RATELIMITS={"login-account": (3, 3600), "login-ip": (100, 900), "login-account-ip": (100, 900)}, TRUSTED_PROXY_COUNT=1, CLIENT_IP_HEADER="")
    def test_global_account_limit_blocks_attempts_spread_over_ips(self):
        User.objects.create_user("victima@example.com", "Victima", PASSWORD)
        url = reverse("accounts:login")
        for n in range(3):
            self.client.post(url, {"username": "victima@example.com", "password": "mala"}, HTTP_X_FORWARDED_FOR=f"198.51.100.{n}")
        response = self.client.post(url, {"username": "victima@example.com", "password": PASSWORD}, HTTP_X_FORWARDED_FOR="198.51.100.99")
        self.assertEqual(response.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_change_alias_requires_login_and_unique_alias(self):
        url = reverse("accounts:change_alias")
        self.assertEqual(self.client.get(url).status_code, 302)
        user = User.objects.create_user("duena@example.com", "AliasAjeno", PASSWORD)
        User.objects.create_user("otra@example.com", "Ocupado", PASSWORD)
        self.client.force_login(user)
        self.assertEqual(self.client.post(url, {"alias": "ocupado"}).status_code, 200)
        self.assertRedirects(self.client.post(url, {"alias": "MiAlias"}), reverse("accounts:profile"), fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertEqual(user.alias, "MiAlias")
