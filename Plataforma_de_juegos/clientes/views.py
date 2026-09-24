import secrets
from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from administrador.models import Juego, LicenciaCompra, PerfilUsuario
from dios.authz import is_dios


EDITION_EXTRA = {
    "Estándar": 0,
    "Deluxe": 12,
    "Ultimate": 28,
}


def _profile(user):
    try:
        return user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        return None


def _banned(user):
    profile = _profile(user)
    return bool(profile and profile.baneado)


def _make_key(prefix="NEXUS"):
    while True:
        value = prefix + "-" + "-".join(
            secrets.token_hex(2).upper() for _ in range(3)
        )
        if not LicenciaCompra.objects.filter(clave=value).exists():
            return value


def _unique_username(value):
    base = slugify(value)[:130] or "usuario"
    candidate = base
    counter = 2
    while User.objects.filter(username=candidate).exists():
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate




def _cart_context(request):
    cart_items = []
    cart_total = 0

    for index, item in enumerate(request.session.get("nexus_cart", [])):
        try:
            game = Juego.objects.get(
                pk=int(item.get("game_id", 0)),
                estado="publicado",
            )
        except (Juego.DoesNotExist, ValueError, TypeError, AttributeError, KeyError):
            continue

        edition = item.get("edition", "Estándar")
        extra = EDITION_EXTRA.get(edition, 0)
        price = game.precio + extra
        cart_items.append({"index": index, "game": game, "edition": edition, "price": price})
        cart_total += price

    return {"cart_items": cart_items, "cart_total": cart_total}


def autenticacion(request):
    if request.user.is_authenticated:
        return redirect("administrador:catalogo")
    return render(request, "plataforma/auth.html", {"tab": request.GET.get("tab", "login")})


def carrito(request):
    return render(request, "plataforma/carrito.html", _cart_context(request))


@login_required
def biblioteca(request):
    profile = _profile(request.user)
    if not profile:
        messages.error(request, "Tu cuenta no tiene un perfil NEXUS.")
        return redirect("clientes:auth")
    licencias = list(
        LicenciaCompra.objects.filter(jugador=profile)
        .select_related("juego")
        .order_by("-fecha_compra")
    )
    return render(request, "plataforma/biblioteca.html", {"licencias": licencias, "perfil": profile})

@require_POST
def login_view(request):
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        messages.error(request, "No existe ninguna cuenta con ese correo.")
        return redirect("/usuarios/autenticacion/?tab=login")

    if _banned(user):
        messages.error(request, "Tu cuenta está baneada y no puede iniciar sesión.")
        return redirect("/usuarios/autenticacion/?tab=login")

    authenticated = authenticate(request, username=user.username, password=password)
    if authenticated is None:
        messages.error(request, "Correo o contraseña incorrectos.")
        return redirect("/usuarios/autenticacion/?tab=login")

    login(request, authenticated)
    messages.success(request, f"Bienvenido a NEXUS, {authenticated.username}.")
    return redirect("administrador:catalogo")


@require_POST
def register_user(request):
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")
    birth = request.POST.get("fecha_nacimiento", "").strip()

    if not name or not email or not password:
        messages.error(request, "Completá nombre, correo y contraseña.")
        return redirect("/usuarios/autenticacion/?tab=regUser")

    if User.objects.filter(email__iexact=email).exists():
        messages.error(request, "Ese correo ya está registrado.")
        return redirect("/usuarios/autenticacion/?tab=regUser")

    birth_date = None
    if birth:
        try:
            birth_date = date.fromisoformat(birth)
        except ValueError:
            messages.error(request, "La fecha de nacimiento no es válida.")
            return redirect("/usuarios/autenticacion/?tab=regUser")

    user = User.objects.create_user(
        username=_unique_username(name),
        email=email,
        password=password,
    )
    PerfilUsuario.objects.create(
        usuario=user,
        rol="jugador",
        fecha_nacimiento=birth_date,
    )
    login(request, user)
    messages.success(request, f"Cuenta creada. Bienvenido, {user.username}.")
    return redirect("administrador:catalogo")


@require_POST
def register_developer(request):
    studio = request.POST.get("studio", "").strip()
    email = request.POST.get("email", "").strip().lower()
    tax_id = request.POST.get("tax_id", "").strip()
    password = request.POST.get("password", "")

    if not studio or not email or not password:
        messages.error(request, "Completá estudio, correo y contraseña.")
        return redirect("/usuarios/autenticacion/?tab=regDev")

    if User.objects.filter(email__iexact=email).exists():
        messages.error(request, "Ese correo ya está registrado.")
        return redirect("/usuarios/autenticacion/?tab=regDev")

    user = User.objects.create_user(
        username=_unique_username(studio),
        email=email,
        password=password,
    )
    PerfilUsuario.objects.create(
        usuario=user,
        rol="desarrollador",
        nombre_estudio=studio,
        tax_id=tax_id,
    )
    login(request, user)
    messages.success(request, f'Estudio "{studio}" registrado como desarrollador.')
    return redirect("administrador:catalogo")


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect("administrador:catalogo")


@require_POST
def carrito_agregar(request, game_id):
    game = get_object_or_404(Juego, pk=game_id, estado="publicado")
    edition = request.POST.get("edition", "Estándar")
    if edition not in EDITION_EXTRA:
        edition = "Estándar"

    cart = request.session.get("nexus_cart", [])
    cart.append({"game_id": game.id, "edition": edition})
    request.session["nexus_cart"] = cart
    request.session.modified = True
    messages.success(request, f'"{game.titulo} ({edition})" se agregó al carrito.')
    return redirect("clientes:carrito")


@require_POST
def carrito_eliminar(request, index):
    cart = request.session.get("nexus_cart", [])
    if 0 <= index < len(cart):
        cart.pop(index)
        request.session["nexus_cart"] = cart
        request.session.modified = True
    return redirect("clientes:carrito")


@login_required
@require_POST
def checkout(request):
    if _banned(request.user):
        messages.error(request, "Una cuenta baneada no puede comprar.")
        return redirect("administrador:catalogo")

    profile = _profile(request.user)
    if not profile or profile.rol not in ("jugador", "desarrollador"):
        messages.error(request, "Esta cuenta no puede realizar compras.")
        return redirect("administrador:catalogo")

    cart = request.session.get("nexus_cart", [])
    if not cart:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("clientes:carrito")

    created = 0
    for item in cart:
        try:
            game = Juego.objects.get(pk=int(item["game_id"]), estado="publicado")
        except (Juego.DoesNotExist, ValueError, TypeError, KeyError):
            continue

        edition = item.get("edition", "Estándar")
        if edition not in EDITION_EXTRA:
            edition = "Estándar"

        final_price = game.precio + EDITION_EXTRA[edition]
        LicenciaCompra.objects.create(
            jugador=profile,
            juego=game,
            edicion=edition,
            clave=_make_key(),
            origen="compra",
            monto_pagado=final_price,
        )
        created += 1

    request.session["nexus_cart"] = []
    request.session.modified = True
    messages.success(request, f"Compra completada: {created} clave(s) agregada(s) a tu biblioteca.")
    return redirect("clientes:biblioteca")


@login_required
@require_POST
def generar_clave(request, game_id):
    game = get_object_or_404(Juego, pk=game_id, estado="publicado")
    profile = _profile(request.user)
    if not profile:
        messages.error(request, "Tu cuenta no tiene un perfil NEXUS.")
        return redirect("administrador:catalogo")

    edition = request.POST.get("edition", "Estándar")
    if edition not in EDITION_EXTRA:
        edition = "Estándar"

    is_owner = (
        profile.rol == "desarrollador"
        and game.desarrollador_id == profile.id
    )

    if not (is_dios(request.user) or is_owner):
        messages.error(request, "Solo podés generar claves gratis para tus propios juegos.")
        return redirect("administrador:catalogo")

    LicenciaCompra.objects.create(
        jugador=profile,
        juego=game,
        edicion=edition,
        clave=_make_key("GOD" if is_dios(request.user) else "DEV"),
        origen="admin" if is_dios(request.user) else "desarrollador",
        monto_pagado=0,
    )
    messages.success(request, f'Clave gratis de "{game.titulo}" ({edition}) generada.')
    return redirect("clientes:biblioteca")
