from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import fhir, hl7
from .models import MensajeHL7, Paciente

FHIR_JSON = "application/fhir+json"


@csrf_exempt  # lo llaman otros sistemas, no un formulario del navegador
@require_POST
def recibir_hl7(request):
    """Recibe un mensaje HL7 v2 en texto plano y responde con un ACK."""
    texto = request.body.decode("utf-8", errors="replace")
    mensaje = None
    try:
        mensaje = hl7.leer(texto)
        if not hl7.es_alta_o_actualizacion(mensaje):
            raise hl7.MensajeInvalido(f"Tipo de mensaje no soportado: {mensaje.tipo}")
        datos = hl7.datos_paciente(mensaje)
        with transaction.atomic():
            paciente, _ = Paciente.objects.update_or_create(dni=datos.pop("dni"), defaults=datos)
            MensajeHL7.objects.create(texto=texto, tipo=mensaje.tipo, control_id=mensaje.control_id,
                                      estado=MensajeHL7.ACEPTADO, paciente=paciente)
        respuesta = hl7.ack(mensaje, "AA")
    except (hl7.MensajeInvalido, ValueError) as error:
        MensajeHL7.objects.create(texto=texto, estado=MensajeHL7.ERROR, detalle=str(error)[:200],
                                  tipo=mensaje.tipo if mensaje else "",
                                  control_id=mensaje.control_id if mensaje else "")
        respuesta = hl7.ack(mensaje, "AE", str(error))
    return HttpResponse(respuesta, content_type="application/hl7-v2; charset=utf-8")


@require_GET
def fhir_patient(request, pk):
    return JsonResponse(fhir.patient(get_object_or_404(Paciente, pk=pk)), content_type=FHIR_JSON)


@require_GET
def fhir_buscar_patient(request):
    """GET /fhir/Patient?identifier=<dni> o sin filtro para listar todos."""
    pacientes = Paciente.objects.all()
    identificador = request.GET.get("identifier")
    if identificador:
        pacientes = pacientes.filter(dni=identificador.split("|")[-1])
    return JsonResponse(fhir.bundle(pacientes), content_type=FHIR_JSON)
