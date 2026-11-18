from django.contrib import admin
from django.urls import path

from interop import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("hl7/mensajes", views.recibir_hl7, name="recibir_hl7"),
    path("fhir/Patient", views.fhir_buscar_patient, name="fhir_buscar_patient"),
    path("fhir/Patient/<int:pk>", views.fhir_patient, name="fhir_patient"),
]
