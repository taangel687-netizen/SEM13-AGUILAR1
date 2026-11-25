from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from .models import Tarea


class TareaAPITests(APITestCase):
    url = "/api/tareas/"
    payload = {
        "titulo": "Preparar entrega",
        "periodo": {"inicio": "2026-11-25", "fin": "2026-11-27"},
    }

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.user = get_user_model().objects.create_user("estudiante")
        self.token = Token.objects.create(user=self.user)

    def test_validacion_anidada(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        invalido = dict(self.payload, periodo={"inicio": "2026-11-25", "fin": "2026-11-24"})
        response = self.client.post(self.url, invalido, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("fin", response.data["periodo"])
        detail = self.client.post(self.url, self.payload, format="json").data["url"]
        response = self.client.patch(detail, {"periodo": {"fin": "2026-11-24"}}, format="json")
        self.assertEqual(response.status_code, 400)
        response = self.client.patch(detail, {"periodo": {"fin": "2026-11-28"}}, format="json")
        self.assertEqual(response.data["periodo"]["fin"], "2026-11-28")

    def test_crud_y_enlaces(self):
        self.assertEqual(self.client.get("/api/").data["tareas"], "http://testserver/api/tareas/")
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        detail, completar = response.data["url"], response.data["completar_url"]
        self.assertEqual(self.client.get(detail).status_code, 200)
        payload = dict(self.payload, titulo="Entrega revisada")
        response = self.client.put(detail, payload, format="json")
        self.assertEqual(response.data["titulo"], "Entrega revisada")
        self.assertEqual(self.client.post(completar).data["status"], "completado")
        self.assertEqual(self.client.post(completar).data["status"], "completado")
        self.assertEqual(self.client.delete(detail).status_code, 204)
        self.assertEqual(self.client.get(detail).status_code, 404)

    def test_filtros_busqueda_y_paginacion(self):
        for index in range(7):
            Tarea.objects.create(titulo=f"Laboratorio {index}", fecha_inicio="2026-11-25",
                                 fecha_fin="2026-11-27")
        Tarea.objects.create(titulo="Laboratorio excluido", status="completado",
                             fecha_inicio="2026-11-25", fecha_fin="2026-11-27")
        response = self.client.get(self.url, {
            "status": "activo", "page": 2, "ordering": "-created", "search": "Laboratorio",
        })
        self.assertEqual(response.data["count"], 7)
        self.assertIsNone(response.data["next"])
        self.assertIn("status=activo", response.data["previous"])
        self.assertEqual([item["titulo"] for item in response.data["results"]],
                         ["Laboratorio 1", "Laboratorio 0"])

    def test_limite_de_tasa(self):
        from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

        for throttle, client, limit in (
            (AnonRateThrottle, self.client, 2),
            (UserRateThrottle, APIClient(), 3),
        ):
            if throttle is UserRateThrottle:
                client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
            with patch.object(throttle, "THROTTLE_RATES", {"anon": "2/min", "user": "3/min"}):
                for _ in range(limit):
                    self.assertEqual(client.get(self.url).status_code, 200)
                response = client.get(self.url)
                self.assertEqual(response.status_code, 429)
                self.assertIn("Retry-After", response)

    def test_cors_csrf_y_documentacion(self):
        origin = "http://localhost:5173"
        preflight = self.client.options(
            self.url, HTTP_ORIGIN=origin, HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,x-csrftoken",
        )
        self.assertEqual(preflight["Access-Control-Allow-Origin"], origin)
        self.assertEqual(preflight["Access-Control-Allow-Credentials"], "true")
        response = self.client.options(
            self.url, HTTP_ORIGIN="https://otro.example", HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )
        self.assertNotIn("Access-Control-Allow-Origin", response)

        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.get("/api/csrf/", HTTP_ORIGIN=origin)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(client.post(self.url, self.payload, format="json", HTTP_ORIGIN=origin)
                         .status_code, 403)
        response = client.post(self.url, self.payload, format="json", HTTP_ORIGIN=origin,
                               HTTP_X_CSRFTOKEN=response.json()["csrfToken"])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)
        schema = self.client.get("/api/schema/", HTTP_ACCEPT="application/vnd.oai.openapi+json")
        self.assertIn("/api/tareas/{id}/completar/", schema.json()["paths"])
