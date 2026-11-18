#!/usr/bin/env bash
# Simula un sistema de admisión que manda un ADT^A04 (registro de paciente) por HTTP,
# muestra el ACK que responde el servidor y después pide el mismo paciente en FHIR.
# Uso: ./scripts/enviar_hl7.sh   (con `python manage.py runserver` corriendo)
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
DNI="${1:-30111222}"
AHORA="$(date +%Y%m%d%H%M%S)"

MENSAJE="MSH|^~\\&|HIS|CLINICA|AGENDA|CLINICA|${AHORA}||ADT^A04|MSG${AHORA}|P|2.5\r"
MENSAJE+="EVN|A04|${AHORA}\r"
MENSAJE+="PID|1||${DNI}^^^RENAPER^DNI||Pérez^Ana||19850412|F|||Av. Maipú 100^^Ushuaia||2901000001\r"

echo "▶ Enviando ADT^A04 del DNI ${DNI}"
ACK="$(printf "%b" "$MENSAJE" | curl -s -X POST "$BASE_URL/hl7/mensajes" -H 'Content-Type: text/plain' --data-binary @-)"
printf '%s\n' "$ACK" | tr '\r' '\n'

grep -q "MSA|AA" <<<"$ACK" || { echo "El servidor no aceptó el mensaje" >&2; exit 1; }

echo "▶ El mismo paciente en HL7 FHIR R4"
curl -s "$BASE_URL/fhir/Patient?identifier=${DNI}"
echo
