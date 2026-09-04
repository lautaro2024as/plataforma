"""
URL configuration for Plataforma_de_juegos project.
"""
from django.contrib import admin
from django.urls import path
from administrador.omega_system import system_stats
from administrador.omega_local_wallpaper import activate as wallpaper_activate, delete as wallpaper_delete, listing as wallpaper_list, panel as wallpaper_panel, upload as wallpaper_upload, video as wallpaper_video
from administrador.omega_music import music_delete, music_list, music_player, music_stream, music_upload

urlpatterns = [
    path('admin/omega/system-stats/', system_stats, name='omega-system-stats'),
    path('admin/omega/wallpapers/', wallpaper_panel, name='omega-wallpapers'),
    path('admin/omega/wallpapers/list/', wallpaper_list, name='omega-wallpaper-list'),
    path('admin/omega/wallpapers/upload/', wallpaper_upload, name='omega-wallpaper-upload'),
    path('admin/omega/wallpapers/set/', wallpaper_activate, name='omega-wallpaper-set'),
    path('admin/omega/wallpapers/delete/', wallpaper_delete, name='omega-wallpaper-delete'),
    path('admin/omega/wallpapers/video/', wallpaper_video, name='omega-wallpaper-video'),
    path('admin/omega/music/', music_player, name='omega-music-player'),
    path('admin/omega/music/list/', music_list, name='omega-music-list'),
    path('admin/omega/music/upload/', music_upload, name='omega-music-upload'),
    path('admin/omega/music/stream/<str:music_id>/', music_stream, name='omega-music-stream'),
    path('admin/omega/music/delete/<str:music_id>/', music_delete, name='omega-music-delete'),
    path('admin/', admin.site.urls),
]
