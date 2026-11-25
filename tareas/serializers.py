from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import Tarea


class PeriodoSerializer(serializers.Serializer):
    inicio = serializers.DateField(source="fecha_inicio")
    fin = serializers.DateField(source="fecha_fin")

    def validate(self, attrs):
        tarea = self.parent.instance
        inicio = attrs.get("fecha_inicio", getattr(tarea, "fecha_inicio", None))
        fin = attrs.get("fecha_fin", getattr(tarea, "fecha_fin", None))
        if inicio is not None and fin is not None and fin < inicio:
            raise serializers.ValidationError({"fin": "Debe ser igual o posterior al inicio."})
        return attrs


class TareaSerializer(serializers.HyperlinkedModelSerializer):
    periodo = PeriodoSerializer(source="*")
    id = serializers.ReadOnlyField()
    completar_url = serializers.SerializerMethodField()

    class Meta:
        model = Tarea
        fields = ("id", "url", "titulo", "descripcion", "status", "periodo", "created", "completar_url")
        read_only_fields = ("created",)

    def get_completar_url(self, obj) -> str:
        return reverse("tarea-completar", args=[obj.pk], request=self.context.get("request"))
