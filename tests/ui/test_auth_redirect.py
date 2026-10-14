"""End-to-end checks for the account login redirect field."""

from html.parser import HTMLParser

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User

PASSWORD = "clave-pruebas-123"


class HiddenNextParser(HTMLParser):
    """Collect the hidden ``next`` value exactly as a browser would submit it."""

    def __init__(self):
        super().__init__()
        self.next_value = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "input" and attributes.get("name") == "next":
            self.next_value = attributes.get("value", "")


class LoginRedirectTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "login@example.com", "LoginPrueba", PASSWORD
        )
        self.login_url = reverse("accounts:login")

    def next_value_from(self, response):
        parser = HiddenNextParser()
        parser.feed(response.content.decode(response.charset))
        return parser.next_value

    def test_login_form_preserves_internal_next_destination(self):
        destination = reverse("posts:list")
        response = self.client.get(self.login_url, {"next": destination})
        self.assertEqual(response.status_code, 200)
        submitted_next = self.next_value_from(response)
        self.assertEqual(submitted_next, destination)

        response = self.client.post(
            self.login_url,
            {
                "username": self.user.email,
                "password": PASSWORD,
                "next": submitted_next,
            },
        )
        self.assertRedirects(
            response, destination, fetch_redirect_response=False
        )

    def test_external_next_destination_is_not_followed(self):
        external_url = "https://malicioso.example/perfil/"
        response = self.client.get(self.login_url, {"next": external_url})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.next_value_from(response), "")

        response = self.client.post(
            self.login_url,
            {
                "username": self.user.email,
                "password": PASSWORD,
                "next": external_url,
            },
        )
        self.assertRedirects(
            response, reverse("accounts:profile"), fetch_redirect_response=False
        )
        self.assertNotEqual(response["Location"], external_url)
