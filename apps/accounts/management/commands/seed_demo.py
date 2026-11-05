"""Siembra datos de demostración: 36 usuarios y ~120 publicaciones.

Marca demo: correo ``demo.<slug>@example.com`` (prefijo ``demo.`` y dominio
``example.com``). ``--purge`` borra SOLO cuentas con esa marca y nunca toca
los pk 6 y 7. Es determinista (``random.Random(SEED)``) e idempotente
(``get_or_create`` por correo y por (autor, título)). Las contraseñas son
inutilizables. ``--dry-run`` no escribe nada.
"""

import random

import pycountry
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Profile, User
from apps.accounts.validators import (
    validate_language_codes,
    validate_region_for_country,
)
from apps.posts.models import Category, Post, Status

SEED = 20260101
N_USERS = 36
N_POSTS = 120
PROTECTED_PKS = [6, 7]
DEMO_PREFIX = "demo."
DEMO_DOMAIN = "@example.com"

NAMES = [
    "maria", "jose", "luisa", "carlos", "ana", "pedro", "sofia", "miguel",
    "elena", "diego", "lucia", "andres", "rosa", "javier", "carmen", "ricardo",
    "paola", "hector", "gabriela", "oscar", "valeria", "ramon", "daniela",
    "mateo", "isabel", "tomas", "camila", "fernando", "patricia", "esteban",
    "noemi", "ivan", "marta", "raul", "julia", "sergio",
]
COUNTRIES = ["GT", "MX", "US", "HN", "SV"]
LANGS = [["es"], ["es", "en"], ["es"], ["en", "es"]]

TOPICS = [
    ("experiences", "Mi travesía hacia {lugar}", "Salí de mi pueblo con poco dinero y mucha esperanza. El camino hacia {lugar} me enseñó a confiar en la gente y a cuidar cada paso. Quiero contar lo que viví para que otras personas se sientan acompañadas."),
    ("experiences", "Los primeros meses en {lugar}", "Llegar a {lugar} fue más difícil de lo que imaginaba: el idioma, el frío, el trabajo. Poco a poco armé una rutina y encontré gente que me tendió la mano."),
    ("problems", "No logro entender mi cita de inmigración en {lugar}", "Recibí una carta con una fecha y varios formularios que no comprendo. ¿Alguien pasó por algo parecido en {lugar}? Busco orientación sobre qué documentos llevar."),
    ("problems", "Dificultades para conseguir vivienda en {lugar}", "Pedir un contrato sin historial ni papeles locales es casi imposible. He recibido muchas negativas y necesito consejos prácticos para no caer en estafas."),
    ("help", "Guía básica de trámites al llegar a {lugar}", "Comparto una lista de pasos que me sirvió: abrir un buzón de correo, buscar una organización comunitaria, guardar copias de todos los documentos y pedir ayuda legal gratuita."),
    ("help", "Dónde encontrar clases de idioma gratis en {lugar}", "Las bibliotecas y las iglesias suelen ofrecer clases sin costo. Aquí van algunas recomendaciones para empezar cuanto antes y no quedarse aislado."),
    ("opinions", "Lo que pienso del debate migratorio en {lugar}", "Se habla mucho de cifras y poco de personas. Creo que hace falta escuchar las historias reales detrás de cada trámite y de cada frontera."),
    ("opinions", "Por qué importa contar nuestras historias", "Cuando una historia se comparte, deja de ser una carga individual. Escribir sobre {lugar} me ayudó a ordenar mis ideas y a sentirme menos solo."),
    ("community", "Encuentro de familias migrantes en {lugar}", "Organizamos una comida compartida para conocernos y compartir recursos. Quien quiera sumarse con ideas o con un plato será bienvenido."),
    ("community", "Busco red de apoyo en {lugar}", "Acabo de llegar y no conozco a nadie. Me gustaría conectar con personas de mi país para intercambiar consejos y apoyarnos mutuamente."),
]
PLACES = ["Estados Unidos", "México", "Guatemala", "Honduras", "El Salvador", "Canadá", "España", "Houston", "Los Ángeles", "Ciudad de México"]


class Command(BaseCommand):
    help = "Crea (o purga con --purge) usuarios y publicaciones de demostración."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--purge", action="store_true")

    def demo_users(self):
        return User.objects.filter(
            email__startswith=DEMO_PREFIX, email__endswith=DEMO_DOMAIN
        ).exclude(pk__in=PROTECTED_PKS)

    def handle(self, *args, dry_run=False, purge=False, **options):
        if purge:
            qs = self.demo_users()
            n = qs.count()
            if not dry_run:
                qs.delete()
            self.stdout.write(f"{'Se borrarían' if dry_run else 'Borrados'}: {n} usuarios demo")
            return
        rng = random.Random(SEED)
        plan = self.build_plan(rng)
        if dry_run:
            self.stdout.write(
                f"Se asegurarían {len(plan['users'])} usuarios y {len(plan['posts'])} publicaciones"
            )
            return
        with transaction.atomic():
            made_u, made_p = self.apply(plan)
        self.stdout.write(f"Usuarios nuevos: {made_u}; publicaciones nuevas: {made_p}")

    def build_plan(self, rng):
        users = []
        for i in range(N_USERS):
            name = NAMES[i]
            country = COUNTRIES[i % len(COUNTRIES)]
            subs = sorted(s.code for s in pycountry.subdivisions.get(country_code=country))
            users.append({
                "email": f"{DEMO_PREFIX}{name}{DEMO_DOMAIN}",
                "alias": f"{name.capitalize()}_{rng.randint(10, 99)}",
                "country": country,
                "region": rng.choice(subs),
                "languages": rng.choice(LANGS),
                "description": f"Soy {name.capitalize()}, comparto mi experiencia migrando para acompañar a otras personas.",
            })
        posts = []
        for j in range(N_POSTS):
            cat, title, body = TOPICS[j % len(TOPICS)]
            lugar = rng.choice(PLACES)
            status = Status.DRAFT if rng.random() < 0.1 else Status.PUBLISHED
            posts.append({
                "author": rng.randrange(N_USERS),
                "category": cat,
                # el número hace único el título por autor
                "title": f"{title.format(lugar=lugar)} (relato {j + 1})"[:160],
                "content": body.format(lugar=lugar),
                "status": status,
            })
        return {"users": users, "posts": posts}

    def apply(self, plan):
        made_u = made_p = 0
        objs = []
        fresh = set()
        for d in plan["users"]:
            validate_language_codes(d["languages"])
            validate_region_for_country(d["region"], d["country"])
            user = User.objects.filter(email=d["email"]).first()
            if user is None:
                alias = d["alias"]
                while User.objects.filter(alias__iexact=alias).exists():
                    alias += "x"
                user = User(email=d["email"], alias=alias[:30], is_active=True)
                user.set_unusable_password()
                user.save()
                made_u += 1
                fresh.add(user.pk)
            # Un usuario preexistente con pk 6/7 no se toca; uno recién creado sí.
            if user.pk in fresh or user.pk not in PROTECTED_PKS:
                Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        "country": d["country"],
                        "region": d["region"],
                        "languages": d["languages"],
                        "description": d["description"],
                    },
                )
            objs.append(user)
        for p in plan["posts"]:
            author = objs[p["author"]]
            if author.pk in PROTECTED_PKS and author.pk not in fresh:
                continue
            _, created = Post.objects.get_or_create(
                author=author,
                title=p["title"],
                defaults={
                    "category": p["category"],
                    "content": p["content"],
                    "status": p["status"],
                },
            )
            made_p += created
        return made_u, made_p
