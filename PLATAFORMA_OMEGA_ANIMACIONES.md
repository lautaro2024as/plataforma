# OMEGA — Django Admin gamer/otaku

La personalización vive dentro de `Plataforma_de_juegos/administrador/static/admin/omega/` y se carga desde `templates/admin/base_site.html`.

## Archivos

- `omega_admin.css`: vidrio, neon, hover, lluvia, parallax y responsive.
- `omega_scene.css`: ventana/ciudad cyberpunk.
- `omega_city.svg`: ciudad neon vectorial sin dependencias externas.
- `omega_character.svg`: una sola mujer/mascota visual para conservar siempre la misma identidad.
- `omega_admin.js`: seguimiento del mouse, ojos, respiración, sonrisa y giro al pulsar Juegos.

## Ejecutar en Windows

Desde la carpeta que contiene `manage.py`:

```powershell
python manage.py runserver
```

Abre el admin en `http://127.0.0.1:8000/admin/`.

## Si Django no encuentra los assets

Comprueba que `django.contrib.staticfiles` esté en `INSTALLED_APPS` y que la carpeta exista exactamente en:

```text
administrador/static/admin/omega/
```

No hace falta agregar `STATICFILES_DIRS` cuando los archivos están dentro de la carpeta `static` de una app instalada.

## Cambiar la apariencia de la mujer

Edita solo `omega_character.svg`. Mantener un único SVG evita que la cara y el pelo cambien entre estados. La animación modifica cabeza, pupilas, sonrisa, humo y movimiento suave sin sustituir el personaje.

## Comportamiento

- Mouse: los ojos siguen la posición horizontal/vertical del cursor.
- Hover sobre módulos: el neon acelera y el personaje reacciona.
- Click sobre un enlace cuyo texto/URL contiene `juego`: giro corto → mirada al centro → sonrisa → vuelta al estado normal.
- Lluvia y luces: se generan en el navegador para evitar GIFs pesados.
