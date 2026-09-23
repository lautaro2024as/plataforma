from django.urls import path

from . import views

app_name = "administrador"

urlpatterns = [
    path("", views.catalogo_juegos, name="catalogo"),
    path("panel/", views.panel, name="panel"),
    path("moderacion/<int:user_id>/strike/", views.add_strike, name="strike"),
    path("moderacion/<int:user_id>/ban/", views.toggle_ban, name="ban"),
    path("moderacion/<int:user_id>/staff/", views.toggle_staff, name="staff"),
    path("juegos/<int:game_id>/eliminar/", views.delete_game, name="eliminar_juego"),
]
