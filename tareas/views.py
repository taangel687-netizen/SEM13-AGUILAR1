from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Tarea
from .serializers import TareaSerializer


class TareaViewSet(ModelViewSet):
    """Consulta y administra tareas."""

    queryset = Tarea.objects.all()
    serializer_class = TareaSerializer
    filterset_fields = ["status"]
    search_fields = ["titulo", "descripcion"]
    ordering_fields = ["created", "titulo", "fecha_fin"]
    ordering = ["-created", "-pk"]

    @extend_schema(request=None, responses=TareaSerializer)
    @action(detail=True, methods=["post"])
    def completar(self, request, pk=None):
        """Marca la tarea como completada."""
        tarea = self.get_object()
        if tarea.status != Tarea.Estado.COMPLETADO:
            tarea.status = Tarea.Estado.COMPLETADO
            tarea.save(update_fields=["status"])
        return Response(self.get_serializer(tarea).data)
