from django.db import migrations, models


def rellenar_claves(apps, schema_editor):
    LicenciaCompra = apps.get_model("administrador", "LicenciaCompra")
    for licencia in LicenciaCompra.objects.filter(clave__isnull=True):
        licencia.clave = f"NEXUS-LEGACY-{licencia.pk:012d}"
        licencia.save(update_fields=["clave"])


class Migration(migrations.Migration):

    dependencies = [
        ("administrador", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="nombre_estudio",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="tax_id",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="strikes",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="juego",
            name="calificacion",
            field=models.DecimalField(decimal_places=1, default=0.0, max_digits=3),
        ),
        migrations.AddField(
            model_name="juego",
            name="categoria",
            field=models.CharField(default="Indie", max_length=40),
        ),
        migrations.AddField(
            model_name="juego",
            name="descripcion",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="juego",
            name="imagen_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="juego",
            name="precio_original",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="juego",
            name="tipo_clave",
            field=models.CharField(default="Steam Key Global", max_length=80),
        ),
        migrations.AlterField(
            model_name="licenciacompra",
            name="monto_pagado",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name="licenciacompra",
            name="clave",
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name="licenciacompra",
            name="edicion",
            field=models.CharField(default="Estándar", max_length=20),
        ),
        migrations.AddField(
            model_name="licenciacompra",
            name="origen",
            field=models.CharField(
                choices=[
                    ("compra", "Compra"),
                    ("desarrollador", "Gratis - Desarrollador"),
                    ("admin", "Gratis - Administrador"),
                ],
                default="compra",
                max_length=20,
            ),
        ),
        migrations.RunPython(rellenar_claves, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="licenciacompra",
            name="clave",
            field=models.CharField(max_length=40, unique=True),
        ),
    ]
