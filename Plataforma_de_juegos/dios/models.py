from django.contrib.auth.models import User
from django.db import models


class DiosCuenta(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cuenta_dios",
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dios: {self.usuario.username}"


class AdministradorEspecial(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="admin_especial",
    )
    creado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="administradores_creados",
    )
    activo = models.BooleanField(default=True)

    # Usuarios
    puede_strike_usuario = models.BooleanField(default=False)
    puede_ban_usuario = models.BooleanField(default=False)
    puede_eliminar_usuario = models.BooleanField(default=False)

    # Desarrolladores
    puede_strike_desarrollador = models.BooleanField(default=False)
    puede_ban_desarrollador = models.BooleanField(default=False)
    puede_eliminar_desarrollador = models.BooleanField(default=False)

    # Juegos
    puede_eliminar_juegos = models.BooleanField(default=False)
    puede_generar_claves = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Admin especial: {self.usuario.username}"

    class Meta:
        verbose_name = "Administrador especial"
        verbose_name_plural = "Administradores especiales"
