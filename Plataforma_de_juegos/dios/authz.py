from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .models import AdministradorEspecial, DiosCuenta


PERMISOS = {
    "strike_usuario": "puede_strike_usuario",
    "ban_usuario": "puede_ban_usuario",
    "eliminar_usuario": "puede_eliminar_usuario",
    "strike_desarrollador": "puede_strike_desarrollador",
    "ban_desarrollador": "puede_ban_desarrollador",
    "eliminar_desarrollador": "puede_eliminar_desarrollador",
    "eliminar_juegos": "puede_eliminar_juegos",
    "generar_claves": "puede_generar_claves",
}


def is_dios(user):
    if not getattr(user, "is_authenticated", False):
        return False
    return DiosCuenta.objects.filter(usuario=user, activo=True).exists()


def get_admin_especial(user):
    if not getattr(user, "is_authenticated", False):
        return None
    try:
        admin = user.admin_especial
    except AdministradorEspecial.DoesNotExist:
        return None
    if not admin.activo or not user.is_active or not user.is_staff:
        return None
    return admin


def is_admin_especial(user):
    return get_admin_especial(user) is not None


def has_admin_permission(user, permission):
    if is_dios(user):
        return True

    admin = get_admin_especial(user)
    field = PERMISOS.get(permission)
    return bool(admin and field and getattr(admin, field, False))


def dios_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not is_dios(request.user):
            if not request.user.is_authenticated:
                return redirect("/?view=store")
            return HttpResponseForbidden("Solo Dios puede acceder a este panel.")
        return view_func(request, *args, **kwargs)

    return wrapped
