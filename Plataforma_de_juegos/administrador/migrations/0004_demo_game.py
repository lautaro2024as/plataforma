from django.db import migrations


def crear_datos_demo(apps, schema_editor):
    User = apps.get_model("auth", "User")
    PerfilUsuario = apps.get_model("administrador", "PerfilUsuario")
    Juego = apps.get_model("administrador", "Juego")

    user, created = User.objects.get_or_create(
        username="nexus_demo_dev",
        defaults={"email": "demo@nexus.local"},
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])

    profile, _ = PerfilUsuario.objects.get_or_create(
        usuario_id=user.id,
        defaults={
            "rol": "desarrollador",
            "nombre_estudio": "NEXUS Demo Studio",
            "tax_id": "DEMO-001",
        },
    )

    Juego.objects.get_or_create(
        titulo="NEXUS Demo Game",
        desarrollador_id=profile.id,
        defaults={
            "categoria": "Indie",
            "precio": 9.99,
            "precio_original": 14.99,
            "imagen_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=1200&q=80",
            "descripcion": "Juego de prueba para comprobar carrito, eliminación y compra simulada.",
            "calificacion": 4.5,
            "tipo_clave": "Demo Key Global",
            "estado": "publicado",
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("administrador", "0003_roles_and_license_owner"),
    ]

    operations = [
        migrations.RunPython(crear_datos_demo, migrations.RunPython.noop),
    ]