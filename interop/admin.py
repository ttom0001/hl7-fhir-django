from django.contrib import admin

from .models import MensajeHL7, Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "dni", "fecha_nacimiento", "genero", "actualizado")
    search_fields = ("apellido", "nombre", "dni")


@admin.register(MensajeHL7)
class MensajeHL7Admin(admin.ModelAdmin):
    list_display = ("recibido", "tipo", "control_id", "estado", "paciente", "detalle")
    list_filter = ("estado", "tipo")
    readonly_fields = [f.name for f in MensajeHL7._meta.fields]
