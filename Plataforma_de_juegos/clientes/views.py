import secrets
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from administrador.models import DetallePedido, Juego, LicenciaCompra, Pedido, PerfilUsuario
from dios.authz import is_dios
from .forms import PerfilUsuarioForm
from .models import CarritoItem


EDITION_EXTRA = {"Estándar": Decimal("0.00"), "Deluxe": Decimal("12.00"), "Ultimate": Decimal("28.00")}


class CheckoutError(Exception):
    """Error de negocio que debe cancelar por completo el checkout."""


def _profile(user):
    try:
        return user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        return None


def _banned(user):
    profile = _profile(user)
    return bool(profile and profile.baneado)


def _make_key(prefix="ARGGAMES"):
    while True:
        value = prefix + "-" + "-".join(secrets.token_hex(2).upper() for _ in range(3))
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


def _price(game, edition):
    return game.precio + EDITION_EXTRA.get(edition, Decimal("0.00"))


def _cart_context(profile):
    cart_items = []
    cart_total = Decimal("0.00")
    for item in CarritoItem.objects.filter(perfil=profile).select_related("juego"):
        if item.juego.estado != "publicado":
            continue
        price = _price(item.juego, item.edicion)
        line_total = price * item.cantidad
        cart_items.append({
            "id": item.pk, "index": item.pk, "game": item.juego,
            "edition": item.edicion, "quantity": item.cantidad,
            "price": price, "line_total": line_total,
        })
        cart_total += line_total
    return {"cart_items": cart_items, "cart_total": cart_total}


def autenticacion(request):
    if request.user.is_authenticated:
        return redirect("administrador:catalogo")
    return render(request, "plataforma/auth.html", {"tab": request.GET.get("tab", "login")})


@login_required
def carrito(request):
    profile = _profile(request.user)
    if not profile:
        messages.error(request, "Tu cuenta no tiene un perfil ARG GAMES.")
        return redirect("clientes:auth")
    return render(request, "plataforma/carrito.html", _cart_context(profile))


@login_required
def biblioteca(request):
    profile = _profile(request.user)
    if not profile:
        messages.error(request, "Tu cuenta no tiene un perfil ARG GAMES.")
        return redirect("clientes:auth")
    licencias = LicenciaCompra.objects.filter(jugador=profile).select_related("juego").order_by("-fecha_compra")
    return render(request, "plataforma/biblioteca.html", {"licencias": licencias, "perfil": profile})


@require_POST
def login_view(request):
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        messages.error(request, "Correo o contraseña incorrectos.")
        return redirect("/usuarios/autenticacion/?tab=login")
    if _banned(user):
        messages.error(request, "Tu cuenta está baneada y no puede iniciar sesión.")
        return redirect("/usuarios/autenticacion/?tab=login")
    authenticated = authenticate(request, username=user.username, password=password)
    if authenticated is None:
        messages.error(request, "Correo o contraseña incorrectos.")
        return redirect("/usuarios/autenticacion/?tab=login")
    login(request, authenticated)
    messages.success(request, f"Bienvenido a ARG GAMES, {authenticated.username}.")
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
            if birth_date > date.today():
                raise ValueError
        except ValueError:
            messages.error(request, "La fecha de nacimiento no es válida.")
            return redirect("/usuarios/autenticacion/?tab=regUser")
    candidate = User(username=_unique_username(name), email=email)
    try:
        validate_password(password, user=candidate)
    except ValidationError as exc:
        for error in exc.messages:
            messages.error(request, error)
        return redirect("/usuarios/autenticacion/?tab=regUser")
    with transaction.atomic():
        user = User.objects.create_user(username=candidate.username, email=email, password=password)
        PerfilUsuario.objects.create(usuario=user, rol="jugador", fecha_nacimiento=birth_date)
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
    candidate = User(username=_unique_username(studio), email=email)
    try:
        validate_password(password, user=candidate)
    except ValidationError as exc:
        for error in exc.messages:
            messages.error(request, error)
        return redirect("/usuarios/autenticacion/?tab=regDev")
    with transaction.atomic():
        user = User.objects.create_user(username=candidate.username, email=email, password=password)
        PerfilUsuario.objects.create(usuario=user, rol="desarrollador", nombre_estudio=studio, tax_id=tax_id)
    login(request, user)
    messages.success(request, f'Estudio "{studio}" registrado como desarrollador.')
    return redirect("administrador:catalogo")


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect("administrador:catalogo")


@login_required
@require_POST
def carrito_agregar(request, game_id):
    profile = _profile(request.user)
    if not profile or _banned(request.user):
        messages.error(request, "Tu cuenta no puede usar el carrito.")
        return redirect("clientes:auth")
    game = get_object_or_404(Juego, pk=game_id, estado="publicado")
    edition = request.POST.get("edition", "Estándar")
    if edition not in EDITION_EXTRA:
        edition = "Estándar"
    item = CarritoItem.objects.filter(perfil=profile, juego=game, edicion=edition).first()
    desired_quantity = (item.cantidad if item else 0) + 1
    if desired_quantity > game.stock:
        messages.error(request, "No hay stock suficiente para agregar otra unidad.")
    elif item:
        item.cantidad = desired_quantity
        item.save(update_fields=["cantidad"])
        messages.success(request, f'"{game.titulo} ({edition})" se agregó al carrito.')
    else:
        CarritoItem.objects.create(perfil=profile, juego=game, edicion=edition, cantidad=1)
        messages.success(request, f'"{game.titulo} ({edition})" se agregó al carrito.')
    return redirect("clientes:carrito")


@login_required
@require_POST
def carrito_eliminar(request, index):
    profile = _profile(request.user)
    if not profile:
        return redirect("clientes:auth")
    item = get_object_or_404(CarritoItem, pk=index, perfil=profile)
    item.delete()
    messages.info(request, "Producto eliminado del carrito.")
    return redirect("clientes:carrito")


@login_required
@require_POST
def checkout(request):
    profile = _profile(request.user)
    if _banned(request.user) or not profile or profile.rol not in ("jugador", "desarrollador"):
        messages.error(request, "Esta cuenta no puede realizar compras.")
        return redirect("administrador:catalogo")
    try:
        with transaction.atomic():
            cart_items = list(
                CarritoItem.objects.select_for_update().filter(perfil=profile)
                .select_related("juego").order_by("juego_id", "pk")
            )
            if not cart_items:
                raise CheckoutError("Tu carrito está vacío.")
            game_ids = sorted({item.juego_id for item in cart_items})
            locked_games = {
                game.pk: game
                for game in Juego.objects.select_for_update()
                .filter(pk__in=game_ids, estado="publicado").order_by("pk")
            }
            if len(locked_games) != len(game_ids):
                raise CheckoutError("Uno de los juegos ya no está publicado. No se realizó ninguna compra.")
            for item in cart_items:
                game = locked_games[item.juego_id]
                if item.cantidad < 1 or game.stock < item.cantidad:
                    raise CheckoutError(f"Stock insuficiente para {game.titulo}. No se realizó ninguna compra.")
            order = Pedido.objects.create(usuario=profile, estado="pendiente", total=Decimal("0.00"))
            total = Decimal("0.00")
            for item in cart_items:
                game = locked_games[item.juego_id]
                unit_price = _price(game, item.edicion)
                DetallePedido.objects.create(
                    pedido=order, juego=game, cantidad=item.cantidad,
                    precio_unitario=unit_price, edicion=item.edicion,
                )
                game.stock -= item.cantidad
                game.save(update_fields=["stock"])
                for _ in range(item.cantidad):
                    LicenciaCompra.objects.create(
                        jugador=profile, juego=game, pedido=order, edicion=item.edicion,
                        clave=_make_key(), origen="compra", monto_pagado=unit_price,
                    )
                total += unit_price * item.cantidad
            order.total = total
            order.estado = "completado"
            order.save(update_fields=["total", "estado"])
            CarritoItem.objects.filter(pk__in=[item.pk for item in cart_items]).delete()
    except CheckoutError as exc:
        messages.error(request, str(exc))
        return redirect("clientes:carrito")
    except IntegrityError:
        messages.error(request, "No se pudo completar la compra por un conflicto de datos. El carrito se conservó.")
        return redirect("clientes:carrito")
    messages.success(request, f"Pedido #{order.pk} completado. Total: US$ {order.total}.")
    return redirect("clientes:pedido_detalle", pedido_id=order.pk)


@login_required
def perfil(request):
    profile = _profile(request.user)
    if not profile:
        messages.error(request, "Tu cuenta no tiene un perfil ARG GAMES.")
        return redirect("clientes:auth")
    if request.method == "POST":
        form = PerfilUsuarioForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("clientes:perfil")
    else:
        form = PerfilUsuarioForm(instance=profile)
    return render(request, "plataforma/perfil.html", {"form": form, "perfil": profile})


@login_required
def pedidos(request):
    profile = _profile(request.user)
    if not profile:
        return redirect("clientes:auth")
    order_list = Pedido.objects.filter(usuario=profile).prefetch_related("detalles__juego")
    return render(request, "plataforma/pedidos.html", {"pedidos": order_list})


@login_required
def pedido_detalle(request, pedido_id):
    profile = _profile(request.user)
    if not profile:
        return redirect("clientes:auth")
    pedido = get_object_or_404(
        Pedido.objects.prefetch_related("detalles__juego", "licencias"),
        pk=pedido_id, usuario=profile,
    )
    return render(request, "plataforma/pedido_detalle.html", {"pedido": pedido})


@login_required
@require_POST
def generar_clave(request, game_id):
    game = get_object_or_404(Juego, pk=game_id, estado="publicado")
    profile = _profile(request.user)
    if not profile:
        messages.error(request, "Tu cuenta no tiene un perfil ARG GAMES.")
        return redirect("administrador:catalogo")
    edition = request.POST.get("edition", "Estándar")
    if edition not in EDITION_EXTRA:
        edition = "Estándar"
    is_owner = profile.rol == "desarrollador" and game.desarrollador_id == profile.id
    if not (is_dios(request.user) or is_owner):
        messages.error(request, "Solo podés generar claves gratis para tus propios juegos.")
        return redirect("administrador:catalogo")
    LicenciaCompra.objects.create(
        jugador=profile, juego=game, edicion=edition,
        clave=_make_key("GOD" if is_dios(request.user) else "DEV"),
        origen="admin" if is_dios(request.user) else "desarrollador",
        monto_pagado=Decimal("0.00"),
    )
    messages.success(request, f'Clave gratis de "{game.titulo}" ({edition}) generada.')
    return redirect("clientes:biblioteca")
