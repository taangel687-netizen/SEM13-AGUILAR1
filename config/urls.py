from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import include, path
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from tareas.views import TareaViewSet

router = DefaultRouter()
router.register("tareas", TareaViewSet)


@require_GET
@never_cache
def csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


urlpatterns = [
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/csrf/", csrf_token, name="csrf-token"),
    path("api/auth/", include("rest_framework.urls")),
]
