"""Reglas de voto: crear, cambiar o revocar con una transacción explícita."""

from django.db import IntegrityError, transaction


def cast_vote(model, owner_field, owner, user, value):
    """Aplica un voto de ``user`` sobre ``owner`` y devuelve el valor final.

    - Sin voto previo: se crea.
    - Mismo valor otra vez: se revoca (devuelve ``None``).
    - Valor opuesto: se cambia.
    Nunca hay más de una fila por (elemento, persona): lo garantiza además la
    UniqueConstraint de la base de datos. Un doble POST concurrente cae en
    IntegrityError, se relee la fila y se aplica la misma lógica.
    """
    lookup = {owner_field: owner, "user": user}
    with transaction.atomic():
        vote = model.objects.select_for_update().filter(**lookup).first()
        if vote is None:
            try:
                with transaction.atomic():
                    model.objects.create(value=value, **lookup)
                return value
            except IntegrityError:
                vote = model.objects.select_for_update().get(**lookup)
        if vote.value == value:
            vote.delete()
            return None
        vote.value = value
        vote.save(update_fields=["value"])
        return value


def user_votes(model, owner_field, user, owner_ids):
    """Mapa {id_del_elemento: valor} de los votos de ``user``."""
    if user is None or not user.is_authenticated:
        return {}
    return dict(
        model.objects.filter(user=user, **{f"{owner_field}__in": owner_ids}).values_list(
            f"{owner_field}_id", "value"
        )
    )
