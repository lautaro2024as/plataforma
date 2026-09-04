"""
URL configuration for Plataforma_de_juegos project.
"""
from django.contrib import admin
from django.urls import path
from administrador.omega_system import system_stats

urlpatterns = [
    path('admin/omega/system-stats/', system_stats, name='omega-system-stats'),
    path('admin/', admin.site.urls),
]
