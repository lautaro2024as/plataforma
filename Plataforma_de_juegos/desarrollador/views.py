from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from administrador.models import Juego, PerfilUsuario

from .forms import PrecioJuegoForm, PublicarJuegoForm


def _perfil_dev(request):
    if not request.user.is_authenticated:
        return None
    try:
        profile = request.user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        return None
    if profile.rol != "desarrollador":
        return None
    return profile


@login_required
def publicar_juego(request):
    profile = _perfil_dev(request)
    if not profile:
        messages.error(request, "Solo una cuenta desarrolladora puede publicar juegos.")
        return redirect("/?view=dev")

    if request.method != "POST":
        return redirect("/?view=dev")

    form = PublicarJuegoForm(request.POST, request.FILES)
    if not form.is_valid():
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
        return redirect("/?view=dev")

    game = form.save(commit=False)
    game.desarrollador = profile
    game.estado = "publicado"
    if not game.precio_original:
        game.precio_original = game.precio
    game.save()

    messages.success(request, f'"{game.titulo}" fue publicado en la tienda.')
    return redirect("/?view=dev")


@login_required
def editar_precio(request, game_id):
    profile = _perfil_dev(request)
    if not profile:
        return redirect("/?view=dev")

    game = get_object_or_404(Juego, pk=game_id, desarrollador=profile)

    if request.method != "POST":
        return redirect("/?view=dev")

    form = PrecioJuegoForm(request.POST, instance=game)
    if not form.is_valid():
        messages.error(request, "Ingresá un precio válido.")
        return redirect("/?view=dev")

    form.save()
    messages.success(request, f'Precio de "{game.titulo}" actualizado.')
    return redirect("/?view=dev")
