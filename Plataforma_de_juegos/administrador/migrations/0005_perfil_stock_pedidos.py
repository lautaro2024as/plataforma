import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("administrador", "0004_demo_game")]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="telefono",
            field=models.CharField(blank=True, default="", max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="direccion",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="ciudad",
            field=models.CharField(blank=True, default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="juego",
            name="stock",
            field=models.PositiveIntegerField(default=100, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.CreateModel(
            name="Pedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("estado", models.CharField(choices=[("pendiente", "Pendiente"), ("completado", "Completado"), ("cancelado", "Cancelado")], default="pendiente", max_length=20)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("total", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to="administrador.perfilusuario")),
            ],
            options={"ordering": ("-fecha_creacion", "-pk")},
        ),
        migrations.CreateModel(
            name="DetallePedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cantidad", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("precio_unitario", models.DecimalField(decimal_places=2, max_digits=10)),
                ("edicion", models.CharField(default="Estándar", max_length=20)),
                ("juego", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="detalles_pedido", to="administrador.juego")),
                ("pedido", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="detalles", to="administrador.pedido")),
            ],
        ),
        migrations.AddField(
            model_name="licenciacompra",
            name="pedido",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="licencias", to="administrador.pedido"),
        ),
    ]
