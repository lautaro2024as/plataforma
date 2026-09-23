from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from dios.authz import has_admin_permission, is_admin_especial, is_dios
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


def _es_admin(request):
    return request.user.is_authenticated and (
        is_dios(request.user) or is_admin_especial(request.user)
    )


def catalogo_juegos(request):
    perfil = _perfil(request)
    juegos = (
        Juego.objects.filter(estado="publicado")
        .select_related("desarrollador__usuario")
        .order_by("-fecha_subida")
    )

    privilegiado = _es_admin(request)
    if not privilegiado:
        if not perfil or not perfil.fecha_nacimiento or _edad(perfil.fecha_nacimiento) < 18:
            juegos = juegos.filter(etiqueta_mas_18=False)

    juegos_list = list(juegos)

    licencias = []
    if perfil and perfil.rol in ("jugador", "desarrollador"):
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

    if _es_admin(request):
        for account in User.objects.all().order_by("username"):
            account_profile = getattr(account, "perfilusuario", None)
            if is_dios(account):
                role_label = "DIOS"
            elif account_profile and account_profile.rol == "administrador":
                role_label = "ADMINISTRADOR ESPECIAL"
            elif account_profile and account_profile.rol == "desarrollador":
                role_label = "DESARROLLADOR"
            else:
                role_label = "USUARIO"

            is_target_admin = bool(
                account_profile and account_profile.rol == "administrador"
            )
            is_target_dios = is_dios(account)

            admin_user_rows.append(
                {
                    "user": account,
                    "profile": account_profile,
                    "role_label": role_label,
                    "strikes": account_profile.strikes if account_profile else 0,
                    "banned": account_profile.baneado if account_profile else False,
                    "can_strike": (
                        not is_target_admin
                        and not is_target_dios
                        and bool(
                            is_dios(request.user)
                            or (
                                account_profile
                                and has_admin_permission(
                                    request.user,
                                    "strike_desarrollador"
                                    if account_profile.rol == "desarrollador"
                                    else "strike_usuario",
                                )
                            )
                        )
                    ),
                    "can_ban": (
                        not is_target_admin
                        and not is_target_dios
                        and bool(
                            is_dios(request.user)
                            or (
                                account_profile
                                and has_admin_permission(
                                    request.user,
                                    "ban_desarrollador"
                                    if account_profile.rol == "desarrollador"
                                    else "ban_usuario",
                                )
                            )
                        )
                    ),
                    "can_delete": (
                        not is_target_admin
                        and not is_target_dios
                        and bool(
                            is_dios(request.user)
                            or (
                                account_profile
                                and has_admin_permission(
                                    request.user,
                                    "eliminar_desarrollador"
                                    if account_profile.rol == "desarrollador"
                                    else "eliminar_usuario",
                                )
                            )
                        )
                    ),
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
            "total_users": User.objects.filter(
                is_superuser=False,
            ).exclude(
                perfilusuario__rol="administrador",
            ).count(),
            "total_devs": PerfilUsuario.objects.filter(rol="desarrollador").count(),
            "platform_revenue": platform_revenue,
        }

    cart_items = []
    cart_total = Decimal("0")
    raw_cart = request.session.get("nexus_cart", [])

    for index, item in enumerate(raw_cart):
        try:
            game = Juego.objects.get(pk=int(item.get("game_id", 0)), estado="publicado")
        except (Juego.DoesNotExist, ValueError, TypeError, AttributeError, KeyError):
            continue

        edition = item.get("edition", "Estándar")
        extra = {
            "Estándar": Decimal("0"),
            "Deluxe": Decimal("12"),
            "Ultimate": Decimal("28"),
        }.get(edition, Decimal("0"))

        final_price = game.precio + extra
        cart_items.append(
            {"index": index, "game": game, "edition": edition, "price": final_price}
        )
        cart_total += final_price

    game_data = []
    for game in juegos_list:
        game_data.append(
            {
                "id": game.id,
                "title": game.titulo,
                "category": game.categoria,
                "price": str(game.precio),
                "original_price": str(game.precio_original or game.precio),
                "developer": game.desarrollador.nombre_estudio or game.desarrollador.usuario.username,
                "rating": str(game.calificacion),
                "image": game.imagen_url
                or "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=800&q=80",
                "description": game.descripcion,
                "key_type": game.tipo_clave,
                "can_free": bool(
                    perfil
                    and perfil.rol == "desarrollador"
                    and game.desarrollador_id == perfil.id
                ),
            }
        )

    return render(
        request,
        "catalogo.html",
        {
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
        },
    )


def _required_permission(request, target, action):
    if is_dios(request.user):
        return True

    profile = getattr(target, "perfilusuario", None)
    if not profile or profile.rol == "administrador" or is_dios(target):
        return False

    permission = {
        ("jugador", "strike"): "strike_usuario",
        ("jugador", "ban"): "ban_usuario",
        ("jugador", "delete"): "eliminar_usuario",
        ("desarrollador", "strike"): "strike_desarrollador",
        ("desarrollador", "ban"): "ban_desarrollador",
        ("desarrollador", "delete"): "eliminar_desarrollador",
    }.get((profile.rol, action))

    return bool(permission and has_admin_permission(request.user, permission))


@require_POST
def add_strike(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if not _es_admin(request) or not _required_permission(request, target, "strike"):
        return HttpResponseForbidden("No tenés permiso para dar strikes a esta cuenta.")

    profile = getattr(target, "perfilusuario", None)
    if not profile:
        return HttpResponseForbidden("La cuenta no tiene perfil.")

    profile.strikes += 1
    if profile.strikes >= 3:
        profile.baneado = True
        messages.error(request, f"{target.username} alcanzó 3 strikes y fue baneado.")
    else:
        messages.warning(request, f"Strike aplicado a {target.username}: {profile.strikes}/3.")
    profile.save(update_fields=["strikes", "baneado"])
    return redirect("/?view=admin")


@require_POST
def toggle_ban(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if not _es_admin(request) or not _required_permission(request, target, "ban"):
        return HttpResponseForbidden("No tenés permiso para banear esta cuenta.")

    profile = getattr(target, "perfilusuario", None)
    if not profile:
        return HttpResponseForbidden("La cuenta no tiene perfil.")

    profile.baneado = not profile.baneado
    if not profile.baneado:
        profile.strikes = 0
        messages.success(request, f"{target.username} fue desbaneado.")
    else:
        messages.error(request, f"{target.username} fue baneado.")
    profile.save(update_fields=["strikes", "baneado"])
    return redirect("/?view=admin")


@require_POST
def delete_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if not _es_admin(request) or not _required_permission(request, target, "delete"):
        return HttpResponseForbidden("No tenés permiso para eliminar esta cuenta.")
    if target == request.user:
        return HttpResponseForbidden("No podés eliminar tu propia cuenta desde este panel.")

    username = target.username
    target.delete()
    messages.error(request, f"La cuenta '{username}' fue eliminada.")
    return redirect("/?view=admin")


@require_POST
def delete_game(request, game_id):
    if not _es_admin(request):
        return HttpResponseForbidden("No tenés acceso a este panel.")

    if not (
        is_dios(request.user)
        or has_admin_permission(request.user, "eliminar_juegos")
    ):
        return HttpResponseForbidden("No tenés permiso para eliminar juegos.")

    game = get_object_or_404(Juego, pk=game_id)
    title = game.titulo
    game.delete()
    messages.error(request, f'El juego "{title}" fue eliminado.')
    return redirect("/?view=admin")


@require_POST
def toggle_staff(request, user_id):
    return HttpResponseForbidden(
        "Los administradores especiales se gestionan exclusivamente desde Dios."
    )
