from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from dios.models import DiosCuenta


class Command(BaseCommand):
    help = "Convierte una cuenta existente en la cuenta maestra de Dios."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        username = options["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"No existe el usuario '{username}'.")

        existing = DiosCuenta.objects.filter(activo=True).exclude(usuario=user).first()
        if existing:
            raise CommandError(
                f"Ya existe una cuenta Dios activa: {existing.usuario.username}."
            )

        user.is_staff = True
        user.is_superuser = True
        user.save(update_fields=["is_staff", "is_superuser"])

        cuenta, created = DiosCuenta.objects.get_or_create(usuario=user)
        if not cuenta.activo:
            cuenta.activo = True
            cuenta.save(update_fields=["activo"])

        self.stdout.write(
            self.style.SUCCESS(
                f"{user.username} es ahora la cuenta Dios de NEXUS."
            )
        )
