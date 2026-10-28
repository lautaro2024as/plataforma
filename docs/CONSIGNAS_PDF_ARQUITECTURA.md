# Cambios de arquitectura para cumplir la consigna

## Decisiones
- Se conserva el dominio NEXUS (juegos digitales); se incorporan los patrones de e-commerce exigidos por el PDF.
- `PerfilUsuario` agrega teléfono, dirección y ciudad y se edita con un `ModelForm`.
- `CarritoItem` se persiste en la base de datos y pertenece a un perfil.
- `Pedido` guarda cabecera, fecha, estado y total; `DetallePedido` conserva cantidad, edición y precio unitario histórico.
- `Juego.stock` se valida y descuenta en checkout.
- El checkout usa `transaction.atomic()` y `select_for_update()` para impedir pedidos parciales y reducir carreras de inventario.
- Las vistas de perfil, carrito y pedidos requieren sesión; las consultas de pedido filtran por el perfil autenticado.
- Las claves digitales siguen registrándose como `LicenciaCompra` y quedan vinculadas al pedido.
- Los tests cubren registro/login, perfil, propiedad del carrito/pedido, compra, precio histórico y rollback por falta de stock.

## Migraciones
Aplicar las migraciones en orden desde `Plataforma_de_juegos/`:
```bash
python manage.py migrate
```

## Pruebas
Para ejecutar sin un servidor MySQL configurado, activar SQLite temporalmente:
```powershell
$env:DJANGO_USE_SQLITE='1'
python manage.py test
```

En producción, configurar `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false` y las variables `DB_*`. Las credenciales que estuvieron en el historial público deben rotarse fuera de GitHub.
