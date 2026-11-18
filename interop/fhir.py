"""Traducción del paciente a recurso HL7 FHIR R4."""

SISTEMA_DNI = "http://www.renaper.gob.ar/dni"


def patient(p) -> dict:
    recurso = {
        "resourceType": "Patient",
        "id": str(p.pk),
        "meta": {"lastUpdated": p.actualizado.isoformat(timespec="seconds")},
        "identifier": [{"use": "official", "system": SISTEMA_DNI, "value": p.dni}],
        "name": [{"use": "official", "family": p.apellido, "given": [p.nombre]}],
        "gender": p.genero,
    }
    if p.fecha_nacimiento:
        recurso["birthDate"] = p.fecha_nacimiento.isoformat()
    if p.telefono:
        recurso["telecom"] = [{"system": "phone", "value": p.telefono}]
    return recurso


def bundle(pacientes) -> dict:
    recursos = [patient(p) for p in pacientes]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(recursos),
        "entry": [{"fullUrl": f"Patient/{r['id']}", "resource": r} for r in recursos],
    }
