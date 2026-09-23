from django.urls import path

from . import views

app_name = "dios"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("admins/crear/", views.crear_admin, name="crear_admin"),
    path("admins/<int:user_id>/permisos/", views.editar_permisos_admin, name="editar_permisos"),
    path("admins/<int:user_id>/desactivar/", views.desactivar_admin, name="desactivar_admin"),
    path("keys/generar/", views.generar_clave, name="generar_clave"),
]
