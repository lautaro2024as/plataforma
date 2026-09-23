from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Juego, LicenciaCompra, PerfilUsuario


def _perfil(request):
    if not request.user.is_authenticated:
        return None
    try:
        return request.user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        return None


def _edad(fecha_nacimiento):
    hoy = date.today()
    return (
        hoy.year
        - fecha_nacimiento.year
        - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    )


def _es_staff(request):
    return request.user.is_authenticated and request.user.is_staff


def catalogo_juegos(request):
    perfil = _perfil(request)
    juegos = (
        Juego.objects.filter(estado="publicado")
        .select_related("desarrollador__usuario")
        .order_by("-fecha_subida")
    )

    if not request.user.is_superuser:
        if not perfil or not perfil.fecha_nacimiento or _edad(perfil.fecha_nacimiento) < 18:
            juegos = juegos.filter(etiqueta_mas_18=False)

    juegos_list = list(juegos)

    licencias = []
    if perfil:
        licencias = list(
            LicenciaCompra.objects.filter(jugador=perfil)
            .select_related("juego")
            .order_by("-fecha_compra")
        )

    mis_juegos = []
    dev_revenue = Decimal("0")
    if perfil and perfil.rol == "desarrollador":
        mis_juegos = list(
            Juego.objects.filter(desarrollador=perfil)
            .select_related("desarrollador__usuario")
            .order_by("-fecha_subida")
        )
        dev_revenue = (
            LicenciaCompra.objects.filter(
                juego__desarrollador=perfil,
                origen="compra",
            ).aggregate(total=Sum("monto_pagado"))["total"]
            or Decimal("0")
        ) * Decimal("0.85")

    admin_games = []
    admin_metrics = None
    admin_user_rows = []

    if _es_staff(request):
        admin_users = User.objects.all().order_by("username")

        for account in admin_users:
            account_profile = getattr(account, "perfilusuario", None)
            if account.is_superuser:
                role_label = "ADMINISTRADOR"
            elif account.is_staff:
                role_label = "STAFF / MODERADOR"
            elif account_profile and account_profile.rol == "desarrollador":
                role_label = "DESARROLLADOR"
            else:
                role_label = "USUARIO"

            admin_user_rows.append(
                {
                    "user": account,
                    "profile": account_profile,
                    "role_label": role_label,
                    "strikes": account_profile.strikes if account_profile else 0,
                    "banned": account_profile.baneado if account_profile else False,
                    "can_moderate": not account.is_superuser or request.user.is_superuser,
                }
            )

        admin_games = list(
            Juego.objects.select_related("desarrollador__usuario")
            .all()
            .order_by("-fecha_subida")
        )

        platform_revenue = (
            LicenciaCompra.objects.filter(origen="compra").aggregate(
                total=Sum("monto_pagado")
            )["total"]
            or Decimal("0")
        ) * Decimal("0.15")

        admin_metrics = {
            "total_games": Juego.objects.filter(estado="publicado").count(),
            "total_users": User.objects.filter(is_superuser=False).count(),
            "total_devs": PerfilUsuario.objects.filter(rol="desarrollador").count(),
            "platform_revenue": platform_revenue,
        }

        if request.user.is_superuser:
            mis_juegos = admin_games

    cart_items = []
    cart_total = Decimal("0")
    raw_cart = request.session.get("nexus_cart", [])

    for index, item in enumerate(raw_cart):
        try:
            game = Juego.objects.get(pk=int(item.get("game_id", 0)), estado="publicado")
        except (Juego.DoesNotExist, ValueError, TypeError, AttributeError):
            continue

        edition = item.get("edition", "Estándar")
        extra = {
            "Estándar": Decimal("0"),
            "Deluxe": Decimal("12"),
            "Ultimate": Decimal("28"),
        }.get(edition, Decimal("0"))

        final_price = game.precio + extra
        cart_items.append(
            {
                "index": index,
                "game": game,
                "edition": edition,
                "price": final_price,
            }
        )
        cart_total += final_price

    game_data = []
    for game in juegos_list:
        price = str(game.precio)
        original = str(game.precio_original or game.precio)
        can_free = bool(
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or (
                    perfil
                    and perfil.rol == "desarrollador"
                    and game.desarrollador_id == perfil.id
                )
            )
        )
        game_data.append(
            {
                "id": game.id,
                "title": game.titulo,
                "category": game.categoria,
                "price": price,
                "original_price": original,
                "developer": (
                    game.desarrollador.nombre_estudio
                    or game.desarrollador.usuario.username
                ),
                "rating": str(game.calificacion),
                "image": game.imagen_url
                or "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=800&q=80",
                "description": game.descripcion,
                "key_type": game.tipo_clave,
                "can_free": can_free,
            }
        )

    contexto = {
        "juegos": juegos_list,
        "licencias": licencias,
        "mis_juegos": mis_juegos,
        "dev_revenue": dev_revenue,
        "admin_user_rows": admin_user_rows,
        "admin_games": admin_games,
        "admin_metrics": admin_metrics,
        "perfil": perfil,
        "game_data": game_data,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "active_view": request.GET.get("view", "store"),
    }

    return render(request, "catalogo.html", contexto)


@user_passes_test(_es_staff)
def panel(request):
    return redirect("/?view=admin")


def _moderation_allowed(request, target):
    if not _es_staff(request):
        return False
    if target.is_superuser:
        return request.user.is_superuser
    return True


@require_POST
def add_strike(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if not _moderation_allowed(request, target):
        return HttpResponseForbidden("No tenés permisos para moderar esta cuenta.")

    perfil = getattr(target, "perfilusuario", None)
    if not perfil:
        perfil = PerfilUsuario.objects.create(usuario=target)

    perfil.strikes += 1
    if perfil.strikes >= 3:
        perfil.baneado = True
        messages.error(request, f"{target.username} alcanzó 3 strikes y fue baneado.")
    else:
        messages.warning(request, f"Strike aplicado a {target.username}: {perfil.strikes}/3.")
    perfil.save(update_fields=["strikes", "baneado"])
    return redirect("/?view=admin")


@require_POST
def toggle_ban(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if not _moderation_allowed(request, target):
        return HttpResponseForbidden("No tenés permisos para moderar esta cuenta.")

    perfil = getattr(target, "perfilusuario", None)
    if not perfil:
        perfil = PerfilUsuario.objects.create(usuario=target)

    perfil.baneado = not perfil.baneado
    if not perfil.baneado:
        perfil.strikes = 0
        messages.success(request, f"{target.username} fue desbaneado y sus strikes se reiniciaron.")
    else:
        messages.error(request, f"{target.username} fue baneado.")
    perfil.save(update_fields=["strikes", "baneado"])
    return redirect("/?view=admin")


@require_POST
def delete_game(request, game_id):
    if not _es_staff(request):
        return HttpResponseForbidden("No tenés permisos para eliminar juegos.")
    game = get_object_or_404(Juego, pk=game_id)
    title = game.titulo
    game.delete()
    messages.error(request, f'El juego "{title}" fue eliminado.')
    return redirect("/?view=admin")


@require_POST
def toggle_staff(request, user_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden("Solo el superadministrador puede asignar staff.")

    target = get_object_or_404(User, pk=user_id)
    if target.is_superuser:
        return HttpResponseForbidden("Los superusuarios no necesitan esta acción.")

    target.is_staff = not target.is_staff
    target.save(update_fields=["is_staff"])
    messages.info(
        request,
        f"{target.username} ahora {'forma parte del staff' if target.is_staff else 'ya no forma parte del staff'}.",
    )
    return redirect("/?view=admin")
