"""Lectura de mensajes HL7 v2 y armado de ACK, escrito a mano para entender el formato.

Un mensaje HL7 v2 son segmentos (líneas) separados por retorno de carro. Cada segmento
son campos separados por '|' y cada campo puede tener componentes separados por '^'.
"""
from dataclasses import dataclass
from datetime import datetime


class MensajeInvalido(ValueError):
    """El texto recibido no es un mensaje HL7 v2 que podamos procesar."""


@dataclass
class Mensaje:
    segmentos: dict  # nombre de segmento -> lista de campos del primero que aparece

    def campo(self, segmento: str, numero: int) -> str:
        """Devuelve SEG-n. En MSH el campo 1 es el propio separador, por eso se corre uno."""
        campos = self.segmentos.get(segmento)
        if campos is None:
            raise MensajeInvalido(f"Falta el segmento {segmento}")
        indice = numero - 1 if segmento == "MSH" else numero
        return campos[indice] if indice < len(campos) else ""

    @property
    def tipo(self) -> str:
        return self.campo("MSH", 9)  # ej. ADT^A04

    @property
    def control_id(self) -> str:
        return self.campo("MSH", 10)


def leer(texto: str) -> Mensaje:
    lineas = [l for l in texto.replace("\r\n", "\r").replace("\n", "\r").split("\r") if l.strip()]
    if not lineas or not lineas[0].startswith("MSH|"):
        raise MensajeInvalido("El mensaje tiene que empezar con el segmento MSH")
    segmentos = {}
    for linea in lineas:
        campos = linea.split("|")
        segmentos.setdefault(campos[0], campos)
    return Mensaje(segmentos)


def componente(valor: str, numero: int) -> str:
    partes = valor.split("^")
    return partes[numero - 1] if numero <= len(partes) else ""


def leer_fecha(valor: str):
    """HL7 usa AAAAMMDD; devuelve None si viene vacía."""
    return datetime.strptime(valor[:8], "%Y%m%d").date() if valor else None


SEXO_A_FHIR = {"M": "male", "F": "female", "O": "other", "U": "unknown", "A": "other"}


def datos_paciente(mensaje: Mensaje) -> dict:
    """Extrae el paciente del segmento PID (HL7 v2.5)."""
    identificador = mensaje.campo("PID", 3)
    dni = componente(identificador, 1)
    if not dni:
        raise MensajeInvalido("PID-3 no trae identificador del paciente")
    nombre = mensaje.campo("PID", 5)
    return {
        "dni": dni,
        "apellido": componente(nombre, 1),
        "nombre": componente(nombre, 2),
        "fecha_nacimiento": leer_fecha(mensaje.campo("PID", 7)),
        "genero": SEXO_A_FHIR.get(mensaje.campo("PID", 8).upper(), "unknown"),
        "telefono": mensaje.campo("PID", 13) or None,
    }


def ack(mensaje: Mensaje | None, codigo: str, texto_error: str = "") -> str:
    """Arma el ACK de respuesta: AA = aceptado, AE = error, AR = rechazado."""
    ahora = datetime.now().strftime("%Y%m%d%H%M%S")
    if mensaje is not None:
        destino_app, destino_inst = mensaje.campo("MSH", 3), mensaje.campo("MSH", 4)
        evento = componente(mensaje.tipo, 2)
        control = mensaje.control_id
    else:
        destino_app = destino_inst = evento = control = ""
    msh = f"MSH|^~\\&|AGENDA|CLINICA|{destino_app}|{destino_inst}|{ahora}||ACK^{evento}|ACK{ahora}|P|2.5"
    msa = f"MSA|{codigo}|{control}" + (f"|{texto_error}" if texto_error else "")
    return f"{msh}\r{msa}\r"


def es_alta_o_actualizacion(mensaje: Mensaje) -> bool:
    """ADT^A01 (internación), A04 (registro) y A08 (actualización) traen datos del paciente."""
    return componente(mensaje.tipo, 1) == "ADT" and componente(mensaje.tipo, 2) in {"A01", "A04", "A08"}
