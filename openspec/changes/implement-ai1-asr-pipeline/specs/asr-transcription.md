# Especificación de Capacidad: Transcripción Automática ASR (SCRUM-15)

- **Capacidad:** `asr-transcription`
- **Historia de Usuario:** `SCRUM-15`
- **Módulo Backend:** `backend/app/services/asr/`, `backend/app/api/v1/endpoints/transcriptions.py`

---

## Requisito 1: Preprocesamiento Canónico de Audio

El sistema debe convertir cualquier grabación de audio admitida a un formato canónico normalizado para alimentar de manera homogénea a los modelos de espectrograma mel (VAD, Whisper y Wav2Vec2).

### Escenario 1.1: Conversión exitosa a formato canónico
- **Given** un archivo de audio registrado en la tabla `public.audio`,
- **When** se inicia el preprocesamiento de la grabación,
- **Then** el componente `AudioPreprocessor` invoca FFmpeg para generar un flujo de audio canónico con:
  - Formato: WAV PCM 16-bit sin compresión con pérdidas (`pcm_s16le`).
  - Frecuencia de muestreo: exactamente 16.000 Hz (16 kHz).
  - Canales: exactamente 1 canal (mono).
  - Normalización de amplitud: normalización de picos o RMS a nivel estándar (-20 dBFS).
- **And** el archivo preprocesado se almacena temporalmente y se elimina de forma segura una vez concluida la sesión de inferencia.

---

## Requisito 2: Detección de Actividad Vocal (VAD)

El sistema debe segmentar el audio en fragmentos de habla activa (*speech segments*), identificando y suprimiendo silencios prolongados y ruido de fondo antes de la decodificación.

### Escenario 2.1: Segmentación vocal de prueba FAS
- **Given** un audio canónico correspondiente a una prueba de fluencia verbal FAS de 60 segundos,
- **When** se ejecuta el módulo de VAD (Pyannote-audio VAD o Silero VAD integrado),
- **Then** el sistema produce una lista ordenada de intervalos temporales con marcas de inicio (`start`) y fin (`end`) que contienen energía vocal,
- **And** descarta los intervalos mudos o con solo ruido ambiental no fonético.

---

## Requisito 3: Inferencia ASR con Whisper large-v3 y CTranslate2

El sistema debe transcribir los segmentos de habla activa utilizando el motor `faster-whisper` con el modelo Whisper `large-v3`, configurado para el idioma español.

### Escenario 3.1: Generación de texto crudo literal
- **Given** los segmentos vocales preprocesados y el idioma configurado como español (`es`),
- **When** el motor `WhisperXEngine` ejecuta la inferencia ASR mediante CTranslate2,
- **Then** se obtiene el texto continuo transcrito literalmente (`raw_text`),
- **And** se registran las probabilidades logarítmicas de los tokens,
- **And** se identifica el modelo utilizado (`asr_model = 'whisper-large-v3'`) y su versión de checkpoint (`model_version`).

### Escenario 3.2: Ejecución local adaptada a CPU con INT8
- **Given** que el entorno de ejecución está configurado con `ASR_DEVICE=cpu` y `ASR_COMPUTE_TYPE=int8`,
- **When** se ejecuta la inferencia,
- **Then** CTranslate2 ejecuta el modelo cuantizado en 8 bits utilizando instrucciones vectoriales AVX2 del procesador,
- **And** no requiere llamadas a librerías CUDA ni genera excepciones por falta de GPU NVIDIA.

---

## Requisito 4: Alineación Forzada Palabra a Palabra

El sistema debe alinear temporalmente cada palabra del texto transcrito contra la señal acústica utilizando un modelo fonético Wav2Vec2 CTC específico para español.

### Escenario 4.1: Alineación milimétrica de palabras
- **Given** el texto transcrito y la señal de audio de 16 kHz,
- **When** se ejecuta el módulo de alineación forzada (`Wav2Vec2 CTC`),
- **Then** para cada palabra del `raw_text` se generan:
  - Palabra transcrita (`word`).
  - Marca de tiempo inicial en segundos (`start_time_seconds`).
  - Marca de tiempo final en segundos (`end_time_seconds`).
  - Puntuación de confianza acústica del alineador (`confidence`).

---

## Requisito 5: Persistencia Dual Consistente

El resultado del procesamiento debe persistirse atómicamente combinando entidades relacionales para consulta SQL rápida y un payload documental JSONB para trazabilidad profunda.

### Escenario 5.1: Guardado dual atómico exitoso
- **Given** una sesión de transcripción finalizada exitosamente para un `audio_id`,
- **When** se ejecuta el servicio de persistencia,
- **Then** se inserta o actualiza un registro en `public.transcriptions` con `raw_text`, `language = 'es'`, `asr_model`, `confidence` global y `processing_status = 'COMPLETED'`,
- **And** se insertan registros en `public.annotations` vinculados a la transcripción con `annotation_type = 'WORD'`, conteniendo `text = word`, `start_time_seconds`, `end_time_seconds` y `confidence`,
- **And** se inserta un registro en `public.ai_analysis` vinculado a la evaluación y la transcripción con `model_name = 'whisperx-large-v3'` y `result_json` conteniendo el payload JSON estructurado completo de WhisperX (segmentos, palabras y metadatos).

---

## Requisito 6: Ejecución Asíncrona Desacoplada

La solicitud de transcripción debe responder inmediatamente al cliente y ejecutar el cómputo en segundo plano con control estricto de concurrencia.

### Escenario 6.1: Encolamiento y consulta de estado
- **Given** un audio registrado con identificador `audio_id`,
- **When** un usuario autorizado envía una petición `POST /api/v1/audio/{audio_id}/transcribe`,
- **Then** el sistema crea un registro inicial en `public.transcriptions` con `processing_status = 'PENDING'`,
- **And** responde inmediatamente con código HTTP `202 Accepted` y el `transcription_id`,
- **And** delega la ejecución de AI1 a un worker en segundo plano protegido por un semáforo de concurrencia (`MAX_CONCURRENT_ASR_JOBS`).
