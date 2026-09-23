from django.contrib import admin

from .models import AdministradorEspecial, DiosCuenta


@admin.register(DiosCuenta)
class DiosCuentaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "activo", "fecha_creacion")
    list_filter = ("activo",)
    search_fields = ("usuario__username", "usuario__email")


@admin.register(AdministradorEspecial)
class AdministradorEspecialAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "activo",
        "puede_strike_usuario",
        "puede_ban_usuario",
        "puede_eliminar_usuario",
        "puede_strike_desarrollador",
        "puede_ban_desarrollador",
        "puede_eliminar_desarrollador",
        "puede_eliminar_juegos",
        "puede_generar_claves",
    )
    list_filter = ("activo",)
    search_fields = ("usuario__username", "usuario__email")
