# Especificación de Capacidad: Exportación Estructurada de Transcripciones (Etapa 10)

- **Capacidad:** `transcription-export`
- **Módulo Backend:** `backend/app/services/asr/export_service.py`, `backend/app/api/v1/endpoints/transcriptions.py`

---

## Requisito 1: Exportación en Formato JSON Enriquecido

El sistema debe proveer una exportación estructurada en formato JSON estándar que incluya metadatos de la sesión, cabecera de transcripción, y el arreglo detallado de palabras alineadas con sus marcas temporales y puntuaciones de confianza.

### Escenario 1.1: Descarga de JSON estructurado
- **Given** una transcripción completada con palabras alineadas persistidas,
- **When** un usuario autorizado envía una petición `GET /api/v1/transcriptions/{transcription_id}/export?format=json`,
- **Then** el sistema responde con HTTP `200 OK`, `Content-Type: application/json` y un documento JSON que contiene:
  - Identificadores de evaluación, audio y transcripción.
  - Modelo ASR y versión utilizada.
  - Texto crudo (`raw_text`) y texto corregido (`corrected_text`, si existe).
  - Colección ordenada de segmentos y palabras con `start`, `end`, `word` y `confidence`.

---

## Requisito 2: Exportación a Formato Subtítulos SRT

El sistema debe generar archivos de subtítulos estándar `.srt` a partir de los segmentos temporales para permitir la reproducción de audio sincronizada con texto en reproductores externos o herramientas de análisis.

### Escenario 2.1: Generación de archivo SRT válido
- **Given** una transcripción procesada con segmentos de habla,
- **When** el usuario solicita `GET /api/v1/transcriptions/{transcription_id}/export?format=srt`,
- **Then** el sistema genera dinámicamente un archivo con sintaxis SRT estricta:
  ```text
  1
  00:00:01,200 --> 00:00:03,800
  foca fuente flor
  ```
- **And** responde con `Content-Type: text/plain; charset=utf-8` y encabezado `Content-Disposition: attachment; filename="transcription_{id}.srt"`.

---

## Requisito 3: Exportación a Formato Praat TextGrid

El sistema debe soportar la exportación al formato estándar de fonética acústica y fonoaudiología clínica **Praat TextGrid**, permitiendo a investigadores abrir las alineaciones temporales directamente en el software Praat.

### Escenario 3.1: Generación de TextGrid con tiers de palabras e intervalos
- **Given** una transcripción alineada con palabras e intervalos de silencio/habla,
- **When** el usuario solicita `GET /api/v1/transcriptions/{transcription_id}/export?format=textgrid`,
- **Then** el sistema genera un archivo de texto plano compatible con la especificación `ooTextFile` de Praat,
- **And** estructura al menos dos niveles de intervalos (*IntervalTier*):
  - Nivel 1: Segmentos de habla activa (*speech chunks* detectados por VAD).
  - Nivel 2: Palabras individuales alineadas temporalmente (*words* con sus límites exactos `xmin` y `xmax`),
- **And** responde con `Content-Type: text/plain; charset=utf-8` y cabecera de descarga de archivo `.TextGrid`.

---

## Requisito 4: Eficiencia y Generación a partir de Datos Persistidos

La exportación no debe re-ejecutar el pipeline ASR ni volver a decodificar el audio original.

### Escenario 4.1: Exportación puramente basada en base de datos
- **Given** una transcripción ya procesada y persistida en `transcriptions`, `annotations` y `ai_analysis`,
- **When** se solicita la exportación en cualquiera de los formatos soportados (`json`, `srt`, `textgrid`),
- **Then** el sistema consulta los datos ya almacenados en base de datos,
- **And** ensambla el archivo en memoria en menos de 200 ms sin invocar FFmpeg, WhisperX ni modelos de Machine Learning.
