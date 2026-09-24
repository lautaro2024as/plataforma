from getpass import getpass

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from dios.models import DiosCuenta


class Command(BaseCommand):
    help = "Crea o actualiza la cuenta maestra de Dios."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Correo de acceso de Dios.")
        parser.add_argument("--username", default="lautaro2024as", help="Usuario de la cuenta.")
        parser.add_argument(
            "--password",
            default=None,
            help="Contraseña. Se recomienda omitirla para introducirla de forma privada.",
        )

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        username = options["username"].strip()
        password = options["password"] or getpass("Contraseña para Dios: ")

        if not email or not username or not password:
            raise CommandError("Correo, usuario y contraseña son obligatorios.")

        email_owner = User.objects.filter(email__iexact=email).first()
        username_owner = User.objects.filter(username=username).first()
        user = email_owner or username_owner

        if user is None:
            user = User(username=username, email=email)
        else:
            user.email = email
            if not user.username:
                user.username = username

        existing = DiosCuenta.objects.filter(activo=True).exclude(usuario=user).first()
        if existing:
            raise CommandError(
                f"Ya existe otra cuenta Dios activa: {existing.usuario.email}. "
                "Desactívala antes de asignar Dios a esta cuenta."
            )

        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        DiosCuenta.objects.update_or_create(
            usuario=user,
            defaults={"activo": True},
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Cuenta Dios configurada: {user.email} (usuario: {user.username})."
            )
        )
