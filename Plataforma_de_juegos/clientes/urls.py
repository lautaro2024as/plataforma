from django.urls import path

from . import views

app_name = "clientes"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("registro/usuario/", views.register_user, name="registro_usuario"),
    path("registro/desarrollador/", views.register_developer, name="registro_desarrollador"),
    path("logout/", views.logout_view, name="logout"),
    path("carrito/agregar/<int:game_id>/", views.carrito_agregar, name="carrito_agregar"),
    path("carrito/eliminar/<int:index>/", views.carrito_eliminar, name="carrito_eliminar"),
    path("carrito/checkout/", views.checkout, name="checkout"),
    path("biblioteca/clave/<int:game_id>/", views.generar_clave, name="generar_clave"),
]
