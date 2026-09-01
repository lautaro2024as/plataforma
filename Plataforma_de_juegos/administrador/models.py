from django.db import models
from django.contrib.auth.models import User

# 1. Extendemos el usuario para guardar su rol, fecha de nacimiento (validador +18) y estado de baneo
class PerfilUsuario(models.Model):
    ROLES = (
        ('jugador', 'Jugador / Usuario'),
        ('desarrollador', 'Desarrollador Indie'),
    )
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, default='jugador')
    fecha_nacimiento = models.DateField(null=True, blank=True)
    baneado = models.BooleanField(default=False) # Para la acción de "Banear Desarrolladores"

    def __str__(self):
        return f"{self.usuario.username} ({self.get_rol_display()})"

# 2. El modelo del juego con sus etiquetas, precio y estados según el pipeline anti-malware
class Juego(models.Model):
    ESTADOS = (
        ('cuarentena', 'En Cuarentena (Análisis Anti-Malware)'),
        ('publicado', 'Publicado (Archivo Limpio)'),
        ('baneado', 'Baneado (Contenido Rechazado)'),
    )
    titulo = models.CharField(max_length=150)
    desarrollador = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, limit_choices_to={'rol': 'desarrollador'})
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    etiqueta_mas_18 = models.BooleanField(default=False) # Filtro SQL +18
    # Aquí se guardaría el .exe (por ejemplo, compilados de motores gráficos)
    archivo_exe = models.FileField(upload_to='juegos_exe/', null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='cuarentena')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

# 3. Módulo para el Sistema de Moderación y Auditoría
class AlertaMalware(models.Model):
    juego = models.ForeignKey(Juego, on_delete=models.CASCADE)
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    detalles_analisis = models.TextField(help_text="Detalles del escáner (ej. VirusTotal)")
    resuelta = models.BooleanField(default=False)

    def __str__(self):
        return f"Alerta de Malware en: {self.juego.titulo}"

# 4. Módulo de Pagos y Licencias
class LicenciaCompra(models.Model):
    jugador = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, limit_choices_to={'rol': 'jugador'})
    juego = models.ForeignKey(Juego, on_delete=models.CASCADE)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Licencia de {self.juego.titulo} - Propietario: {self.jugador.usuario.username}"