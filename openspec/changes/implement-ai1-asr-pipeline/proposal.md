# Propuesta OpenSpec: Implementación del Pipeline ASR (AI1) en LINGUA

- **Identificador del Cambio:** `implement-ai1-asr-pipeline`
- **Subsistema:** `AI1 — Automatic Speech Recognition Pipeline`
- **Fecha de Propuesta:** 24 de noviembre de 2026
- **Estado:** Propuesto (Borrador de Especificación Técnica)
- **Autor:** Arquitectura de Software LINGUA

---

## 1. Problema Actual

La plataforma LINGUA cuenta actualmente con la gestión completa de pacientes, consentimientos informados bioéticos y sesiones de evaluación clínica neuropsicológica (ej. Fluencia Verbal FAS). Sin embargo, el subsistema de procesamiento sonoro se encuentra completamente desconectado:

1. **Inexistencia de Ingesta de Audio:** No existe infraestructura de backend para que los profesionales fonoaudiólogos o evaluadores suban, almacenen y vinculen grabaciones de voz a las evaluaciones o subpruebas aplicadas.
2. **Latencia del Pipeline de Transcripción:** Aunque existen modelos ORM en base de datos (`audio`, `transcriptions`, `annotations`, `ai_analysis`), no existe ningún servicio, repositorio ni endpoint que procese las grabaciones sonoras.
3. **Transcripción Manual Ineficiente:** Los profesionales de fonoaudiología deben transcribir manualmente cada segundo de audio de las pruebas de fluencia verbal, lo cual consume tiempo clínico crítico, introduce sesgos ortográficos y carece de alineación temporal precisa (impidiendo medir silencios, latencias y pausas articulatorias con rigor milimétrico).
4. **Vulnerabilidad ante Fallas de ASR en Habla Patológica:** Los modelos estándar de reconocimiento automático de voz fallan severamente ante el habla afásica (parafasias fonémicas, titubeos, neologismos). Sin un mecanismo de control de calidad por confianza y curaduría profesional (*Human-in-the-Loop*), la información transcrita no puede ser utilizada para investigación clínica ni caracterización computacional del lenguaje.

---

## 2. Justificación de AI1

El subsistema **AI1 (ASR Pipeline)** constituye el núcleo de procesamiento sonoro de LINGUA. Su implementación automatiza la conversión del habla clínica en texto enriquecido mediante el estado del arte en modelos de reconocimiento del habla:

- Utiliza **WhisperX**, integrando **Whisper large-v3** optimizado con **CTranslate2**, **Voice Activity Detection (VAD)** para suprimir ruidos/silencios, y **alineación forzada a nivel de palabra mediante Wav2Vec2 CTC** específico para el idioma español.
- Resuelve la necesidad clínica fundamental de obtener la transcripción exacta de cada palabra junto con sus marcas temporales de inicio (`start_time`) y fin (`end_time`).
- Implementa un paradigma ético de **curaduría profesional obligatoria (*Human-in-the-Loop*)**, permitiendo identificar automáticamente transcripciones de baja confianza y habilitando al especialista a validar o corregir el texto sin alterar la inmutabilidad forense del resultado bruto de la IA (`raw_text`).

---

## 3. Objetivos Funcionales

1. **Ingesta y Validación de Audio Clínico (SCRUM-25):** Permitir a los evaluadores autorizados cargar grabaciones sonoras vinculadas a evaluaciones o subpruebas, validando previamente que el paciente cuente con consentimiento informado activo (`AUDIO_RECORDING`).
2. **Transcripción Automática Fonológica y Semántica (SCRUM-15):** Generar de forma asíncrona la transcripción literal del habla en español (`raw_text`) con alineación temporal palabra por palabra.
3. **Control de Calidad y Confianza ASR (SCRUM-24):** Evaluar cuantitativamente la confianza del reconocimiento y clasificar las transcripciones dudosas (umbral inicial referencial $< 0.75$) bajo el estado `NEEDS_REVIEW` para priorizar la supervisión humana.
4. **Curaduría y Revisión Humana (SCRUM-26):** Proveer la funcionalidad para que el profesional edite el texto corregido (`corrected_text`), certifique la revisión clínica (`human_reviewed = true`) y registre su autoría sin modificar el `raw_text` original.
5. **Exportación Estructurada Multi-Formato:** Generar y descargar artefactos estandarizados en formato JSON estructurado (palabra por palabra con scores), subtítulos SRT/VTT y archivos de análisis fonético Praat TextGrid.

---

## 4. Objetivos Técnicos

1. **Preservación Arquitectónica:** Integrar AI1 dentro del monolito modular existente de FastAPI en `backend/app/services/asr/` sin introducir microservicios innecesarios ni romper el patrón por capas (API $\rightarrow$ Servicios $\rightarrow$ Repositorios $\rightarrow$ Modelos).
2. **Desacoplamiento y Asincronía:** Evitar el bloqueo del event loop de Uvicorn durante la inferencia intensiva, gestionando la ejecución en background (con control de concurrencia mediante semáforos) y estados transicionales (`PENDING` $\rightarrow$ `PROCESSING` $\rightarrow$ `COMPLETED` / `NEEDS_REVIEW` / `FAILED`).
3. **Persistencia Dual Consistente:**
   - *Persistencia Relacional:* En `transcriptions` (cabecera) y `annotations` (palabras alineadas en PostgreSQL).
   - *Persistencia Documental:* En `ai_analysis.result_json` (payload estructurado completo de WhisperX en formato JSONB).
4. **Portabilidad de Hardware (CPU en Desarrollo / GPU en Producción):**
   - Permitir ejecución local en CPU con CTranslate2 en cuantización `int8` sobre instrucciones AVX2 (adecuado para el procesador anfitrión Intel Core i5-10600K).
   - Permitir alternancia mediante configuración de entorno (`ASR_DEVICE=cuda`, `ASR_COMPUTE_TYPE=float16`) para despliegue productivo sobre aceleradoras NVIDIA.
5. **Almacenamiento Conectable:** Implementar una interfaz unificada `StorageService` con soporte para disco local protegido y para Supabase Storage (bucket privado `clinical-audio`).

---

## 5. Alcance de la Implementación

### Dentro del Alcance
- Ingesta, almacenamiento, validación de formato, extracción de metadatos y eliminación lógica de audios.
- Preprocesamiento de audio a formato canónico WAV PCM 16kHz mono mediante FFmpeg.
- VAD (detección de habla activa y supresión de silencios) mediante Pyannote / Silero VAD integrado.
- Inferencia ASR en español con Whisper large-v3 y CTranslate2.
- Alineación temporal palabra por palabra mediante Wav2Vec2 CTC.
- Clasificación de calidad por umbral de confianza y detección de alucinaciones por repetición.
- Endpoint de revisión humana para guardar `corrected_text` y certificar `human_reviewed`.
- Exportadores a JSON, SRT y Praat TextGrid.
- Suite de pruebas unitarias y de integración para cada fase.

### Fuera del Alcance
- **AI2 (Extracción de Features Lingüísticas Avanzadas y Diagnóstico Autónomo):** No se calcula densidad léxica profunda ni clasificación de afasias en este subsistema.
- **Frontend / Interfaz Gráfica:** Este cambio comprende exclusivamente los endpoints, servicios, repositorios y persistencia en el backend REST.
- **Servicios Externos Propietarios:** No se permite el uso de APIs externas de transcripción de pago (como OpenAI Whisper API o Google Cloud Speech); la inferencia debe ser autónoma, privada y on-premise/self-hosted.

---

## 6. Historias de Usuario Involucradas

1. **SCRUM-25:** Ingesta y gestión de grabaciones de audio clínico de la evaluación.
2. **SCRUM-15:** Transcripción automática ASR con alineación temporal palabra por palabra.
3. **SCRUM-24:** Control de calidad y clasificación por confianza ASR.
4. **SCRUM-26:** Revisión, edición y certificación humana de transcripciones clínicas.

---

## 7. Beneficios Esperados

- **Clínico:** Disminución de más del 80% en el tiempo dedicado a la transcripción manual de pruebas verbales como el FAS.
- **Científico:** Precisión temporal milimétrica indispensable para la investigación de latencias fonológicas, pausas hesitativas y velocidad de habla.
- **Bioético y Forense:** Cumplimiento del principio *Human-in-the-Loop* de LINGUA, garantizando que el profesional siempre tenga la última palabra y que el texto crudo generado por la máquina permanezca inmutable.
- **Técnico:** Desacoplamiento total y escalabilidad controlada mediante persistencia dual y aislamiento de recursos.

---

## 8. Restricciones Técnicas

1. **Prohibición de Cambios Destructivos en Base de Datos:** Se deben reutilizar estrictamente las tablas ya migradas en PostgreSQL (`audio`, `transcriptions`, `annotations`, `ai_analysis`).
2. **Validación Bioética Ineludible:** Ningún archivo de audio puede ser subido o procesado si el paciente no tiene un consentimiento registrado en estado `GRANTED` para `AUDIO_RECORDING` o `EVALUATION`.
3. **No Bloqueo del Event Loop:** La inferencia no puede invocarse de manera síncrona dentro del ciclo de solicitud-respuesta HTTP.
4. **Hardware Local:** En el entorno de desarrollo actual (Windows, Intel i5, sin GPU NVIDIA), el pipeline debe operar de forma estable en CPU con cuantización `int8`.
5. **Inmutabilidad de `raw_text`:** Bajo ninguna circunstancia la edición profesional puede sobrescribir el texto original emitido por WhisperX.

---

## 9. Dependencias

- **Dependencias de Sistema:** Binario `ffmpeg` y biblioteca `libsndfile1` disponibles en el PATH del sistema o contenedor Docker.
- **Dependencias Internas de LINGUA:**
  - `Evaluation` y `EvaluationRepository` (para anclaje de sesiones clínicas).
  - `ConsentService.is_consent_granted()` (para verificación ética).
  - `require_professional_or_admin` (para protección RBAC de rutas).
- **Dependencias de Machine Learning:**
  - `torch` y `torchaudio`.
  - `ctranslate2` y `faster-whisper`.
  - `whisperx` y `transformers`.
  - Checkpoint del modelo Whisper `large-v3` y modelo de alineación para español (`facebook/wav2vec2-large-xlsr-53-spanish`).
  - Token de Hugging Face (`HUGGINGFACE_TOKEN`) para Pyannote VAD (o uso de Silero VAD como alternativa sin credenciales).

---

## 10. Criterios Generales de Aceptación del Cambio

1. **SCRUM-25 (Audio):** Un profesional autenticado puede subir un archivo de audio (.wav, .mp3, etc.) asociado a una evaluación; el sistema valida el consentimiento del paciente, almacena el binario y registra metadatos precisos en `public.audio`.
2. **SCRUM-15 (ASR):** Dado un `audio_id` registrado, el sistema ejecuta de forma asíncrona el preprocesamiento a 16kHz mono, VAD, inferencia con Whisper large-v3 y alineación forzada, persistiendo el `raw_text` en `transcriptions`, las palabras alineadas en `annotations` y el JSON enriquecido en `ai_analysis`.
3. **SCRUM-24 (Calidad):** Si la confianza media es inferior a 0.75 o se detectan anomalías de alucinación, la transcripción pasa al estado `NEEDS_REVIEW` y es consultable mediante filtros específicos.
4. **SCRUM-26 (Curaduría):** Un profesional puede actualizar el `corrected_text` y certificar la revisión (`human_reviewed = true`), registrando su `reviewer_id` y `reviewed_at`, sin alterar el `raw_text`.
5. **Exportación:** El profesional puede descargar el resultado en formato JSON estructurado, subtítulos SRT y Praat TextGrid.
6. **No Regresión:** Las 35 pruebas automatizadas existentes del backend de LINGUA continúan pasando al 100%.
