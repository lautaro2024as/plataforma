from django.contrib import admin
from .models import PerfilUsuario, Juego, AlertaMalware, LicenciaCompra

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'fecha_nacimiento', 'baneado')
    list_filter = ('rol', 'baneado')
    search_fields = ('usuario__username', 'usuario__email')
    actions = ['banear_usuarios', 'desbanear_usuarios']

    # Acción personalizada: Banear Desarrolladores o Jugadores
    def banear_usuarios(self, request, queryset):
        queryset.update(baneado=True)
    banear_usuarios.short_description = "Banear usuarios seleccionados"

    def desbanear_usuarios(self, request, queryset):
        queryset.update(baneado=False)
    desbanear_usuarios.short_description = "Quitar baneo a usuarios seleccionados"


@admin.register(Juego)
class JuegoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'desarrollador', 'precio', 'etiqueta_mas_18', 'estado')
    list_filter = ('estado', 'etiqueta_mas_18')
    search_fields = ('titulo', 'desarrollador__usuario__username')
    actions = ['aprobar_juegos', 'banear_contenido']

    # Acciones para cambiar el estado del contenido tras pasar el pipeline de seguridad
    def aprobar_juegos(self, request, queryset):
        queryset.update(estado='publicado')
    aprobar_juegos.short_description = "Cambiar estado a 'Publicado' (Aprobar)"

    def banear_contenido(self, request, queryset):
        queryset.update(estado='baneado')
    banear_contenido.short_description = "Banear contenido seleccionado"


@admin.register(AlertaMalware)
class AlertaMalwareAdmin(admin.ModelAdmin):
    list_display = ('juego', 'fecha_alerta', 'resuelta')
    list_filter = ('resuelta',)
    actions = ['marcar_como_resuelta']

    # Acción para Moderar Alertas de Malware
    def marcar_como_resuelta(self, request, queryset):
        queryset.update(resuelta=True)
    marcar_como_resuelta.short_description = "Moderar: Marcar alertas como resueltas/falsos positivos"


@admin.register(LicenciaCompra)
class LicenciaCompraAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'juego', 'fecha_compra', 'monto_pagado')
    search_fields = ('jugador__usuario__username', 'juego__titulo')
    # Las licencias normalmente son de solo lectura en el panel admin para no alterar la auditoría
    readonly_fields = ('jugador', 'juego', 'fecha_compra', 'monto_pagado')