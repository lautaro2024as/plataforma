from .authz import get_admin_especial, is_admin_especial, is_dios


def account_roles(request):
    admin = get_admin_especial(request.user)
    return {
        "is_dios": is_dios(request.user),
        "is_admin_especial": is_admin_especial(request.user),
        "admin_permissions": admin,
    }
