"""Fase 1, tareas 1.5, 1.7 y 1.8: cabeceras, logs sin datos personales y región cerrada."""

import logging

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.models import Profile, User
from apps.core.logging import RedactPersonalDataFilter, redact


class SecurityHeadersTests(TestCase):
    def test_csp_and_referrer_policy_on_pages(self):
        response = self.client.get(reverse("core:home"))
        csp = response["Content-Security-Policy"]
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertNotIn("unsafe-inline", csp)
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")


class LogRedactionTests(SimpleTestCase):
    def test_redacts_email_and_truncates_ips(self):
        text = redact("fallo de ana.perez+x@example.com desde 198.51.100.77 y 2001:db8:abcd:12::1")
        self.assertNotIn("ana.perez", text)
        self.assertIn("[correo]", text)
        self.assertIn("198.51.100.0", text)
        self.assertNotIn("198.51.100.77", text)
        self.assertIn("2001:db8:abcd::", text)

    def test_filter_rewrites_formatted_record(self):
        record = logging.LogRecord(
            "x", logging.INFO, __file__, 1, "acceso de %s", ("ana@example.com",), None
        )
        RedactPersonalDataFilter().filter(record)
        self.assertEqual(record.getMessage(), "acceso de [correo]")


class RegionClosedListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("perfil@example.com", "Perfil", "clave-sintetica-123")

    def test_accepts_iso_subdivision_of_same_country(self):
        profile = Profile(user=self.user, country="GT", region="GT-01")
        profile.full_clean()
        self.assertEqual(profile.region_display, "Guatemala")

    def test_rejects_free_text_and_other_country(self):
        for region in ["Mi barrio, calle 5", "ES-MD", "GT-GU", "XX-00"]:
            with self.subTest(region=region), self.assertRaises(ValidationError) as ctx:
                Profile(user=self.user, country="GT", region=region).full_clean()
            self.assertIn("region", ctx.exception.message_dict)
