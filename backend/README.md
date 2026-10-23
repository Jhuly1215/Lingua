# LINGUA — Backend Inicial (FastAPI + PostgreSQL en Supabase)

**Plataforma Computacional para la Investigación y Caracterización del Lenguaje en Personas con Afasia**

---

## 1. Contexto y Enfoque Clínico

LINGUA es una plataforma diseñada para apoyar a profesionales de fonoaudiología, neurología e investigadores en el registro de pacientes, administración de evaluaciones del lenguaje (ej. Fluencia Verbal FAS) y caracterización computacional del lenguaje.

> [!IMPORTANT]
> **Aviso clínico y ético:** LINGUA está concebida como herramienta de investigación y apoyo a la evaluación clínica profesional. **No emite diagnósticos clínicos autónomos ni sustituye el criterio, valoración ni juicio de los profesionales de la salud.**

---

## 2. Arquitectura del Sistema

La solución adopta una arquitectura de **Monolito Modular** orientada al dominio clínico, estructurada en capas desacopladas con inversión de dependencias:

```
┌────────────────────────────────────────────────────────┐
│             Frontend (React + TypeScript)              │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP REST / Bearer JWT
                            ▼
┌────────────────────────────────────────────────────────┐
│             FastAPI (Routers /api/v1)                  │
├───────────────────────────┬────────────────────────────┤
│   Capa de Dependencias    │ • Supabase Auth JWT        │
│   y Seguridad             │ • RBAC (Roles de Usuario)  │
├───────────────────────────┼────────────────────────────┤
│   Capa de Servicios       │ • Validación de Dominio    │
│   (Business Logic)        │ • Reglas Clínicas FAS      │
├───────────────────────────┼────────────────────────────┤
│   Capa de Repositorios    │ • Consultas SQLAlchemy 2.x │
│   (Data Access Layer)     │ • Borrado lógico (active)  │
└───────────────────────────┬────────────────────────────┘
                            │ Pool asyncpg / SSL
                            ▼
┌────────────────────────────────────────────────────────┐
│         Supabase PostgreSQL (Database v0.2)           │
│         (19 Tablas del Diccionario Oficial)            │
└────────────────────────────────────────────────────────┘
```

---

## 3. Estructura del Proyecto

```
backend/
├── app/
│   ├── main.py                     # Instancia FastAPI, CORS y Exception Handlers
│   ├── core/
│   │   ├── config.py               # Pydantic Settings con detección de Pooler Supabase
│   │   ├── exceptions.py           # Excepciones de dominio tipadas (401, 403, 404, 409, 422)
│   │   ├── logging.py              # Logging estructurado con enmascaramiento de secretos
│   │   └── security.py             # Verificación de JWT de Supabase Auth
│   ├── db/
│   │   ├── base.py                 # DeclarativeBase, GUID agnóstico y AuditMixin
│   │   ├── session.py              # Motor AsyncEngine, sesiones y comprobación de salud
│   │   └── models/                 # Modelos ORM exactos al Diccionario v0.2
│   │       ├── role.py             # roles
│   │       ├── user.py             # users
│   │       ├── patient.py          # patients
│   │       ├── clinical_event.py   # clinical_events
│   │       ├── catalogs.py         # aphasia_types, severity_levels
│   │       ├── protocol.py         # protocols
│   │       ├── subtest.py          # subtests
│   │       ├── evaluation.py       # evaluations, evaluation_subtests
│   │       ├── consent.py          # patient_consents
│   │       └── pipeline.py         # items, responses, audio, transcriptions, etc.
│   ├── api/
│   │   └── v1/
│   │       ├── router.py           # Agrupador de rutas /api/v1
│   │       └── endpoints/
│   │           ├── health.py       # /health y /health/database
│   │           ├── auth.py         # /me
│   │           ├── patients.py     # CRUD pacientes, eventos, consentimientos, evaluaciones
│   │           ├── evaluations.py  # Detalle de evaluación y subpruebas
│   │           └── protocols.py    # Protocolos FAS y catálogos clínicos
│   ├── schemas/                    # Modelos de validación Pydantic v2
│   ├── services/                   # Lógica de negocio (US-01 a US-06)
│   ├── repositories/               # Abstracción de acceso a datos
│   ├── dependencies/               # Inyección de dependencias (Auth, DB)
│   └── utils/                      # Funciones auxiliares
├── alembic/                        # Migraciones versionadas
│   ├── env.py                      # Configuración de migraciones con app models
│   └── versions/
│       └── 20261021_0100_0001_initial_schema.py # Migración inicial 19 tablas
├── tests/
│   ├── conftest.py                 # Fixtures con SQLite en memoria y tokens mock
│   ├── unit/                       # Pruebas unitarias de esquemas y seguridad
│   └── integration/                # Pruebas de integración de endpoints
├── scripts/
│   ├── init_db.py                  # Creación de esquema y seed directo
│   └── seed_catalogs.py            # Población idempotente de catálogos
├── .env.example                    # Plantilla de variables sin secretos
├── .gitignore                      # Reglas de exclusión para Git
├── alembic.ini                     # Configuración de Alembic
├── pyproject.toml                  # Configuración de proyecto y pytest
├── requirements.txt                # Dependencias fijadas del backend
├── Dockerfile                      # Contenedor seguro sin root
└── README.md                       # Documentación técnica en español
```

---

## 4. Requisitos Previos e Instalación

### Requisitos del Sistema
- **Python:** 3.11 o 3.12
- **Gestor de paquetes:** `pip`
- **PostgreSQL / Supabase:** Proyecto creado en [supabase.com](https://supabase.com)

### Paso 1: Clonar e ingresar al directorio
```bash
cd backend
```

### Paso 2: Crear y activar entorno virtual
En Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 3: Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. Configuración de Supabase y Variables de Entorno

Copia el archivo de ejemplo a `.env`:
```bash
cp .env.example .env
```

### Cómo obtener las credenciales en Supabase:
1. Ingresa a tu proyecto en el panel de **Supabase**.
2. **Cadenas de Conexión a la Base de Datos:**
   - Ve a `Project Settings` → `Database` → `Connection string`.
   - **Direct Connection (Puerto 5432):**
     `DATABASE_URL="postgresql+asyncpg://postgres:[TU_PASSWORD]@[HOST]:5432/postgres"`
   - **Transaction Pooler (Puerto 6543 con PgBouncer):**
     `DATABASE_URL="postgresql+asyncpg://postgres.[REF]:[TU_PASSWORD]@[POOLER_HOST]:6543/postgres"`
     *Nota:* La aplicación detecta automáticamente el puerto `6543` y desactiva el caché de sentencias preparadas de `asyncpg` para evitar errores de protocolo con PgBouncer.
3. **Claves de API y JWT:**
   - Ve a `Project Settings` → `API`.
   - Copia `Project URL` en `SUPABASE_URL`.
   - Copia `anon public` en `SUPABASE_ANON_KEY`.
   - Copia `JWT Secret` en `SUPABASE_JWT_SECRET`.
   - Mantén `JWT_AUDIENCE="authenticated"`.

---

## 6. Migraciones y Población de Datos Iniciales

### Aplicar migraciones con Alembic:
```bash
alembic upgrade head
```

### O inicializar tablas y catálogos con el script automatizado:
```bash
python scripts/init_db.py
```

### Poblar catálogos únicamente (idempotente):
```bash
python scripts/seed_catalogs.py
```
Este script inserta de forma segura y sin duplicados:
- **Roles:** `admin`, `professional`, `researcher`
- **Catálogo de Afasias:** `Broca`, `Wernicke`, `Conducción`, `Global`, `Anómica`, `Transcortical Motora`, `Transcortical Sensorial`, `Transcortical Mixta`, `Mixta` y `No clasificada`.
- **Niveles de Severidad:** `Normal / Sin afasia`, `Leve`, `Moderada`, `Severa`, `Profunda`.
- **Protocolo FAS:** `Fluencia Verbal FAS` con sus 4 subpruebas estándar (Letra F, Letra A, Letra S, Semántica Animales).

---

## 7. Ejecución del Servidor de Desarrollo

Inicia Uvicorn con recarga en vivo:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Acceso a la documentación interactiva:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 8. Ejecución de Pruebas Automatizadas

El proyecto incluye una suite completa de pruebas unitarias y de integración que se ejecutan sobre una base de datos SQLite asíncrona en memoria, sin requerir credenciales externas:

```bash
pytest -v
```

Con reporte de cobertura:
```bash
pytest --cov=app --cov-report=term-missing
```

---

## 9. Tabla de Endpoints, Permisos y Dependencias

| Método | Endpoint | Roles Permitidos | Descripción |
|---|---|---|---|
| `GET` | `/api/v1/health` | Público | Comprobación de salud de la API |
| `GET` | `/api/v1/health/database` | Público | Comprobación de conectividad y latencia con PostgreSQL |
| `GET` | `/api/v1/me` | Autenticado | Perfil clínico y rol del usuario actual |
| `GET` | `/api/v1/patients` | `professional`, `admin` | Listado paginado con búsqueda por código o nombre |
| `POST` | `/api/v1/patients` | `professional`, `admin` | Registro de nuevo paciente |
| `GET` | `/api/v1/patients/{patient_id}` | `professional`, `admin` | Consulta de paciente por UUID |
| `PATCH` | `/api/v1/patients/{patient_id}` | `professional`, `admin` | Actualización de campos permitidos |
| `DELETE` | `/api/v1/patients/{patient_id}` | `professional`, `admin` | Eliminación lógica (`active = false`) |
| `GET` | `/api/v1/patients/{patient_id}/clinical-events` | `professional`, `admin` | Listado de eventos neurológicos del paciente |
| `POST` | `/api/v1/patients/{patient_id}/clinical-events` | `professional`, `admin` | Registro de evento clínico (ACV, TCE, etc.) |
| `GET` | `/api/v1/patients/{patient_id}/consents` | `professional`, `admin` | Historial de consentimientos del paciente |
| `POST` | `/api/v1/patients/{patient_id}/consents` | `professional`, `admin` | Registro de consentimiento informado |
| `GET` | `/api/v1/patients/{patient_id}/evaluations` | `professional`, `admin` | Evaluaciones administradas al paciente |
| `POST` | `/api/v1/patients/{patient_id}/evaluations` | `professional`, `admin` | Crear evaluación para el paciente |
| `GET` | `/api/v1/evaluations/{evaluation_id}` | `professional`, `admin` | Detalle de evaluación y sus subpruebas |
| `PATCH` | `/api/v1/evaluations/{evaluation_id}` | `professional`, `admin` | Actualizar estado u observaciones |
| `GET` | `/api/v1/evaluations/{evaluation_id}/subtests` | `professional`, `admin` | Subpruebas asociadas a una evaluación |
| `POST` | `/api/v1/evaluations/{evaluation_id}/subtests` | `professional`, `admin` | Configurar subprueba (duración FAS, etc.) |
| `GET` | `/api/v1/protocols` | Autenticado | Listar protocolos activos |
| `GET` | `/api/v1/protocols/{protocol_id}` | Autenticado | Detalle de protocolo con subpruebas ordenadas |
| `GET` | `/api/v1/protocols/{protocol_id}/subtests` | Autenticado | Subpruebas de un protocolo |
| `GET` | `/api/v1/catalogs/aphasia-types` | Autenticado | Catálogo de tipos de afasia |
| `GET` | `/api/v1/catalogs/severity-levels` | Autenticado | Catálogo de niveles de severidad |

---

## 10. Ejemplos de Peticiones y Respuestas HTTP

### A. Crear Paciente (`POST /api/v1/patients`)
**Headers:**
```http
Authorization: Bearer <supabase_jwt_token>
Content-Type: application/json
```
**Request Body:**
```json
{
  "patient_code": "PAC-2026-0042",
  "first_name": "Mario",
  "last_name": "Sarmiento",
  "date_of_birth": "1963-08-14",
  "gender": "Masculino",
  "education_years": 12,
  "occupation": "Carpintero",
  "handedness": "Diestro",
  "primary_language": "Español",
  "bilingual": false,
  "dialect_region": "Andina",
  "medical_record_number": "HC-10492",
  "clinical_background": "Hipertensión arterial diagnosticada en 2018",
  "notes": "Acude acompañado de su hija"
}
```
**Response (HTTP 201 Created):**
```json
{
  "patient_id": "c7a8b3f2-89b4-4e2a-8d3e-1b8f9e2a3c4d",
  "patient_code": "PAC-2026-0042",
  "first_name": "Mario",
  "last_name": "Sarmiento",
  "date_of_birth": "1963-08-14",
  "gender": "Masculino",
  "education_years": 12,
  "occupation": "Carpintero",
  "handedness": "Diestro",
  "primary_language": "Español",
  "bilingual": false,
  "secondary_language": null,
  "dialect_region": "Andina",
  "medical_record_number": "HC-10492",
  "clinical_background": "Hipertensión arterial diagnosticada en 2018",
  "notes": "Acude acompañado de su hija",
  "active": true,
  "created_at": "2026-10-21T01:15:30.123456Z",
  "updated_at": "2026-10-21T01:15:30.123456Z"
}
```

### B. Asociar Subprueba FAS a Evaluación (`POST /api/v1/evaluations/{id}/subtests`)
**Request Body:**
```json
{
  "subtest_id": "d1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a",
  "duration_seconds": 60.0,
  "status": "PENDING",
  "observations": "FAS Fonológico letra F aplicado durante 60 segundos"
}
```
**Response (HTTP 201 Created):**
```json
{
  "evaluation_subtest_id": "8f3b2a1c-9d8e-4a7b-b1c2-d3e4f5a6b7c8",
  "evaluation_id": "e4f5a6b7-c8d9-4e0f-a1b2-c3d4e5f6a7b8",
  "subtest_id": "d1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a",
  "duration_seconds": "60.000",
  "score": null,
  "status": "PENDING",
  "observations": "FAS Fonológico letra F aplicado durante 60 segundos",
  "active": true,
  "created_at": "2026-10-21T01:20:00.000000Z",
  "updated_at": "2026-10-21T01:20:00.000000Z"
}
```

### C. Error Estandarizado (HTTP 409 Conflict)
```json
{
  "error": {
    "code": "ENTITY_CONFLICT",
    "message": "Ya existe un paciente registrado con el código clínico 'PAC-2026-0042'.",
    "details": null
  }
}
```

---

## 11. Decisiones Técnicas y Supuestos

1. **Alineación con Diccionario de Datos v0.2:** Se adoptaron las 19 tablas oficiales, respetando identificadores primarios UUID, `date_of_birth`, `education_years`, `dialect_region`, `duration_seconds` en `evaluation_subtests`, y `active` para borrado lógico en todas las tablas.
2. **Supabase Auth y Usuarios:** La tabla `users` vincula `user_id` con `auth.users.id` de Supabase. El backend nunca almacena contraseñas en texto plano ni duplica sesiones; valida el JWT de Supabase Auth en cada petición y extrae el rol interno de la base de datos PostgreSQL.
3. **Manejo de Pooler PgBouncer:** Para compatibilidad con el pooler de Supabase en puerto 6543 (modo transaccional), se desactiva `statement_cache_size` en `asyncpg`, eliminando fallos en sentencias preparadas.
4. **Protección de Datos Sensibles:** Los formateadores de logs enmascaran tokens Bearer, contraseñas de conexión y credenciales de API.
5. **Aislamiento en Pruebas:** Los tests se ejecutan con SQLite en memoria (`aiosqlite`) mediante `StaticPool`, garantizando pruebas reproducibles en cualquier entorno sin conexión obligatoria a Internet ni exposición de datos clínicos.

---

## 12. Funcionalidades Pendientes para el Sprint 2

- **Gestión de Audio:** Carga de grabaciones de audio mediante URLs firmadas directas a Supabase Storage y registro de metadatos en tabla `audio`.
- **Pipeline de Transcripción ASR:** Recepción de transcripciones (`raw_text`) y módulo de revisión humana por parte del fonoaudiólogo (`corrected_text`).
- **Anotaciones y Características Lingüísticas:** Registro de eventos temporales en `annotations` y cálculo de métricas acústicas/léxicas en `linguistic_features`.
- **Servicio de Análisis IA:** Integración asíncrona mediante cola de tareas/worker para inferencia de modelos y persistencia estructurada en `ai_analysis` (JSONB).
- **Generación de Reportes:** Consolidación de observaciones del examinador y exportación de reportes clínicos en PDF.
