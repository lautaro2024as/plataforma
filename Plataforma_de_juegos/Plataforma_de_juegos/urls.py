"""
URL configuration for Plataforma_de_juegos project.
"""
from django.contrib import admin
from django.urls import path
from administrador.omega_system import system_stats
from administrador.omega_wallpaper import wallpaper_import, wallpaper_list, wallpaper_panel, wallpaper_preview, wallpaper_set
from administrador.omega_portable import activate as portable_activate, import_bundle as portable_import, listing as portable_list, panel as portable_panel, preview as portable_preview
from administrador.omega_music import music_delete, music_list, music_player, music_stream, music_upload
from administrador.omega_scene_engine import scene_frame

urlpatterns = [
    path('admin/omega/system-stats/', system_stats, name='omega-system-stats'),
    # OMEGA portable wallpaper engine is intentionally first: these routes replace the old
    # path-based selector without breaking the existing route names used by the admin UI.
    path('admin/omega/wallpapers/', portable_panel, name='omega-wallpapers'),
    path('admin/omega/wallpapers/list/', portable_list, name='omega-wallpaper-list'),
    path('admin/omega/wallpapers/import/', portable_import, name='omega-wallpaper-import'),
    path('admin/omega/wallpapers/preview/', portable_preview, name='omega-wallpaper-preview'),
    path('admin/omega/wallpapers/activate/', portable_activate, name='omega-wallpaper-set'),
    path('admin/omega/wallpapers/render/<str:wallpaper_id>/', scene_frame, name='omega-wallpaper-render'),
    path('admin/omega/wallpapers/legacy-set/', wallpaper_set, name='omega-wallpaper-legacy-set'),
    path('admin/omega/wallpapers/legacy/', wallpaper_panel, name='omega-wallpaper-legacy'),
    path('admin/omega/wallpapers/legacy-list/', wallpaper_list, name='omega-wallpaper-legacy-list'),
    path('admin/omega/wallpapers/legacy-import/', wallpaper_import, name='omega-wallpaper-legacy-import'),
    path('admin/omega/wallpapers/legacy-preview/', wallpaper_preview, name='omega-wallpaper-legacy-preview'),
    path('admin/omega/music/', music_player, name='omega-music-player'),
    path('admin/omega/music/list/', music_list, name='omega-music-list'),
    path('admin/omega/music/upload/', music_upload, name='omega-music-upload'),
    path('admin/omega/music/stream/<str:music_id>/', music_stream, name='omega-music-stream'),
    path('admin/omega/music/delete/<str:music_id>/', music_delete, name='omega-music-delete'),
    path('admin/', admin.site.urls),
]
