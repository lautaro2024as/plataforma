from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("administrador", "0002_marketplace_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="perfilusuario",
            name="rol",
            field=models.CharField(
                choices=[
                    ("jugador", "Jugador / Usuario"),
                    ("desarrollador", "Desarrollador Indie"),
                    ("administrador", "Administrador Especial"),
                ],
                default="jugador",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="licenciacompra",
            name="jugador",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="licencias",
                to="administrador.perfilusuario",
            ),
        ),
    ]
