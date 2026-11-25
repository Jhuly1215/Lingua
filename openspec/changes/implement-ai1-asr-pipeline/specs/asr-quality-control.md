# Especificación de Capacidad: Control de Calidad y Confianza ASR (SCRUM-24)

- **Capacidad:** `asr-quality-control`
- **Historia de Usuario:** `SCRUM-24`
- **Módulo Backend:** `backend/app/services/asr/quality_control.py`, `backend/app/api/v1/endpoints/transcriptions.py`

---

## Requisito 1: Cálculo Cuantitativo de Confianza

El sistema debe calcular una métrica objetiva de confianza agregada para toda la transcripción basada en las probabilidades posteriores de las palabras alineadas.

### Escenario 1.1: Asignación de confianza global dentro del rango normativo
- **Given** una sesión de transcripción donde se alinearon exitosamente $N$ palabras,
- **When** el evaluador de calidad (`QualityControlEvaluator`) procesa las puntuaciones de las palabras,
- **Then** calcula la media ponderada de confianza de los tokens y palabras en el intervalo continuo $[0.00000, 1.00000]$,
- **And** persiste el valor en la columna `transcriptions.confidence` respetando el CheckConstraint `confidence >= 0 AND confidence <= 1`.

---

## Requisito 2: Clasificación por Umbral Configurable de Calidad

El sistema debe comparar la confianza calculada contra un umbral clínico configurable (`ASR_CONFIDENCE_THRESHOLD`, valor referencial por defecto `0.75`), clasificando automáticamente aquellas transcripciones dudosas.

### Escenario 2.1: Marcado automático de transcripción de baja confianza
- **Given** una transcripción generada cuya confianza global calculada es $0.62$ (inferior al umbral configurado de $0.75$),
- **When** se finaliza la etapa de control de calidad,
- **Then** el sistema asigna el estado `processing_status = 'NEEDS_REVIEW'`,
- **And** establece `human_reviewed = false`,
- **And** registra una observación interna señalando que la calidad acústica o inteligibilidad del habla presenta incertidumbre.

### Escenario 2.2: Transcripción con confianza superior al umbral
- **Given** una transcripción generada cuya confianza global calculada es $0.88$ (superior o igual al umbral de $0.75$),
- **When** se finaliza la etapa de control de calidad,
- **Then** el sistema asigna el estado `processing_status = 'COMPLETED'`,
- **And** mantiene `human_reviewed = false` disponible para auditoría voluntaria.

---

## Requisito 3: Detección de Alucinaciones y Bucles de Repetición

El sistema debe identificar anomalías comunes de los modelos Transformer Whisper en condiciones de ruido o silencio, como la repetición cíclica de una misma palabra o frase (alucinación por bucle).

### Escenario 3.1: Detección de bucle de repetición en habla afásica
- **Given** una transcripción generada por el ASR donde una misma secuencia de n-gramas se repite de forma no natural más de 4 veces consecutivas sin coincidencia acústica en el audio,
- **When** el evaluador de calidad analiza la coherencia del texto y la densidad temporal,
- **Then** marca la transcripción con la bandera de alerta `possible_hallucination = true`,
- **And** fuerza el estado de la transcripción a `processing_status = 'NEEDS_REVIEW'` independientemente del score numérico promedio.

---

## Requisito 4: Consulta de Transcripciones Pendientes de Revisión

El sistema debe proveer filtros específicos en la API para que los profesionales fonoaudiólogos puedan listar y priorizar las transcripciones dudosas.

### Escenario 4.1: Listado de transcripciones con baja confianza
- **Given** una serie de transcripciones almacenadas con diferentes estados de calidad,
- **When** un profesional autenticado envía una petición `GET /api/v1/transcriptions?status=NEEDS_REVIEW&human_reviewed=false`,
- **Then** el sistema responde con código HTTP `200 OK` y una lista de transcripciones que requieren curaduría fonoaudiológica prioritaria, ordenadas por menor confianza (`confidence ASC`).
