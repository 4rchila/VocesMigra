"""Structural checks for the formal, accessible, mobile-first Voces Migra UI.

These tests use only the standard library so they can run before Django is
installed or wired. They read the raw template and CSS files and assert the
presence of the accessibility, responsive and contractual patterns required by
the formal posts experience.
"""

import os
import re
import unittest


REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)

TEMPLATE_PATHS = [
    "templates/base.html",
    "templates/core/home.html",
    "templates/components/navigation.html",
    "templates/components/footer.html",
    "templates/components/messages.html",
    "templates/components/card.html",
    "templates/components/empty_state.html",
    "templates/components/form_field.html",
    "templates/components/category_nav.html",
    "templates/components/pagination.html",
    "templates/posts/post_list.html",
    "templates/posts/post_detail.html",
    "templates/posts/post_form.html",
    "templates/posts/post_confirm_delete.html",
]

POST_TEMPLATE_PATHS = [
    "templates/posts/post_list.html",
    "templates/posts/post_detail.html",
    "templates/posts/post_form.html",
    "templates/posts/post_confirm_delete.html",
]

COMPONENT_PATHS = [
    "templates/components/navigation.html",
    "templates/components/footer.html",
    "templates/components/messages.html",
    "templates/components/card.html",
    "templates/components/empty_state.html",
    "templates/components/form_field.html",
    "templates/components/category_nav.html",
    "templates/components/pagination.html",
]


# Institutional copy that must appear literally.
INSTITUTIONAL_TITLE = "Información y apoyo para cada etapa del camino"
INSTITUTIONAL_DESCRIPTION = (
    "Voces Migra es un espacio comunitario para compartir experiencias, "
    "solicitar orientación y consultar recursos útiles relacionados con "
    "procesos de migración."
)
INSTITUTIONAL_NOTICE = (
    "Participa con respeto y protege tus datos personales. "
    "La información compartida por la comunidad no sustituye asesoría legal "
    "ni atención de emergencia."
)
PRIMARY_ACTIONS = ["Explorar publicaciones", "Crear una publicación"]


def _read(path):
    with open(os.path.join(REPO_ROOT, path), "r", encoding="utf-8") as f:
        return f.read()


def _read_all(paths):
    return "".join(_read(p) for p in paths)


class TemplateStructureTests(unittest.TestCase):
    """Presence of required UI components and accessibility patterns."""

    def test_required_templates_exist(self):
        for path in TEMPLATE_PATHS:
            with self.subTest(path=path):
                self.assertTrue(
                    os.path.isfile(os.path.join(REPO_ROOT, path)),
                    f"Missing template: {path}",
                )

    def test_base_template_exists(self):
        self.assertTrue(
            os.path.isfile(os.path.join(REPO_ROOT, "templates/base.html"))
        )

    def test_core_home_extends_base(self):
        content = _read("templates/core/home.html")
        self.assertIn('{% extends "base.html" %}', content)

    def test_base_has_skip_link_and_main_landmark(self):
        content = _read("templates/base.html")
        self.assertIn('href="#main-content"', content)
        self.assertIn('id="main-content"', content)
        self.assertRegex(content, r"<main\b")
        all_content = _read_all(
            [
                "templates/base.html",
                "templates/components/navigation.html",
                "templates/components/footer.html",
            ]
        )
        self.assertRegex(all_content, r"<header\b")
        self.assertRegex(all_content, r"<nav\b")
        self.assertRegex(all_content, r"<footer\b")

    def test_navigation_is_semantic_and_has_touch_target_classes(self):
        content = _read("templates/components/navigation.html")
        self.assertIn('role="list"', content)
        self.assertIn('aria-label="', content)
        self.assertIn("nav-list__link", content)
        self.assertIn("site-header", content)

    def test_navigation_links_to_posts_urls(self):
        content = _read("templates/components/navigation.html")
        self.assertIn("{% url 'posts:list' %}", content)
        self.assertIn("{% url 'posts:create' %}", content)
        self.assertIn("{% url 'core:home' %}", content)

    def test_navigation_does_not_advertise_unimplemented_search(self):
        content = _read("templates/components/navigation.html")
        self.assertNotIn("/buscar/", content)
        self.assertNotIn(">{% trans \"Buscar\" %}<", content)

    def test_card_is_article_with_heading_and_metadata(self):
        content = _read("templates/components/card.html")
        self.assertRegex(content, r"<article\b")
        self.assertRegex(content, r"<h2\b")
        self.assertIn("card__title", content)
        self.assertIn("card__category", content)
        self.assertIn("card__meta", content)
        self.assertIn("card__meta-item", content)

    def test_card_has_no_social_metrics(self):
        content = _read("templates/components/card.html").lower()
        forbidden = ["likes", "me gusta", "favoritos", "puntuación", "comentarios"]
        for term in forbidden:
            with self.subTest(term=term):
                self.assertNotIn(term, content)

    def test_empty_state_includes_icon_and_title(self):
        content = _read("templates/components/empty_state.html")
        self.assertIn("empty-state", content)
        self.assertIn('aria-hidden="true"', content)
        self.assertIn('focusable="false"', content)

    def test_messages_are_a_list_with_roles(self):
        content = _read("templates/components/messages.html")
        self.assertIn('role="list"', content)
        self.assertIn(
            "{% if message.tags == 'error' %}alert{% else %}status{% endif %}",
            content,
        )

    def test_form_field_has_label_and_aria_descriptions(self):
        content = _read("templates/components/form_field.html")
        self.assertIn("<label", content)
        self.assertIn('for="{{ id }}"', content)
        self.assertIn("aria-describedby", content)
        self.assertIn('aria-invalid="true"', content)
        self.assertIn("form-control--error", content)
        self.assertIn("visually-hidden", content)

    def test_form_field_supports_textarea_and_select(self):
        content = _read("templates/components/form_field.html")
        self.assertIn('{% if type == "textarea" %}', content)
        self.assertIn('{% elif type == "select" %}', content)
        self.assertIn("<textarea", content)
        self.assertIn("<select", content)

    def test_category_nav_exists_and_consumes_categories_context(self):
        content = _read("templates/components/category_nav.html")
        self.assertIn("category-nav", content)
        self.assertIn("category-list", content)
        self.assertIn("{% if categories %}", content)
        self.assertIn("{% for category in categories %}", content)
        self.assertIn("selected_category", content)
        self.assertIn("{% url 'posts:list' %}", content)

    def test_pagination_exists_and_uses_page_obj(self):
        content = _read("templates/components/pagination.html")
        self.assertIn("page_obj", content)
        self.assertIn("page_obj.paginator.num_pages", content)
        self.assertIn("page_obj.has_previous", content)
        self.assertIn("page_obj.has_next", content)
        self.assertIn("aria-label=\"{% trans 'Paginación' %}\"", content)


class HomeTemplateTests(unittest.TestCase):
    """Institutional copy and formal actions on the landing page."""

    def test_home_contains_literal_institutional_title(self):
        content = _read("templates/core/home.html")
        self.assertIn(INSTITUTIONAL_TITLE, content)

    def test_home_contains_literal_institutional_description(self):
        content = _read("templates/core/home.html")
        self.assertIn(INSTITUTIONAL_DESCRIPTION, content)

    def test_home_contains_literal_actions(self):
        content = _read("templates/core/home.html")
        for action in PRIMARY_ACTIONS:
            with self.subTest(action=action):
                self.assertIn(action, content)

    def test_home_contains_literal_institutional_notice(self):
        content = _read("templates/core/home.html")
        self.assertIn(INSTITUTIONAL_NOTICE, content)

    def test_home_uses_posts_urls_for_actions(self):
        content = _read("templates/core/home.html")
        self.assertIn("{% url 'posts:list' %}", content)
        self.assertIn("{% url 'posts:create' %}", content)

    def test_home_uses_components(self):
        content = _read("templates/core/home.html")
        self.assertIn("components/card.html", content)
        self.assertIn("components/empty_state.html", content)
        self.assertIn("components/category_nav.html", content)
        nav_content = _read("templates/components/category_nav.html")
        self.assertIn("category-list", nav_content)

    def test_home_has_no_popularity_language(self):
        content = _read("templates/core/home.html").lower()
        forbidden = [
            "popular",
            "populares",
            "fama",
            "seguidores",
            "ranking",
            "rankings",
            "reputación",
            "competir",
            "viral",
            "trending",
            "insignia",
            "insignias",
            "racha",
            "rachas",
            "puntuación",
            "puntuaciones",
        ]
        for term in forbidden:
            with self.subTest(term=term):
                self.assertNotIn(term, content)

    def test_home_consumes_posts_context(self):
        content = _read("templates/core/home.html")
        self.assertIn("{% if posts %}", content)
        self.assertIn("{% for post in posts %}", content)
        self.assertIn("post.title", content)
        self.assertIn("post.get_category_display", content)
        self.assertIn("post.author", content)
        self.assertIn("post.created_at", content)


class FooterTests(unittest.TestCase):
    """Footer reinforces institutional navigation and notice."""

    def test_footer_contains_institutional_notice(self):
        content = _read("templates/components/footer.html")
        self.assertIn(INSTITUTIONAL_NOTICE, content)

    def test_footer_links_to_posts_and_home(self):
        content = _read("templates/components/footer.html")
        self.assertIn("{% url 'core:home' %}", content)
        self.assertIn("{% url 'posts:list' %}", content)


class PostsTemplateContractTests(unittest.TestCase):
    """The four posts templates honour the required context and URL contracts."""

    def test_post_list_extends_base(self):
        content = _read("templates/posts/post_list.html")
        self.assertIn('{% extends "base.html" %}', content)

    def test_post_list_consumes_page_obj_and_posts_context(self):
        content = _read("templates/posts/post_list.html")
        pagination = _read("templates/components/pagination.html")
        self.assertIn("page_obj.object_list", content)
        self.assertIn("page_obj.paginator.num_pages", pagination)
        self.assertRegex(content, r"{%\s+(?:if|elif)\s+posts\s+%}")
        self.assertIn("{% for post in posts %}", content)

    def test_post_list_consumes_categories_and_selected_category(self):
        content = _read("templates/posts/post_list.html")
        nav_content = _read("templates/components/category_nav.html")
        self.assertIn("category_nav.html", content)
        self.assertIn("selected_category", nav_content)
        self.assertIn("categories", nav_content)

    def test_post_detail_consumes_post_context(self):
        content = _read("templates/posts/post_detail.html")
        self.assertIn("post.title", content)
        self.assertIn("post.content", content)
        self.assertIn("post.author", content)
        self.assertIn("post.get_category_display", content)
        self.assertIn("post.created_at", content)
        self.assertIn("post.public_id", content)

    def test_post_detail_has_author_actions(self):
        content = _read("templates/posts/post_detail.html")
        self.assertIn("{% url 'posts:update' post.public_id %}", content)
        self.assertIn("{% url 'posts:delete' post.public_id %}", content)
        self.assertIn("{% url 'posts:list' %}", content)

    def test_post_form_consumes_form_and_post_context(self):
        content = _read("templates/posts/post_form.html")
        self.assertIn("{% for field in form %}", content)
        self.assertIn("form.non_field_errors", content)
        self.assertIn("field.errors", content)
        self.assertIn("field.id_for_label", content)
        self.assertIn("field.html_name", content)
        self.assertIn("if post", content)

    def test_post_form_links_to_posts_urls(self):
        content = _read("templates/posts/post_form.html")
        self.assertIn("{% url 'posts:list' %}", content)
        self.assertIn("{% url 'posts:detail' post.public_id %}", content)

    def test_post_confirm_delete_consumes_post_context(self):
        content = _read("templates/posts/post_confirm_delete.html")
        self.assertIn("post.title", content)
        self.assertIn("post.public_id", content)
        self.assertIn("{% url 'posts:delete' post.public_id %}", content)
        self.assertIn("{% url 'posts:detail' post.public_id %}", content)

    def test_all_posts_urls_are_used_exactly(self):
        all_templates = _read_all(POST_TEMPLATE_PATHS)
        required_urls = [
            "{% url 'posts:list' %}",
            "{% url 'posts:detail' post.public_id %}",
            "{% url 'posts:create' %}",
            "{% url 'posts:update' post.public_id %}",
            "{% url 'posts:delete' post.public_id %}",
        ]
        for url in required_urls:
            with self.subTest(url=url):
                self.assertIn(url, all_templates)

    def test_posts_templates_have_no_social_metrics(self):
        all_posts = _read_all(POST_TEMPLATE_PATHS).lower()
        forbidden = ["likes", "me gusta", "favoritos", "puntuación", "comentarios"]
        for term in forbidden:
            with self.subTest(term=term):
                self.assertNotIn(term, all_posts)


class CssAccessibilityTests(unittest.TestCase):
    """Checks for mobile-first responsive CSS and accessibility primitives."""

    def test_css_uses_system_fonts_and_no_remote_resources(self):
        content = _read("static/css/main.css")
        self.assertIn("system-ui", content)
        self.assertIn("-apple-system", content)
        self.assertNotIn("fonts.googleapis.com", content)
        self.assertNotIn("@import", content)
        self.assertNotIn("http://", content)
        self.assertNotIn("https://", content)

    def test_css_has_institutional_palette(self):
        content = _read("static/css/main.css")
        self.assertIn("#15324A", content)
        self.assertIn("#1F7A72", content)
        self.assertIn("#F7F8F6", content)
        self.assertIn("#425466", content)
        self.assertIn("#C88719", content)

    def test_css_has_touch_target_tokens_and_applies_them(self):
        content = _read("static/css/main.css")
        self.assertIn("--touch-target: 44px", content)
        self.assertIn("--touch-target-large: 48px", content)
        self.assertIn("min-block-size: var(--touch-target)", content)
        self.assertIn("min-inline-size: var(--touch-target)", content)

    def test_css_has_visible_focus_styles(self):
        content = _read("static/css/main.css")
        self.assertIn(":focus-visible", content)
        self.assertIn("outline-offset", content)
        self.assertIn("outline", content)

    def test_css_respects_reduced_motion(self):
        content = _read("static/css/main.css")
        self.assertIn("@media (prefers-reduced-motion: reduce)", content)
        self.assertIn("scroll-behavior: auto", content)

    def test_css_is_mobile_first_with_360px_baseline(self):
        content = _read("static/css/main.css")
        self.assertIn("@media (min-width: 360px)", content)
        self.assertIn("@media (min-width: 40rem)", content)
        self.assertIn("@media (min-width: 64rem)", content)

    def test_css_has_viewport_agnostic_spacing_units(self):
        content = _read("static/css/main.css")
        self.assertIn("--space-xs:", content)
        self.assertIn("--space-xl:", content)
        self.assertIn("padding-inline", content)

    def test_css_differentiates_primary_and_secondary_buttons(self):
        content = _read("static/css/main.css")
        self.assertIn(".button--primary", content)
        self.assertIn(".button--secondary", content)

    def test_css_has_semantic_landmark_selectors(self):
        content = _read("static/css/main.css")
        self.assertIn(".site-header", content)
        self.assertIn(".site-footer", content)
        self.assertIn(".main-content", content)


class NoForbiddenDependenciesTests(unittest.TestCase):
    """Ensure the UI layer does not introduce prohibited scripts or frameworks."""

    def test_no_javascript_or_htmx_in_templates(self):
        for path in TEMPLATE_PATHS:
            content = _read(path).lower()
            with self.subTest(path=path):
                self.assertNotIn("<script", content)
                self.assertNotIn("hx-", content)
                self.assertNotIn("bootstrap", content)
                self.assertNotIn("tailwind", content)

    def test_no_remote_resources_in_css_or_templates(self):
        for path in ["static/css/main.css"] + TEMPLATE_PATHS:
            content = _read(path).lower()
            with self.subTest(path=path):
                self.assertNotIn("http://", content)
                self.assertNotIn("https://", content)
                self.assertNotIn("//cdn", content)
                self.assertNotIn("//unpkg", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
