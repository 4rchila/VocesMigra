"""Siembra datos de demostración: 36 usuarios, ~120 publicaciones, comentarios y votos.

Marca demo: correo ``demo.<slug>@example.com`` (prefijo ``demo.`` y dominio
``example.com``). ``--purge`` borra SOLO cuentas con esa marca y nunca toca
los pk 6 y 7. Es determinista (``random.Random(SEED)``) e idempotente
(``get_or_create`` por correo y por (autor, título)). Las contraseñas son
inutilizables. ``--dry-run`` no escribe nada.

Comentarios y votos (publicación y comentario) se generan con el mismo
``rng`` DESPUÉS de usuarios y publicaciones, de modo que esos datos no cambian.
Son idempotentes: comentarios por (publicación, autor, texto) y votos con
``update_or_create`` por (elemento, persona). Solo se interactúa con
publicaciones publicadas y nunca se usan cuentas pk 6/7 preexistentes.
``--purge`` los elimina en cascada junto con las cuentas demo.
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
from apps.interactions.models import Comment, CommentVote, Vote
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
COMMENT_TEXTS = [
    "Gracias por compartir esto, me ayuda mucho a entender mejor el proceso.",
    "A mí me pasó algo parecido. Lo que mejor funcionó fue pedir orientación en una organización comunitaria.",
    "¿Sabes si hace falta algún documento adicional? Yo todavía no tengo claro ese paso.",
    "Un consejo: guarda siempre copias de todo y anota las fechas importantes.",
    "Mucho ánimo. Poco a poco las cosas se van acomodando.",
    "Gracias por la información, la voy a compartir con mi familia.",
    "Yo tuve dudas con esto también; lo que me sirvió fue preguntar en una biblioteca cercana.",
    "Buen punto. Ojalá más personas cuenten sus experiencias así.",
]
COMMENTS_PER_POST = [0, 0, 1, 2, 3, 5]
MAX_VOTERS = 12
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
                f"Se asegurarían {len(plan['users'])} usuarios, {len(plan['posts'])} publicaciones, "
                f"{len(plan['comments'])} comentarios, {len(plan['post_votes'])} votos y "
                f"{len(plan['comment_votes'])} votos de comentario"
            )
            return
        with transaction.atomic():
            made_u, made_p = self.apply(plan)
        self.stdout.write(
            f"Usuarios nuevos: {made_u}; publicaciones nuevas: {made_p}; "
            f"comentarios: {Comment.objects.filter(author__in=self.demo_users()).count()}; "
            f"votos: {Vote.objects.filter(user__in=self.demo_users()).count()}; "
            f"votos de comentario: {CommentVote.objects.filter(user__in=self.demo_users()).count()}"
        )

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
        # Interacciones: se generan al final para no alterar usuarios/publicaciones.
        comments, post_votes, comment_votes = [], [], []
        for j, post in enumerate(posts):
            if post["status"] != Status.PUBLISHED:
                continue
            for k in range(rng.choice(COMMENTS_PER_POST)):
                comments.append({
                    "post": j,
                    "author": rng.randrange(N_USERS),
                    "content": f"{rng.choice(COMMENT_TEXTS)} (comentario {j + 1}.{k + 1})",
                    "key": (j, k),
                })
            voters = rng.sample(range(N_USERS), rng.randint(0, MAX_VOTERS))
            for u in voters:
                if u != post["author"]:
                    post_votes.append({
                        "post": j, "user": u, "value": 1 if rng.random() < 0.75 else -1,
                    })
        for c in comments:
            for u in rng.sample(range(N_USERS), rng.randint(0, 6)):
                if u != c["author"]:
                    comment_votes.append({
                        "key": c["key"], "user": u, "value": 1 if rng.random() < 0.7 else -1,
                    })
        return {
            "users": users,
            "posts": posts,
            "comments": comments,
            "post_votes": post_votes,
            "comment_votes": comment_votes,
        }

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
        def usable(user):
            # Una cuenta pk 6/7 preexistente nunca participa.
            return user.pk in fresh or user.pk not in PROTECTED_PKS

        posts = {}
        for j, p in enumerate(plan["posts"]):
            author = objs[p["author"]]
            if not usable(author):
                continue
            post, created = Post.objects.get_or_create(
                author=author,
                title=p["title"],
                defaults={
                    "category": p["category"],
                    "content": p["content"],
                    "status": p["status"],
                },
            )
            made_p += created
            posts[j] = post
        self.apply_interactions(plan, objs, posts, usable)
        return made_u, made_p

    def apply_interactions(self, plan, objs, posts, usable):
        comments = {}
        for c in plan["comments"]:
            author, post = objs[c["author"]], posts.get(c["post"])
            if post is None or not usable(author):
                continue
            comments[c["key"]], _ = Comment.objects.get_or_create(
                post=post, author=author, content=c["content"]
            )
        for v in plan["post_votes"]:
            user, post = objs[v["user"]], posts.get(v["post"])
            if post is None or not usable(user):
                continue
            Vote.objects.update_or_create(
                post=post, user=user, defaults={"value": v["value"]}
            )
        for v in plan["comment_votes"]:
            user, comment = objs[v["user"]], comments.get(v["key"])
            if comment is None or not usable(user):
                continue
            CommentVote.objects.update_or_create(
                comment=comment, user=user, defaults={"value": v["value"]}
            )
