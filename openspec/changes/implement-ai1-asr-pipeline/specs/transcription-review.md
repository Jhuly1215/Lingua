# Especificación de Capacidad: Revisión y Curaduría Humana (SCRUM-26)

- **Capacidad:** `transcription-review`
- **Historia de Usuario:** `SCRUM-26`
- **Módulo Backend:** `backend/app/services/transcription_service.py`, `backend/app/api/v1/endpoints/transcriptions.py`

---

## Requisito 1: Inmutabilidad Forense del Texto Crudo (`raw_text`)

El sistema debe garantizar bajo cualquier circunstancia que el texto generado originalmente por el motor de inteligencia artificial no sea sobrescrito, alterado ni eliminado durante la intervención humana.

### Escenario 1.1: Preservación de `raw_text` tras la corrección
- **Given** una transcripción existente con `raw_text = "perro foca flor fita"`,
- **When** el profesional clínico edita la transcripción corrigiendo una parafasia a `corrected_text = "perro foca flor fruta"`,
- **Then** el valor de `transcriptions.raw_text` permanece estrictamente como `"perro foca flor fita"`,
- **And** el nuevo texto revisado se almacena exclusivamente en la columna `transcriptions.corrected_text`.

---

## Requisito 2: Edición y Certificación Humana de la Transcripción

El sistema debe permitir a un profesional de la salud certificar la corrección de una transcripción clínica, registrando su autoría y marca temporal.

### Escenario 2.1: Registro exitoso de revisión humana
- **Given** una transcripción activa con `human_reviewed = false`,
- **And** un usuario autenticado con rol `professional` cuyo identificador es `user_id`,
- **When** el usuario envía una petición `PATCH /api/v1/transcriptions/{transcription_id}/review` con el payload:
  ```json
  {
    "corrected_text": "perro foca flor fruta fuente",
    "observations": "Se corrigió parafasia fonémica en el segundo 24"
  }
  ```
- **Then** el sistema actualiza de forma atómica:
  - `corrected_text`: texto ingresado y saneado.
  - `human_reviewed`: pasa a `true`.
  - `reviewer_id`: se asigna automáticamente al `user_id` del usuario autenticado en el token JWT.
  - `reviewed_at`: marca temporal actual con zona horaria UTC (`CURRENT_TIMESTAMP`).
  - `processing_status`: se actualiza a `'COMPLETED'`.
- **And** responde con código HTTP `200 OK` y el objeto de la transcripción actualizada.

### Escenario 2.2: Rechazo de corrección vacía
- **Given** una transcripción existente,
- **When** el usuario envía una petición de revisión con `corrected_text` vacío o compuesto únicamente por espacios en blanco,
- **Then** el sistema rechaza la operación con código HTTP `422 Unprocessable Entity`,
- **And** no altera los campos de auditoría ni el estado de la transcripción.

---

## Requisito 3: Control de Permisos y Autorización (RBAC)

Solo profesionales clínicos habilitados o administradores del sistema pueden validar y certificar una transcripción médica.

### Escenario 3.1: Rechazo de revisión por usuario sin rol clínico
- **Given** un usuario autenticado con rol `researcher` (investigador con permisos de solo lectura de datos autorizados),
- **When** intenta enviar una petición `PATCH /api/v1/transcriptions/{transcription_id}/review`,
- **Then** el sistema deniega el acceso con código HTTP `403 Forbidden`,
- **And** retorna código de error `INSUFFICIENT_PERMISSIONS`.
