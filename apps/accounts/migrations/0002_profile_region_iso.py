"""Región pasa de texto libre a código ISO 3166-2 (1.8).

Efecto en datos: los valores que no son un código ISO 3166-2 válido del país
del perfil se vacían antes de acortar la columna. No hay vuelta atrás para
esos textos; el piloto solo tiene datos sintéticos.
"""

from django.db import migrations, models


def clear_free_text_regions(apps, schema_editor):
    import pycountry

    Profile = apps.get_model("accounts", "Profile")
    for profile in Profile.objects.exclude(region=""):
        sub = pycountry.subdivisions.get(code=profile.region.strip().upper())
        if sub is None or sub.country_code != profile.country:
            profile.region = ""
        else:
            profile.region = sub.code
        profile.save(update_fields=["region"])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(clear_free_text_regions, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='profile',
            name='region',
            field=models.CharField(blank=True, help_text='Código ISO 3166-2 de la región; opcional.', max_length=6, verbose_name='región'),
        ),
    ]
