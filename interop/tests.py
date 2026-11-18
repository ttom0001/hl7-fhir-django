from django.test import TestCase

from . import hl7
from .models import MensajeHL7, Paciente

# Mensaje de ejemplo 100% ficticio: registro de paciente (ADT^A04), HL7 v2.5.
ADT_A04 = (
    "MSH|^~\\&|HIS|CLINICA|AGENDA|CLINICA|20301115083000||ADT^A04|MSG0001|P|2.5\r"
    "EVN|A04|20301115083000\r"
    "PID|1||30111222^^^RENAPER^DNI||Pérez^Ana||19850412|F|||Av. Maipú 100^^Ushuaia||2901000001\r"
)


class LecturaHL7Test(TestCase):
    def test_lee_tipo_y_control_del_msh(self):
        mensaje = hl7.leer(ADT_A04)
        self.assertEqual(mensaje.tipo, "ADT^A04")
        self.assertEqual(mensaje.control_id, "MSG0001")

    def test_extrae_el_paciente_del_pid(self):
        datos = hl7.datos_paciente(hl7.leer(ADT_A04))
        self.assertEqual(datos["dni"], "30111222")
        self.assertEqual(datos["apellido"], "Pérez")
        self.assertEqual(datos["nombre"], "Ana")
        self.assertEqual(datos["fecha_nacimiento"].isoformat(), "1985-04-12")
        self.assertEqual(datos["genero"], "female")
        self.assertEqual(datos["telefono"], "2901000001")

    def test_acepta_saltos_de_linea_comunes(self):
        self.assertEqual(hl7.leer(ADT_A04.replace("\r", "\n")).control_id, "MSG0001")

    def test_rechaza_texto_sin_msh(self):
        with self.assertRaises(hl7.MensajeInvalido):
            hl7.leer("PID|1||123")

    def test_ack_devuelve_el_control_id_original(self):
        respuesta = hl7.ack(hl7.leer(ADT_A04), "AA")
        self.assertIn("ACK^A04", respuesta)
        self.assertIn("MSA|AA|MSG0001", respuesta)


class EndpointHL7Test(TestCase):
    def enviar(self, texto):
        return self.client.post("/hl7/mensajes", data=texto, content_type="text/plain")

    def test_registra_el_paciente_y_responde_aa(self):
        respuesta = self.enviar(ADT_A04)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("MSA|AA|MSG0001", respuesta.content.decode())
        self.assertEqual(Paciente.objects.get(dni="30111222").apellido, "Pérez")
        self.assertEqual(MensajeHL7.objects.get().estado, MensajeHL7.ACEPTADO)

    def test_un_a08_actualiza_sin_duplicar(self):
        self.enviar(ADT_A04)
        actualizacion = ADT_A04.replace("ADT^A04", "ADT^A08").replace("MSG0001", "MSG0002").replace("2901000001", "2901999999")
        self.enviar(actualizacion)
        self.assertEqual(Paciente.objects.count(), 1)
        self.assertEqual(Paciente.objects.get().telefono, "2901999999")

    def test_mensaje_roto_responde_ae_y_queda_registrado(self):
        respuesta = self.enviar("MSH|^~\\&|HIS|CLINICA|AGENDA|CLINICA|20301115||ADT^A04|MSG0003|P|2.5\rPID|1||")
        self.assertIn("MSA|AE|MSG0003", respuesta.content.decode())
        self.assertEqual(Paciente.objects.count(), 0)
        self.assertEqual(MensajeHL7.objects.get().estado, MensajeHL7.ERROR)

    def test_tipo_no_soportado_responde_ae(self):
        respuesta = self.enviar(ADT_A04.replace("ADT^A04", "ORU^R01"))
        self.assertIn("MSA|AE", respuesta.content.decode())

    def test_solo_acepta_post(self):
        self.assertEqual(self.client.get("/hl7/mensajes").status_code, 405)


class FhirTest(TestCase):
    def setUp(self):
        self.client.post("/hl7/mensajes", data=ADT_A04, content_type="text/plain")
        self.paciente = Paciente.objects.get()

    def test_expone_el_paciente_como_patient_fhir(self):
        respuesta = self.client.get(f"/fhir/Patient/{self.paciente.pk}")
        self.assertEqual(respuesta["Content-Type"], "application/fhir+json")
        recurso = respuesta.json()
        self.assertEqual(recurso["resourceType"], "Patient")
        self.assertEqual(recurso["identifier"][0], {"use": "official", "system": "http://www.renaper.gob.ar/dni", "value": "30111222"})
        self.assertEqual(recurso["name"][0]["family"], "Pérez")
        self.assertEqual(recurso["gender"], "female")
        self.assertEqual(recurso["birthDate"], "1985-04-12")

    def test_busca_por_identificador(self):
        bundle = self.client.get("/fhir/Patient", {"identifier": "http://www.renaper.gob.ar/dni|30111222"}).json()
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["total"], 1)
        vacio = self.client.get("/fhir/Patient", {"identifier": "99999999"}).json()
        self.assertEqual(vacio["total"], 0)

    def test_paciente_inexistente_da_404(self):
        self.assertEqual(self.client.get("/fhir/Patient/9999").status_code, 404)
