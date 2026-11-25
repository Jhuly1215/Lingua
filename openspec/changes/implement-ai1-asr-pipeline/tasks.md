# Plan de Tareas Técnicas: Pipeline ASR (AI1) en LINGUA

- **Identificador del Cambio:** `implement-ai1-asr-pipeline`
- **Subsistema:** `AI1 — Automatic Speech Recognition Pipeline`
- **Fecha:** 24 de noviembre de 2026
- **Estado:** Desglose Técnico Aprobado para Ejecución Incremental

---

## FASE 1: SCRUM-25 — Ingesta y Gestión de Grabaciones de Audio

### Tarea 1.1: Esquemas Pydantic y Configuración de Almacenamiento
- **ID:** `TASK-AI1-1.1`
- **Descripción:** Definir esquemas de entrada y salida para archivos de audio y agregar variables de configuración de almacenamiento en `Settings`.
- **Archivos a crear:**
  - `backend/app/schemas/audio.py`
- **Archivos a modificar:**
  - `backend/app/core/config.py` (variables `STORAGE_DRIVER`, `AUDIO_STORAGE_PATH`, `MAX_AUDIO_SIZE_MB`).
  - `backend/app/schemas/__init__.py`
- **Dependencias:** Ninguna.
- **Resultado esperado:** Esquemas `AudioUploadResponse`, `AudioDetailResponse` con validación estricta de tipos.
- **Pruebas necesarias:** Pruebas unitarias de serialización de esquemas en `tests/unit/test_audio_schemas.py`.
- **Criterio de terminación:** Esquemas validados por Pydantic y configuración leída correctamente desde `.env`.

---

### Tarea 1.2: Repositorio de Audio (`AudioRepository`)
- **ID:** `TASK-AI1-1.2`
- **Descripción:** Implementar el repositorio de acceso a datos para la entidad `Audio` heredando de `BaseRepository[Audio]`.
- **Archivos a crear:**
  - `backend/app/repositories/audio_repository.py`
- **Archivos a modificar:**
  - `backend/app/repositories/__init__.py`
- **Dependencias:** `TASK-AI1-1.1`.
- **Resultado esperado:** Métodos `list_by_evaluation_id`, `get_by_id_active` implementados con SQLAlchemy 2.x asíncrono.
- **Pruebas necesarias:** Pruebas de consulta y filtrado relacional en base de datos SQLite de prueba.
- **Criterio de terminación:** CRUD asíncrono sobre `public.audio` funcional con filtro `active = True`.

---

### Tarea 1.3: Servicio de Almacenamiento (`StorageService`)
- **ID:** `TASK-AI1-1.3`
- **Descripción:** Implementar la interfaz abstracta `StorageService` y el driver local `LocalStorageService` con soporte para rutas seguras.
- **Archivos a crear:**
  - `backend/app/services/storage_service.py`
- **Dependencias:** `TASK-AI1-1.1`.
- **Resultado esperado:** Métodos `save_file`, `get_file_stream`, `delete_file` y `generate_access_url` operativos sobre disco local protegido.
- **Pruebas necesarias:** Pruebas unitarias de escritura, lectura y eliminación de archivos binarios temporales.
- **Criterio de terminación:** Almacenamiento de archivos binarios con rutas normalizadas y prevención de path traversal.

---

### Tarea 1.4: Servicio de Negocio de Audio (`AudioService`)
- **ID:** `TASK-AI1-1.4`
- **Descripción:** Implementar la lógica de negocio para validar MIME, tamaño, extraer metadatos de cabecera de audio (duración, sample rate, canales), verificar consentimiento mediante `ConsentService` y persistir en base de datos.
- **Archivos a crear:**
  - `backend/app/services/audio_service.py`
- **Dependencias:** `TASK-AI1-1.2`, `TASK-AI1-1.3`.
- **Resultado esperado:** Servicio que orquesta validación bioética, validación técnica, guardado físico y registro relacional.
- **Pruebas necesarias:** Pruebas unitarias de validación con mock de archivos y consentimientos.
- **Criterio de terminación:** `AudioService.upload_audio` valida consentimiento, guarda binario y persiste en `public.audio`.

---

### Tarea 1.5: Endpoints REST de Audio
- **ID:** `TASK-AI1-1.5`
- **Descripción:** Implementar endpoints FastAPI para subida multipart/form-data, consulta de audios por evaluación y streaming seguro.
- **Archivos a crear:**
  - `backend/app/api/v1/endpoints/audio.py`
- **Archivos a modificar:**
  - `backend/app/api/v1/router.py` (registrar router de audio).
- **Dependencias:** `TASK-AI1-1.4`.
- **Resultado esperado:**
  - `POST /api/v1/evaluations/{evaluation_id}/audio` (HTTP 201).
  - `GET /api/v1/evaluations/{evaluation_id}/audio` (HTTP 200).
  - `GET /api/v1/audio/{audio_id}` (HTTP 200).
- **Pruebas necesarias:** Pruebas de integración HTTP con cliente `httpx.AsyncClient`.
- **Criterio de terminación:** Rutas expuestas, documentadas en Swagger OpenAPI y protegidas con `require_professional_or_admin`.

---

### Tarea 1.6: Suite de Pruebas de Integración para SCRUM-25
- **ID:** `TASK-AI1-1.6`
- **Descripción:** Desarrollar suite completa de pruebas para todos los escenarios de ingesta de audio.
- **Archivos a crear:**
  - `backend/tests/integration/test_audio_ingestion.py`
- **Dependencias:** `TASK-AI1-1.5`.
- **Resultado esperado:** Cobertura de: carga exitosa (201), consentimiento denegado (403), tamaño excesivo (413), formato inválido (422), evaluación inexistente (404).
- **Pruebas necesarias:** `pytest tests/integration/test_audio_ingestion.py`.
- **Criterio de terminación:** 100% de las pruebas de audio pasando exitosamente en SQLite en memoria.

---

## FASE 2: SCRUM-15 (Core) — Motor ASR y Preprocesamiento Canónico

### Tarea 2.1: Preprocesador Canónico de Audio (`AudioPreprocessor`)
- **ID:** `TASK-AI1-2.1`
- **Descripción:** Implementar el servicio que ejecuta FFmpeg para convertir cualquier audio recibido a WAV PCM 16-bit, 16.000 Hz mono con normalización a -20 dBFS.
- **Archivos a crear:**
  - `backend/app/services/asr/__init__.py`
  - `backend/app/services/asr/audio_preprocessor.py`
- **Dependencias:** Binario FFmpeg instalado en el sistema.
- **Resultado esperado:** Función que toma una ruta de audio de entrada y retorna la ruta del WAV canónico de 16kHz generado.
- **Pruebas necesarias:** Prueba unitaria de conversión de archivo MP3/WAV a 16kHz mono validando cabeceras con `wave` o `soundfile`.
- **Criterio de terminación:** Conversión determinista a 16kHz mono sin desincronización temporal.

---

### Tarea 2.2: Esquemas Pydantic para Transcripciones y Alineación
- **ID:** `TASK-AI1-2.2`
- **Descripción:** Definir esquemas para respuestas de transcripción, segmentos y palabras alineadas.
- **Archivos a crear:**
  - `backend/app/schemas/transcription.py`
- **Archivos a modificar:**
  - `backend/app/schemas/__init__.py`
- **Dependencias:** Ninguna.
- **Resultado esperado:** DTOs `TranscriptionResponse`, `WordAlignmentItem`, `TranscriptionDetailResponse`.
- **Pruebas necesarias:** Pruebas unitarias de serialización en `tests/unit/test_transcription_schemas.py`.
- **Criterio de terminación:** Modelos Pydantic v2 validados.

---

### Tarea 2.3: Repositorios de Transcripciones y Anotaciones
- **ID:** `TASK-AI1-2.3`
- **Descripción:** Implementar `TranscriptionRepository`, `AnnotationRepository` y `AIAnalysisRepository` para las tablas existentes.
- **Archivos a crear:**
  - `backend/app/repositories/transcription_repository.py`
  - `backend/app/repositories/annotation_repository.py`
  - `backend/app/repositories/ai_analysis_repository.py`
- **Archivos a modificar:**
  - `backend/app/repositories/__init__.py`
- **Dependencias:** `TASK-AI1-2.2`.
- **Resultado esperado:** Métodos para crear/actualizar transcripciones, inserción masiva de palabras alineadas (`bulk_insert`) y persistencia de `result_json`.
- **Pruebas necesarias:** Pruebas de integración sobre base de datos de test.
- **Criterio de terminación:** Repositorios funcionales con sesiones asíncronas de SQLAlchemy.

---

### Tarea 2.4: Motor WhisperX Singleton (`WhisperXEngine`)
- **ID:** `TASK-AI1-2.4`
- **Descripción:** Implementar la clase encargada de cargar y cachear el modelo Whisper `large-v3` mediante `faster-whisper` / `CTranslate2`, respetando la configuración (`device="cpu"`, `compute_type="int8"`).
- **Archivos a crear:**
  - `backend/app/services/asr/whisperx_engine.py`
- **Dependencias:** Dependencias ML instaladas en el entorno (`faster-whisper`, `ctranslate2`).
- **Resultado esperado:** Método `transcribe(audio_path, language="es")` que ejecuta la inferencia y devuelve texto y segmentos.
- **Pruebas necesarias:** Prueba unitaria de inferencia con audio breve de prueba en CPU.
- **Criterio de terminación:** Inferencia ASR completada sin excepciones de CUDA ni bloqueo de memoria.

---

## FASE 3: SCRUM-15 (Completo) — VAD, Forced Alignment y Persistencia Dual

### Tarea 3.1: Alineador Fonético Wav2Vec2 CTC (`AlignmentService`)
- **ID:** `TASK-AI1-3.1`
- **Descripción:** Implementar la integración de alineación forzada palabra por palabra para español (`Wav2Vec2 CTC`) sobre los segmentos emitidos por Whisper.
- **Archivos a crear:**
  - `backend/app/services/asr/alignment_service.py`
- **Dependencias:** `TASK-AI1-2.4`.
- **Resultado esperado:** Obtención de marcas de tiempo precisas (`start`, `end`) y score acústico para cada palabra transcrita.
- **Pruebas necesarias:** Prueba de alineación temporal sobre un audio sintético de palabras fonológicas (FAS).
- **Criterio de terminación:** Cada palabra contiene `start_time_seconds <= end_time_seconds` y score numérico.

---

### Tarea 3.2: Orquestador del Pipeline Asíncrono (`ASRPipelineService`)
- **ID:** `TASK-AI1-3.2`
- **Descripción:** Implementar el servicio orquestador que coordina las 10 etapas: preprocesamiento, VAD, ASR, alineación, persistencia dual y gestión de estados transicionales (`PROCESSING`, `COMPLETED`, `FAILED`).
- **Archivos a crear:**
  - `backend/app/services/asr/asr_pipeline_service.py`
- **Dependencias:** `TASK-AI1-2.1`, `TASK-AI1-2.3`, `TASK-AI1-2.4`, `TASK-AI1-3.1`.
- **Resultado esperado:** Flujo atómico que actualiza `transcriptions`, guarda palabras en `annotations` y payload en `ai_analysis`.
- **Pruebas necesarias:** Pruebas de integración de pipeline completo con mocks/fixtures de audio.
- **Criterio de terminación:** Persistencia dual atómica exitosa con rollback en caso de fallo.

---

### Tarea 3.3: Endpoints de Transcripción Asíncrona
- **ID:** `TASK-AI1-3.3`
- **Descripción:** Implementar los endpoints `POST /api/v1/audio/{audio_id}/transcribe` (HTTP 202) y `GET /api/v1/transcriptions/{transcription_id}` (HTTP 200).
- **Archivos a crear:**
  - `backend/app/api/v1/endpoints/transcriptions.py`
- **Archivos a modificar:**
  - `backend/app/api/v1/router.py` (registrar router de transcripciones).
- **Dependencias:** `TASK-AI1-3.2`.
- **Resultado esperado:** Encolamiento inmediato y consulta reactiva de estado de transcripción.
- **Pruebas necesarias:** Pruebas de integración HTTP de encolamiento y consulta de resultado.
- **Criterio de terminación:** Endpoints funcionales y documentados en OpenAPI.

---

## FASE 4: SCRUM-24 — Control de Calidad y Clasificación por Confianza

### Tarea 4.1: Evaluador de Calidad y Umbrales (`QualityControlEvaluator`)
- **ID:** `TASK-AI1-4.1`
- **Descripción:** Implementar la lógica que calcula la confianza agregada, detecta alucinaciones y compara contra `ASR_CONFIDENCE_THRESHOLD` (0.75).
- **Archivos a crear:**
  - `backend/app/services/asr/quality_control.py`
- **Dependencias:** `TASK-AI1-3.2`.
- **Resultado esperado:** Asignación automática del estado `NEEDS_REVIEW` cuando `confidence < 0.75` o se detecte repetición cíclica.
- **Pruebas necesarias:** Pruebas unitarias de cálculo de umbrales y detección de n-gramas repetidos.
- **Criterio de terminación:** Clasificación determinista de transcripciones dudosas.

---

### Tarea 4.2: Filtros y Consulta de Transcripciones Pendientes de Revisión
- **ID:** `TASK-AI1-4.2`
- **Descripción:** Agregar parámetros de consulta en el endpoint `GET /api/v1/transcriptions` para filtrar por `status=NEEDS_REVIEW` y `human_reviewed=false`.
- **Archivos a modificar:**
  - `backend/app/api/v1/endpoints/transcriptions.py`
  - `backend/app/repositories/transcription_repository.py`
- **Dependencias:** `TASK-AI1-4.1`.
- **Resultado esperado:** Listado priorizado de transcripciones que requieren revisión fonoaudiológica.
- **Pruebas necesarias:** Pruebas de integración de filtrado por estado y confianza.
- **Criterio de terminación:** Endpoint responde lista filtrada con paginación y ordenamiento por menor confianza.

---

## FASE 5: SCRUM-26 — Revisión y Curaduría Humana (Human-in-the-Loop)

### Tarea 5.1: Servicio y Endpoint de Revisión Humana
- **ID:** `TASK-AI1-5.1`
- **Descripción:** Implementar el endpoint `PATCH /api/v1/transcriptions/{transcription_id}/review` que valida roles clínicos, preserva `raw_text`, actualiza `corrected_text` y marca `human_reviewed = true`.
- **Archivos a modificar:**
  - `backend/app/services/transcription_service.py`
  - `backend/app/api/v1/endpoints/transcriptions.py`
  - `backend/app/schemas/transcription.py`
- **Dependencias:** `TASK-AI1-4.2`.
- **Resultado esperado:** Actualización atómica con auditoría clínica (`reviewer_id`, `reviewed_at`) y transición a `COMPLETED`.
- **Pruebas necesarias:** Pruebas de verificación de inmutabilidad de `raw_text`, rechazo a usuarios no autorizados (403), y actualización exitosa (200).
- **Criterio de terminación:** `raw_text` permanece idéntico tras la revisión; `corrected_text` y auditoría persistidos.

---

## FASE 6: Exportación Estructurada (Etapa 10)

### Tarea 6.1: Servicio de Exportación Multi-Formato (`ExportService`)
- **ID:** `TASK-AI1-6.1`
- **Descripción:** Implementar generadores en memoria para formatos JSON enriquecido, subtítulos SRT y Praat TextGrid compatibles con la fonética acústica.
- **Archivos a crear:**
  - `backend/app/services/asr/export_service.py`
- **Dependencias:** `TASK-AI1-3.2`.
- **Resultado esperado:** Generación de strings formateados en SRT (tiempos `00:00:00,000`) y TextGrid (intervalos `xmin`, `xmax`, tiers `words` y `utterances`).
- **Pruebas necesarias:** Pruebas unitarias de formato y sintaxis TextGrid/SRT en `tests/unit/test_export_service.py`.
- **Criterio de terminación:** Archivos válidos parseables por herramientas externas (VLC, Praat).

---

### Tarea 6.2: Endpoint de Descarga de Exportaciones
- **ID:** `TASK-AI1-6.2`
- **Descripción:** Implementar el endpoint `GET /api/v1/transcriptions/{transcription_id}/export?format={json|srt|textgrid}` con cabeceras de descarga de archivo.
- **Archivos a modificar:**
  - `backend/app/api/v1/endpoints/transcriptions.py`
- **Dependencias:** `TASK-AI1-6.1`.
- **Resultado esperado:** Descarga de archivo adjunto con `Content-Disposition: attachment`.
- **Pruebas necesarias:** Pruebas de integración HTTP verificando cabeceras y contenido binario.
- **Criterio de terminación:** Descarga instantánea (< 200 ms) sin re-ejecutar modelos de IA.
