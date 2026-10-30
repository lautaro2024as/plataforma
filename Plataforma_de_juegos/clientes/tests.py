from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from administrador.models import DetallePedido, Juego, LicenciaCompra, Pedido, PerfilUsuario
from .models import CarritoItem


class ClienteWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dev_user = User.objects.create_user(
            username="studio", email="studio@example.test", password="StrongTestPass!782"
        )
        cls.dev_profile = PerfilUsuario.objects.create(usuario=cls.dev_user, rol="desarrollador")
        cls.player_user = User.objects.create_user(
            username="player", email="player@example.test", password="StrongTestPass!782"
        )
        cls.player_profile = PerfilUsuario.objects.create(
            usuario=cls.player_user, rol="jugador", telefono="111222333",
            direccion="Calle 123", ciudad="Morón",
        )
        cls.game = Juego.objects.create(
            titulo="Juego de prueba", precio=Decimal("10.00"), stock=5,
            estado="publicado", desarrollador=cls.dev_profile,
        )

    def test_registration_creates_user_and_profile(self):
        response = self.client.post(reverse("clientes:registro_usuario"), {
            "name": "New Gamer", "email": "new-gamer@example.test",
            "password": "LongEnoughStrongPass!927", "fecha_nacimiento": "2000-01-01",
        })
        self.assertRedirects(response, reverse("administrador:catalogo"))
        user = User.objects.get(email="new-gamer@example.test")
        self.assertEqual(user.perfilusuario.rol, "jugador")
        self.assertEqual(user.perfilusuario.fecha_nacimiento.isoformat(), "2000-01-01")
        self.assertTrue(user.check_password("LongEnoughStrongPass!927"))

    def test_login_success_and_failure(self):
        response = self.client.post(reverse("clientes:login"), {
            "email": "player@example.test", "password": "StrongTestPass!782"
        })
        self.assertRedirects(response, reverse("administrador:catalogo"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.client.logout()
        response = self.client.post(reverse("clientes:login"), {
            "email": "player@example.test", "password": "wrong"
        })
        self.assertRedirects(response, "/usuarios/autenticacion/?tab=login")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_profile_form_persists_current_users_profile(self):
        self.client.force_login(self.player_user)
        response = self.client.post(reverse("clientes:perfil"), {
            "telefono": "999888777", "direccion": "Av. Nueva 55",
            "ciudad": "Ituzaingó", "fecha_nacimiento": "",
        })
        self.assertRedirects(response, reverse("clientes:perfil"))
        self.player_profile.refresh_from_db()
        self.assertEqual(self.player_profile.telefono, "999888777")
        self.assertEqual(self.player_profile.direccion, "Av. Nueva 55")
        self.assertEqual(self.player_profile.ciudad, "Ituzaingó")

    def test_profile_form_rejects_invalid_phone(self):
        self.client.force_login(self.player_user)
        response = self.client.post(reverse("clientes:perfil"), {
            "telefono": "teléfono-no-válido", "direccion": "Calle 1",
            "ciudad": "Morón", "fecha_nacimiento": "",
        })
        self.assertEqual(response.status_code, 200)
        self.player_profile.refresh_from_db()
        self.assertEqual(self.player_profile.telefono, "111222333")

    def test_cart_requires_login_and_removal_checks_ownership(self):
        response = self.client.get(reverse("clientes:carrito"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.player_user)
        other_profile = PerfilUsuario.objects.create(
            usuario=User.objects.create_user(username="other", password="StrongTestPass!782")
        )
        other_item = CarritoItem.objects.create(perfil=other_profile, juego=self.game)
        response = self.client.post(reverse("clientes:carrito_eliminar", args=[other_item.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(CarritoItem.objects.filter(pk=other_item.pk).exists())

    def test_checkout_creates_order_detail_and_license_and_decrements_stock(self):
        self.client.force_login(self.player_user)
        CarritoItem.objects.create(perfil=self.player_profile, juego=self.game, cantidad=2, edicion="Deluxe")
        response = self.client.post(reverse("clientes:checkout"))
        order = Pedido.objects.get(usuario=self.player_profile)
        detail = DetallePedido.objects.get(pedido=order)
        self.game.refresh_from_db()
        self.assertRedirects(response, reverse("clientes:pedido_detalle", args=[order.pk]))
        self.assertEqual(order.estado, "completado")
        self.assertEqual(order.total, Decimal("44.00"))
        self.assertEqual(detail.precio_unitario, Decimal("22.00"))
        self.assertEqual(detail.cantidad, 2)
        self.assertEqual(self.game.stock, 3)
        self.assertEqual(LicenciaCompra.objects.filter(pedido=order).count(), 2)
        self.assertFalse(CarritoItem.objects.filter(perfil=self.player_profile).exists())

    def test_price_snapshot_survives_catalog_price_change(self):
        self.client.force_login(self.player_user)
        CarritoItem.objects.create(perfil=self.player_profile, juego=self.game, cantidad=1)
        self.client.post(reverse("clientes:checkout"))
        detail = DetallePedido.objects.get(pedido__usuario=self.player_profile)
        self.game.precio = Decimal("99.00")
        self.game.save(update_fields=["precio"])
        detail.refresh_from_db()
        self.assertEqual(detail.precio_unitario, Decimal("10.00"))
        self.assertEqual(detail.pedido.total, Decimal("10.00"))

    def test_insufficient_stock_rolls_back_entire_checkout(self):
        self.client.force_login(self.player_user)
        second = Juego.objects.create(
            titulo="Juego sin stock", precio=Decimal("3.00"), stock=0,
            estado="publicado", desarrollador=self.dev_profile,
        )
        CarritoItem.objects.create(perfil=self.player_profile, juego=self.game, cantidad=1)
        CarritoItem.objects.create(perfil=self.player_profile, juego=second, cantidad=1)
        response = self.client.post(reverse("clientes:checkout"))
        self.assertRedirects(response, reverse("clientes:carrito"))
        self.assertFalse(Pedido.objects.filter(usuario=self.player_profile).exists())
        self.assertFalse(LicenciaCompra.objects.filter(jugador=self.player_profile, origen="compra").exists())
        self.assertEqual(CarritoItem.objects.filter(perfil=self.player_profile).count(), 2)
        self.game.refresh_from_db()
        self.assertEqual(self.game.stock, 5)

    def test_user_cannot_view_another_users_order(self):
        self.client.force_login(self.player_user)
        other_profile = PerfilUsuario.objects.create(
            usuario=User.objects.create_user(username="other-order", password="StrongTestPass!782")
        )
        order = Pedido.objects.create(usuario=other_profile, total=Decimal("5.00"))
        response = self.client.get(reverse("clientes:pedido_detalle", args=[order.pk]))
        self.assertEqual(response.status_code, 404)
