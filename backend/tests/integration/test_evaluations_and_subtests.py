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
    - Listar evaluaciones del paciente
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

    # Listar evaluaciones del paciente
    patient_evals_res = await client.get(
        f"/api/v1/patients/{patient_id}/evaluations",
        headers=headers,
    )
    assert patient_evals_res.status_code == 200
    assert len(patient_evals_res.json()) == 1

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


@pytest.mark.integration
async def test_evaluation_aphasia_null_mixta_no_clasificada(client: AsyncClient, professional_token: str):
    """
    Verifica que:
    1. Una evaluación se pueda crear sin clasificar la afasia (aphasia_type_id = None).
    2. Se pueda clasificar explícitamente como 'Mixta'.
    3. Se pueda clasificar explícitamente como 'No clasificada'.
    4. Se distinga claramente entre clasificación ausente (NULL) y explícita.
    """
    headers = {"Authorization": f"Bearer {professional_token}"}

    # 1. Crear Paciente
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-APH-CAT-01",
            "first_name": "Manuel",
            "last_name": "Ortiz",
            "date_of_birth": "1958-10-05",
        },
        headers=headers,
    )
    assert patient_res.status_code == 201
    patient_id = patient_res.json()["patient_id"]

    # 2. Obtener IDs de protocolo y catálogos
    proto_res = await client.get("/api/v1/protocols", headers=headers)
    protocol_id = proto_res.json()[0]["protocol_id"]

    aphasia_res = await client.get("/api/v1/catalogs/aphasia-types", headers=headers)
    aphasias = aphasia_res.json()
    mixta = next(a for a in aphasias if a["name"] == "Mixta")
    no_clasificada = next(a for a in aphasias if a["name"] == "No clasificada")

    # Escenario A: Evaluación con afasia nula (sin clasificación inicial)
    eval_null_res = await client.post(
        f"/api/v1/patients/{patient_id}/evaluations",
        json={
            "protocol_id": protocol_id,
            "aphasia_type_id": None,
            "evaluation_date": "2026-10-22T10:00:00Z",
            "general_observations": "Evaluación preliminar sin clasificación diagnóstica",
        },
        headers=headers,
    )
    assert eval_null_res.status_code == 201
    eval_null_data = eval_null_res.json()
    assert eval_null_data["aphasia_type_id"] is None

    detail_null_res = await client.get(f"/api/v1/evaluations/{eval_null_data['evaluation_id']}", headers=headers)
    assert detail_null_res.status_code == 200
    assert detail_null_res.json()["aphasia_type"] is None

    # Escenario B: Evaluación clasificada como 'Mixta'
    eval_mixta_res = await client.post(
        f"/api/v1/patients/{patient_id}/evaluations",
        json={
            "protocol_id": protocol_id,
            "aphasia_type_id": mixta["aphasia_type_id"],
            "evaluation_date": "2026-10-22T11:00:00Z",
            "general_observations": "Presenta características de fluencia y comprensión alteradas",
        },
        headers=headers,
    )
    assert eval_mixta_res.status_code == 201
    eval_mixta_data = eval_mixta_res.json()
    assert eval_mixta_data["aphasia_type_id"] == mixta["aphasia_type_id"]

    detail_mixta_res = await client.get(f"/api/v1/evaluations/{eval_mixta_data['evaluation_id']}", headers=headers)
    assert detail_mixta_res.status_code == 200
    assert detail_mixta_res.json()["aphasia_type"]["name"] == "Mixta"

    # Escenario C: Evaluación clasificada explícitamente como 'No clasificada'
    eval_noclas_res = await client.post(
        f"/api/v1/patients/{patient_id}/evaluations",
        json={
            "protocol_id": protocol_id,
            "aphasia_type_id": no_clasificada["aphasia_type_id"],
            "evaluation_date": "2026-10-22T12:00:00Z",
            "general_observations": "Cuadro agudo indeterminado",
        },
        headers=headers,
    )
    assert eval_noclas_res.status_code == 201
    eval_noclas_data = eval_noclas_res.json()
    assert eval_noclas_data["aphasia_type_id"] == no_clasificada["aphasia_type_id"]

    detail_noclas_res = await client.get(f"/api/v1/evaluations/{eval_noclas_data['evaluation_id']}", headers=headers)
    assert detail_noclas_res.status_code == 200
    assert detail_noclas_res.json()["aphasia_type"]["name"] == "No clasificada"


@pytest.mark.integration
async def test_evaluation_reject_nonexistent_aphasia_type(client: AsyncClient, professional_token: str):
    """Verifica que asociar un identificador de tipo de afasia inexistente retorne 404."""
    headers = {"Authorization": f"Bearer {professional_token}"}

    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-APH-ERR-01",
            "first_name": "Beatriz",
            "last_name": "Nuñez",
            "date_of_birth": "1970-01-10",
        },
        headers=headers,
    )
    patient_id = patient_res.json()["patient_id"]

    proto_res = await client.get("/api/v1/protocols", headers=headers)
    protocol_id = proto_res.json()[0]["protocol_id"]

    fake_aphasia_id = uuid.uuid4()

    # Creación con afasia inexistente -> 404
    res = await client.post(
        f"/api/v1/patients/{patient_id}/evaluations",
        json={
            "protocol_id": protocol_id,
            "aphasia_type_id": str(fake_aphasia_id),
            "evaluation_date": "2026-10-22T14:00:00Z",
        },
        headers=headers,
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "ENTITY_NOT_FOUND"


@pytest.mark.integration
async def test_evaluation_reject_cross_patient_clinical_event(client: AsyncClient, professional_token: str):
    """
    Verifica que no se pueda vincular un evento clínico perteneciente a otro paciente
    (integridad referencial de negocio).
    """
    headers = {"Authorization": f"Bearer {professional_token}"}

    # Crear Paciente A y su evento
    p_a_res = await client.post(
        "/api/v1/patients",
        json={"patient_code": "PAC-CROSS-A", "first_name": "A", "last_name": "A", "date_of_birth": "1980-01-01"},
        headers=headers,
    )
    patient_a_id = p_a_res.json()["patient_id"]

    evt_res = await client.post(
        f"/api/v1/patients/{patient_a_id}/clinical-events",
        json={"event_type": "ACV", "event_date": "2026-05-01"},
        headers=headers,
    )
    event_a_id = evt_res.json()["clinical_event_id"]

    # Crear Paciente B
    p_b_res = await client.post(
        "/api/v1/patients",
        json={"patient_code": "PAC-CROSS-B", "first_name": "B", "last_name": "B", "date_of_birth": "1985-01-01"},
        headers=headers,
    )
    patient_b_id = p_b_res.json()["patient_id"]

    proto_res = await client.get("/api/v1/protocols", headers=headers)
    protocol_id = proto_res.json()[0]["protocol_id"]

    # Intentar crear evaluación para Paciente B asociando el evento del Paciente A -> 422
    eval_res = await client.post(
        f"/api/v1/patients/{patient_b_id}/evaluations",
        json={
            "protocol_id": protocol_id,
            "clinical_event_id": event_a_id,
            "evaluation_date": "2026-10-22T15:00:00Z",
        },
        headers=headers,
    )
    assert eval_res.status_code == 422
