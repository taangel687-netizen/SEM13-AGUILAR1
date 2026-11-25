from django.db import models


class Tarea(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        COMPLETADO = "completado", "Completado"

    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ACTIVO)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created", "-pk"]
        indexes = [models.Index(fields=["status", "-created"], name="tarea_status_created_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_fin__gte=models.F("fecha_inicio")),
                name="tarea_fechas_validas",
            ),
        ]

    def __str__(self):
        return self.titulo
