import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_evaluation_and_subtest_workflow(client: AsyncClient, professional_token: str):
    """
    Verifica el flujo completo de US-05 y US-06:
    - Crear paciente
    - Consultar protocolos y catálogos
    - Crear evaluación
    - Asociar subprueba con duration_seconds
    - Proteger contra asociaciones duplicadas (409)
    - Proteger contra subpruebas de protocolo ajeno (422)
    - Actualizar estado de evaluación
    """
    headers = {"Authorization": f"Bearer {professional_token}"}

    # 1. Crear Paciente
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-EVAL-01",
            "first_name": "Teresa",
            "last_name": "Campos",
            "date_of_birth": "1964-07-22",
            "primary_language": "Español",
            "bilingual": False,
        },
        headers=headers,
    )
    assert patient_res.status_code == 201
    patient_id = patient_res.json()["patient_id"]

    # 2. Consultar Protocolos y Subpruebas disponibles
    proto_res = await client.get("/api/v1/protocols", headers=headers)
    assert proto_res.status_code == 200
    protocols = proto_res.json()
    fas_proto = next(p for p in protocols if "FAS" in p["name"])
    protocol_id = fas_proto["protocol_id"]

    subtests_res = await client.get(f"/api/v1/protocols/{protocol_id}/subtests", headers=headers)
    assert subtests_res.status_code == 200
    subtests = subtests_res.json()
    assert len(subtests) >= 2
    subtest_f_id = subtests[0]["subtest_id"]

    # 3. Consultar Catálogos clínicos
    aphasia_res = await client.get("/api/v1/catalogs/aphasia-types", headers=headers)
    assert aphasia_res.status_code == 200
    aphasias = aphasia_res.json()
    broca_id = next(a["aphasia_type_id"] for a in aphasias if a["name"] == "Broca")

    severity_res = await client.get("/api/v1/catalogs/severity-levels", headers=headers)
    assert severity_res.status_code == 200
    severities = severity_res.json()
    mod_id = next(s["severity_level_id"] for s in severities if s["name"] == "Moderada")

    # 4. Crear Evaluación
    eval_payload = {
        "protocol_id": protocol_id,
        "aphasia_type_id": broca_id,
        "severity_level_id": mod_id,
        "evaluation_date": "2026-10-21T14:30:00Z",
        "status": "PENDING",
        "general_observations": "Paciente lúcida, colaboradora, manifiesta fatiga moderada",
    }
    eval_res = await client.post(
        f"/api/v1/patients/{patient_id}/evaluations",
        json=eval_payload,
        headers=headers,
    )
    assert eval_res.status_code == 201
    evaluation_data = eval_res.json()
    evaluation_id = evaluation_data["evaluation_id"]
    assert evaluation_data["status"] == "PENDING"

    # 5. Asociar Subprueba F con duración de 60 segundos
    sub_payload = {
        "subtest_id": subtest_f_id,
        "duration_seconds": 60.0,
        "observations": "Se completó la tarea de evocación de fonema F",
    }
    assoc_res = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/subtests",
        json=sub_payload,
        headers=headers,
    )
    assert assoc_res.status_code == 201
    assoc_data = assoc_res.json()
    assert assoc_data["duration_seconds"] == "60.000"

    # 6. Intentar asociar la misma subprueba nuevamente -> 409 Conflicto
    dup_res = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/subtests",
        json=sub_payload,
        headers=headers,
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "ENTITY_CONFLICT"

    # 7. Intentar asociar una subprueba que pertenece a OTRO protocolo -> 422
    alt_proto = next(p for p in protocols if "Alternativo" in p["name"])
    alt_subtests_res = await client.get(f"/api/v1/protocols/{alt_proto['protocol_id']}/subtests", headers=headers)
    foreign_subtest_id = alt_subtests_res.json()[0]["subtest_id"]

    foreign_res = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/subtests",
        json={"subtest_id": foreign_subtest_id},
        headers=headers,
    )
    assert foreign_res.status_code == 422
    assert foreign_res.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"

    # 8. Consultar detalle de la evaluación y verificar que incluya las subpruebas asociadas
    detail_res = await client.get(f"/api/v1/evaluations/{evaluation_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert len(detail_data["evaluation_subtests"]) == 1

    # 9. Actualizar estado de la evaluación (PATCH)
    patch_res = await client.patch(
        f"/api/v1/evaluations/{evaluation_id}",
        json={"status": "COMPLETED", "general_observations": "Evaluación completada con éxito"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "COMPLETED"
