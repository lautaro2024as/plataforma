from django.contrib import admin

from .models import AlertaMalware, DetallePedido, Juego, LicenciaCompra, Pedido, PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rol", "nombre_estudio", "strikes", "baneado")
    list_filter = ("rol", "baneado")
    search_fields = ("usuario__username", "usuario__email", "nombre_estudio")


@admin.register(Juego)
class JuegoAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "desarrollador",
        "categoria",
        "precio",
        "stock",
        "estado",
        "etiqueta_mas_18",
    )
    list_filter = ("estado", "categoria", "etiqueta_mas_18")
    search_fields = ("titulo", "desarrollador__usuario__username", "desarrollador__nombre_estudio")


@admin.register(AlertaMalware)
class AlertaMalwareAdmin(admin.ModelAdmin):
    list_display = ("juego", "fecha_alerta", "resuelta")
    list_filter = ("resuelta",)


@admin.register(LicenciaCompra)
class LicenciaCompraAdmin(admin.ModelAdmin):
    list_display = (
        "jugador",
        "juego",
        "edicion",
        "origen",
        "fecha_compra",
        "monto_pagado",
    )
    search_fields = ("jugador__usuario__username", "juego__titulo", "clave")
    readonly_fields = ("jugador", "juego", "edicion", "clave", "origen", "fecha_compra", "monto_pagado")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "estado", "fecha_creacion", "total")
    list_filter = ("estado", "fecha_creacion")
    search_fields = ("usuario__usuario__username", "usuario__usuario__email")
    readonly_fields = ("usuario", "fecha_creacion", "total")


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "juego", "cantidad", "precio_unitario", "edicion")
    list_filter = ("edicion",)
    readonly_fields = ("pedido", "juego", "cantidad", "precio_unitario", "edicion")
