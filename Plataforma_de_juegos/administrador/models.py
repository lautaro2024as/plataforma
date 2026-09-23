from django.contrib.auth.models import User
from django.db import models


class PerfilUsuario(models.Model):
    ROLES = (
        ("jugador", "Jugador / Usuario"),
        ("desarrollador", "Desarrollador Indie"),
        ("administrador", "Administrador Especial"),
    )

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, default="jugador")
    nombre_estudio = models.CharField(max_length=150, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    strikes = models.PositiveSmallIntegerField(default=0)
    baneado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.usuario.username} ({self.get_rol_display()})"


class Juego(models.Model):
    ESTADOS = (
        ("cuarentena", "En Cuarentena (Análisis Anti-Malware)"),
        ("publicado", "Publicado (Archivo Limpio)"),
        ("baneado", "Baneado (Contenido Rechazado)"),
    )

    titulo = models.CharField(max_length=150)
    categoria = models.CharField(max_length=40, default="Indie")
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    precio_original = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    imagen_url = models.URLField(blank=True)
    descripcion = models.TextField(blank=True)
    calificacion = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    tipo_clave = models.CharField(max_length=80, default="Steam Key Global")
    etiqueta_mas_18 = models.BooleanField(default=False)
    archivo_exe = models.FileField(upload_to="juegos_exe/", null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="cuarentena")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    desarrollador = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        limit_choices_to={"rol": "desarrollador"},
    )

    def __str__(self):
        return self.titulo


class AlertaMalware(models.Model):
    juego = models.ForeignKey(Juego, on_delete=models.CASCADE)
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    detalles_analisis = models.TextField(help_text="Detalles del escáner (ej. VirusTotal)")
    resuelta = models.BooleanField(default=False)

    def __str__(self):
        return f"Alerta de Malware en: {self.juego.titulo}"


class LicenciaCompra(models.Model):
    ORIGENES = (
        ("compra", "Compra"),
        ("desarrollador", "Gratis - Desarrollador"),
        ("admin", "Gratis - Administrador / Dios"),
    )

    jugador = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name="licencias",
    )
    juego = models.ForeignKey(Juego, on_delete=models.CASCADE, related_name="licencias")
    edicion = models.CharField(max_length=20, default="Estándar")
    clave = models.CharField(max_length=40, unique=True)
    origen = models.CharField(max_length=20, choices=ORIGENES, default="compra")
    fecha_compra = models.DateTimeField(auto_now_add=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.juego.titulo} - {self.edicion} - {self.jugador.usuario.username}"
