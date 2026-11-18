from django.db import models


class Paciente(models.Model):
    GENEROS = [("male", "Masculino"), ("female", "Femenino"), ("other", "Otro"), ("unknown", "Desconocido")]

    dni = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=10, choices=GENEROS, default="unknown")
    telefono = models.CharField(max_length=30, null=True, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} (DNI {self.dni})"


class MensajeHL7(models.Model):
    """Bitácora de todo lo que llega: si algo falla, queda el mensaje original para revisarlo."""

    ACEPTADO, ERROR = "AA", "AE"

    recibido = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20, blank=True)
    control_id = models.CharField(max_length=50, blank=True)
    estado = models.CharField(max_length=2, choices=[(ACEPTADO, "Aceptado"), (ERROR, "Error")])
    detalle = models.CharField(max_length=200, blank=True)
    texto = models.TextField()
    paciente = models.ForeignKey(Paciente, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-recibido"]
        verbose_name = "mensaje HL7"
        verbose_name_plural = "mensajes HL7"

    def __str__(self):
        return f"{self.tipo or 'desconocido'} {self.control_id} · {self.get_estado_display()}"
