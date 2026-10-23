from fastapi import APIRouter

from app.api.v1.endpoints import auth, evaluations, health, patients, protocols

api_router = APIRouter()

# Health endpoints (públicos para monitorización y liveness probes)
api_router.include_router(health.router)

# Perfil y sesión de usuario
api_router.include_router(auth.router)

# Gestión clínica de pacientes (US-02, US-03, US-04, US-05)
api_router.include_router(patients.router)

# Evaluaciones y subpruebas (US-05, US-06)
api_router.include_router(evaluations.router)

# Protocolos y catálogos de afasia/severidad (US-06)
api_router.include_router(protocols.router)
