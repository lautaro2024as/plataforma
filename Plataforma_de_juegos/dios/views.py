from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from administrador.models import Juego, LicenciaCompra, PerfilUsuario
from clientes.views import EDITION_EXTRA, _make_key

from .authz import dios_required
from .models import AdministradorEspecial, DiosCuenta


@dios_required
def dashboard(request):
    admins = (
        AdministradorEspecial.objects.select_related("usuario", "creado_por")
        .all()
        .order_by("usuario__username")
    )
    users = (
        PerfilUsuario.objects.select_related("usuario")
        .filter(rol__in=["jugador", "desarrollador"])
        .order_by("usuario__username")
    )
    games = Juego.objects.select_related("desarrollador__usuario").all().order_by("-fecha_subida")
    return render(
        request,
        "plataforma/dios/dashboard.html",
        {
            "dios_cuenta": DiosCuenta.objects.get(usuario=request.user),
            "admins": admins,
            "usuarios": users,
            "juegos": games,
            "ediciones": EDITION_EXTRA.keys(),
        },
    )


@dios_required
@require_POST
def crear_admin(request):
    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")
    if not username or not email or not password:
        messages.error(request, "Completá usuario, correo y contraseña.")
        return redirect("dios:dashboard")

    if User.objects.filter(username=username).exists():
        messages.error(request, "Ese nombre de usuario ya existe.")
        return redirect("dios:dashboard")

    if User.objects.filter(email__iexact=email).exists():
        messages.error(request, "Ese correo ya está registrado.")
        return redirect("dios:dashboard")

    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=False,
            is_active=True,
        )
        PerfilUsuario.objects.create(
            usuario=user,
            rol="administrador",
        )
        AdministradorEspecial.objects.create(
            usuario=user,
            creado_por=request.user,
            activo=True,
            puede_strike_usuario=bool(request.POST.get("puede_strike_usuario")),
            puede_ban_usuario=bool(request.POST.get("puede_ban_usuario")),
            puede_eliminar_usuario=bool(request.POST.get("puede_eliminar_usuario")),
            puede_strike_desarrollador=bool(request.POST.get("puede_strike_desarrollador")),
            puede_ban_desarrollador=bool(request.POST.get("puede_ban_desarrollador")),
            puede_eliminar_desarrollador=bool(request.POST.get("puede_eliminar_desarrollador")),
            puede_eliminar_juegos=bool(request.POST.get("puede_eliminar_juegos")),
            puede_generar_claves=bool(request.POST.get("puede_generar_claves")),
        )

    messages.success(request, f"Administrador especial '{username}' creado.")
    return redirect("dios:dashboard")


@dios_required
@require_POST
def editar_permisos_admin(request, user_id):
    admin = get_object_or_404(
        AdministradorEspecial.objects.select_related("usuario"),
        usuario_id=user_id,
    )
    admin.activo = bool(request.POST.get("activo"))
    admin.usuario.is_staff = admin.activo
    admin.usuario.save(update_fields=["is_staff"])

    for field in (
        "puede_strike_usuario",
        "puede_ban_usuario",
        "puede_eliminar_usuario",
        "puede_strike_desarrollador",
        "puede_ban_desarrollador",
        "puede_eliminar_desarrollador",
        "puede_eliminar_juegos",
        "puede_generar_claves",
    ):
        setattr(admin, field, bool(request.POST.get(field)))

    admin.save()
    messages.success(request, f"Permisos de '{admin.usuario.username}' actualizados.")
    return redirect("dios:dashboard")


@dios_required
@require_POST
def desactivar_admin(request, user_id):
    admin = get_object_or_404(AdministradorEspecial, usuario_id=user_id)
    admin.activo = False
    admin.save(update_fields=["activo"])
    admin.usuario.is_staff = False
    admin.usuario.save(update_fields=["is_staff"])
    messages.warning(request, f"Administrador especial '{admin.usuario.username}' desactivado.")
    return redirect("dios:dashboard")


@dios_required
@require_POST
def generar_clave(request):
    game = get_object_or_404(
        Juego,
        pk=request.POST.get("game_id"),
        estado="publicado",
    )
    recipient = get_object_or_404(
        PerfilUsuario,
        pk=request.POST.get("recipient_id"),
        rol__in=["jugador", "desarrollador"],
    )
    edition = request.POST.get("edition", "Estándar")
    if edition not in EDITION_EXTRA:
        edition = "Estándar"

    LicenciaCompra.objects.create(
        jugador=recipient,
        juego=game,
        edicion=edition,
        clave=_make_key("GOD"),
        origen="admin",
        monto_pagado=0,
    )
    messages.success(
        request,
        f"Clave gratis generada para {recipient.usuario.username}: "
        f"{game.titulo} ({edition}).",
    )
    return redirect("dios:dashboard")
