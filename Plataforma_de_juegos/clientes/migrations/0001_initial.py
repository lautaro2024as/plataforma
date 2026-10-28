import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [("administrador", "0005_perfil_stock_pedidos")]

    operations = [
        migrations.CreateModel(
            name="CarritoItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("edicion", models.CharField(default="Estándar", max_length=20)),
                ("cantidad", models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ("agregado_en", models.DateTimeField(auto_now_add=True)),
                ("juego", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items_carrito", to="administrador.juego")),
                ("perfil", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items_carrito", to="administrador.perfilusuario")),
            ],
            options={"ordering": ("agregado_en", "pk")},
        ),
        migrations.AddConstraint(
            model_name="carritoitem",
            constraint=models.UniqueConstraint(fields=("perfil", "juego", "edicion"), name="unique_cart_game_edition_per_profile"),
        ),
    ]
