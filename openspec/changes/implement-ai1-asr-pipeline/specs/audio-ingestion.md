# Especificación de Capacidad: Ingesta y Gestión de Audio Clínico (SCRUM-25)

- **Capacidad:** `audio-ingestion`
- **Historia de Usuario:** `SCRUM-25`
- **Módulo Backend:** `backend/app/services/audio_service.py`, `backend/app/api/v1/endpoints/audio.py`

---

## Requisito 1: Carga y Almacenamiento de Archivos de Audio

El sistema debe permitir a un usuario con rol clínico autorizado (`professional` o `admin`) subir un archivo de audio asociado a una evaluación clínica activa existente.

### Escenario 1.1: Carga exitosa de archivo de audio válido
- **Given** que el usuario autenticado tiene el rol `professional` o `admin`,
- **And** existe una evaluación activa con identificador `evaluation_id`,
- **And** el paciente vinculado a dicha evaluación tiene un consentimiento informado registrado y activo con `consent_type IN ('AUDIO_RECORDING', 'EVALUATION')` y estado `GRANTED`,
- **When** el usuario envía una petición `POST /api/v1/evaluaciones/{evaluation_id}/audio` con un archivo multipart válido (`.wav`, `audio/wav`, tamaño $\le 50$ MB),
- **Then** el sistema almacena el binario del archivo de forma segura en el almacenamiento configurado (disco local o Supabase Storage),
- **And** persiste un nuevo registro en la tabla `public.audio` con `evaluation_id`, `file_name`, `file_path`, `mime_type`, `file_size_bytes`, `duration_seconds` extraído del archivo, `recorded_at` y `active = true`,
- **And** responde con código HTTP `201 Created` y los metadatos completos del audio creado.

### Escenario 1.2: Rechazo por evaluación inexistente o inactiva
- **Given** que el usuario autenticado tiene rol `professional`,
- **When** envía una petición `POST /api/v1/evaluations/{evaluation_id}/audio` con un UUID de evaluación que no existe en la base de datos o está marcado como inactivo (`active = false`),
- **Then** el sistema no almacena ningún archivo físico en el almacenamiento,
- **And** responde con código HTTP `404 Not Found` y código de error de dominio `ENTITY_NOT_FOUND`.

---

## Requisito 2: Control Bioético de Consentimiento Informado

El sistema debe verificar de forma estricta que el paciente haya otorgado consentimiento para la grabación de audio antes de permitir el almacenamiento del archivo.

### Escenario 2.1: Rechazo por consentimiento denegado o retirado
- **Given** que existe una evaluación activa vinculada a un paciente,
- **And** el paciente tiene su consentimiento en estado `DENIED` o `WITHDRAWN`, o no tiene ningún consentimiento registrado para `AUDIO_RECORDING` o `EVALUATION`,
- **When** el usuario intenta subir un archivo de audio para dicha evaluación,
- **Then** el sistema no persiste el archivo en el sistema de almacenamiento,
- **And** rechaza la solicitud inmediatamente con código HTTP `403 Forbidden`,
- **And** retorna un mensaje de error que indica que se requiere consentimiento informado previo para registrar grabaciones sonoras.

---

## Requisito 3: Validación Técnica de Formato y Tamaño

El sistema debe validar el formato MIME, la integridad del contenedor y el tamaño del archivo de audio para prevenir archivos corruptos o ataques de denegación de servicio.

### Escenario 3.1: Rechazo de formatos no admitidos
- **Given** una evaluación activa con consentimiento otorgado,
- **When** el usuario envía un archivo con formato no soportado (ej. `.pdf`, `.exe`, o MIME `text/plain`),
- **Then** el sistema no almacena el archivo,
- **And** responde con código HTTP `422 Unprocessable Entity` indicando los formatos de audio admitidos (`audio/wav`, `audio/x-wav`, `audio/mpeg`, `audio/mp4`, `audio/x-m4a`, `audio/ogg`, `audio/webm`).

### Escenario 3.2: Rechazo de archivos que superan el tamaño máximo
- **Given** una evaluación activa con consentimiento otorgado,
- **When** el usuario envía un archivo cuyo peso supera el límite configurado (`MAX_AUDIO_SIZE_MB`, por defecto 50 MB),
- **Then** el sistema interrumpe la carga sin escribir en la base de datos,
- **And** responde con código HTTP `413 Payload Too Large`.

---

## Requisito 4: Consulta y Acceso a Grabaciones de Audio

El sistema debe permitir consultar y acceder a las grabaciones registradas de una evaluación con control de acceso por roles.

### Escenario 4.1: Listado de audios de una evaluación
- **Given** una evaluación activa que posee 2 archivos de audio registrados,
- **When** un usuario autorizado envía una petición `GET /api/v1/evaluations/{evaluation_id}/audio`,
- **Then** el sistema responde con código HTTP `200 OK` y una lista de los metadatos de los audios asociados activos, ordenados cronológicamente por `recorded_at`.

### Escenario 4.2: Consulta de un audio específico con URL de acceso
- **Given** un audio registrado con identificador `audio_id`,
- **When** un usuario autorizado envía una petición `GET /api/v1/audio/{audio_id}`,
- **Then** el sistema responde con HTTP `200 OK` conteniendo los metadatos y una URL segura de acceso o streaming con expiración temporal.
