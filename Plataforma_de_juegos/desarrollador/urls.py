from django.urls import path

from . import views

app_name = "desarrollador"

urlpatterns = [
    path("publicar/", views.publicar_juego, name="publicar"),
    path("juego/<int:game_id>/precio/", views.editar_precio, name="editar_precio"),
]
