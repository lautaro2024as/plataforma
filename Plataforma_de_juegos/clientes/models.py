from django.core.validators import MinValueValidator
from django.db import models

from administrador.models import Juego, PerfilUsuario


class CarritoItem(models.Model):
    perfil = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, related_name="items_carrito")
    juego = models.ForeignKey(Juego, on_delete=models.CASCADE, related_name="items_carrito")
    edicion = models.CharField(max_length=20, default="Estándar")
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    agregado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("perfil", "juego", "edicion"),
                name="unique_cart_game_edition_per_profile",
            )
        ]
        ordering = ("agregado_en", "pk")

    def __str__(self):
        return f"{self.cantidad} x {self.juego.titulo} ({self.perfil.usuario.username})"
