"""
URL configuration for Plataforma_de_juegos project.
"""
from django.contrib import admin
from django.urls import path
from administrador.omega_system import system_stats
from administrador.omega_wallpaper import wallpaper_list, wallpaper_panel, wallpaper_set

urlpatterns = [
    path('admin/omega/system-stats/', system_stats, name='omega-system-stats'),
    path('admin/omega/wallpapers/', wallpaper_panel, name='omega-wallpapers'),
    path('admin/omega/wallpapers/list/', wallpaper_list, name='omega-wallpaper-list'),
    path('admin/omega/wallpapers/set/', wallpaper_set, name='omega-wallpaper-set'),
    path('admin/', admin.site.urls),
]
