import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Paciente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("dni", models.CharField(max_length=20, unique=True)),
                ("nombre", models.CharField(max_length=80)),
                ("apellido", models.CharField(max_length=80)),
                ("fecha_nacimiento", models.DateField(blank=True, null=True)),
                ("genero", models.CharField(choices=[("male", "Masculino"), ("female", "Femenino"), ("other", "Otro"), ("unknown", "Desconocido")], default="unknown", max_length=10)),
                ("telefono", models.CharField(blank=True, max_length=30, null=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["apellido", "nombre"]},
        ),
        migrations.CreateModel(
            name="MensajeHL7",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recibido", models.DateTimeField(auto_now_add=True)),
                ("tipo", models.CharField(blank=True, max_length=20)),
                ("control_id", models.CharField(blank=True, max_length=50)),
                ("estado", models.CharField(choices=[("AA", "Aceptado"), ("AE", "Error")], max_length=2)),
                ("detalle", models.CharField(blank=True, max_length=200)),
                ("texto", models.TextField()),
                ("paciente", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="interop.paciente")),
            ],
            options={"verbose_name": "mensaje HL7", "verbose_name_plural": "mensajes HL7", "ordering": ["-recibido"]},
        ),
    ]
