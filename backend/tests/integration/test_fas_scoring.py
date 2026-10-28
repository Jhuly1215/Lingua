import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_fas_condition_scoring_and_error_preservation(client: AsyncClient, professional_token: str):
    """
    Verifica los criterios de aceptación de la Historia de Usuario 9 (US-09):
    1. Obtener el conteo de respuestas válidas por condición (score oficial).
    2. Las repeticiones e intrusiones NO suman al puntaje, pero se conservan íntegramente
       como eventos relevantes con su tipo de error y marcas de tiempo.
    3. Se actualiza el campo score en evaluation_subtests.
    """
    headers = {"Authorization": f"Bearer {professional_token}"}

    # 1. Crear Paciente
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-FAS-001",
            "first_name": "Carlos",
            "last_name": "Mendoza",
            "date_of_birth": "1960-05-12",
            "primary_language": "Español",
            "bilingual": False,
        },
        headers=headers,
    )
    assert patient_res.status_code == 201
    patient_id = patient_res.json()["patient_id"]

    # 2. Consultar protocolo FAS y subpruebas
    proto_res = await client.get("/api/v1/protocols", headers=headers)
    assert proto_res.status_code == 200
    fas_proto = next(p for p in proto_res.json() if "FAS" in p["name"])
    protocol_id = fas_proto["protocol_id"]

    subtests_res = await client.get(f"/api/v1/protocols/{protocol_id}/subtests", headers=headers)
    subtests = subtests_res.json()
    subtest_f = next(s for s in subtests if "F" in s["name"] or s.get("code") == "FAS_F")
    subtest_f_id = subtest_f["subtest_id"]

    # 3. Crear Evaluación
    eval_res = await client.post(
        f"/api/v1/patients/{patient_id}/evaluations",
        json={
            "protocol_id": protocol_id,
            "evaluation_date": "2026-10-22T10:00:00Z",
            "status": "IN_PROGRESS",
        },
        headers=headers,
    )
    assert eval_res.status_code == 201
    evaluation_id = eval_res.json()["evaluation_id"]

    # 4. Enviar respuestas de la condición F:
    # - 4 válidas: "foca", "flor", "fuego", "farol"
    # - 2 repeticiones (perseveraciones): "foca" nuevamente, "flor" nuevamente
    # - 1 intrusión fonética: "barco" (no empieza con F)
    # - 1 nombre propio no permitido: "Fernando"
    # - 1 neologismo / parafasia: "fripio"
    responses_payload = {
        "duration_seconds": 60.0,
        "auto_detect_perseverations": True,
        "responses": [
            {
                "response_text": "foca",
                "response_order": 1,
                "is_valid": True,
                "start_time_ms": 1500,
                "end_time_ms": 2200,
            },
            {
                "response_text": "flor",
                "response_order": 2,
                "is_valid": True,
                "start_time_ms": 4000,
                "end_time_ms": 4700,
            },
            {
                "response_text": "foca",  # Repetición -> debe detectarse como PERSEVERATION
                "response_order": 3,
                "is_valid": True,  # auto_detect la cambiará a False
                "start_time_ms": 8000,
                "end_time_ms": 8600,
            },
            {
                "response_text": "barco",  # Intrusión fonética
                "response_order": 4,
                "is_valid": False,
                "error_type": "PHONETIC_INTRUSION",
                "start_time_ms": 12000,
                "end_time_ms": 12800,
            },
            {
                "response_text": "fuego",
                "response_order": 5,
                "is_valid": True,
                "start_time_ms": 18000,
                "end_time_ms": 18900,
            },
            {
                "response_text": "Fernando",  # Nombre propio no permitido
                "response_order": 6,
                "is_valid": False,
                "error_type": "PROPER_NOUN_NOT_ALLOWED",
                "start_time_ms": 24000,
                "end_time_ms": 25100,
            },
            {
                "response_text": "flor",  # Segunda repetición
                "response_order": 7,
                "is_valid": True,
                "start_time_ms": 32000,
                "end_time_ms": 32600,
            },
            {
                "response_text": "fripio",  # Neologismo / parafasia
                "response_order": 8,
                "is_valid": False,
                "error_type": "NEOLOGISM_PARAPHASIA",
                "start_time_ms": 40000,
                "end_time_ms": 41200,
            },
            {
                "response_text": "farol",
                "response_order": 9,
                "is_valid": True,
                "start_time_ms": 50000,
                "end_time_ms": 50800,
            },
        ],
    }

    post_resp_res = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/subtests/{subtest_f_id}/responses",
        json=responses_payload,
        headers=headers,
    )
    assert post_resp_res.status_code == 201
    data = post_resp_res.json()

    # Comprobación de criterios de aceptación de US-09:
    # Total de respuestas emitidas: 9
    assert data["total_responses"] == 9
    # Solo las respuestas válidas suman al puntaje oficial: 4 ("foca", "flor", "fuego", "farol")
    assert data["valid_responses_count"] == 4
    # Las repeticiones e intrusiones NO suman al puntaje (5 errores):
    assert data["error_responses_count"] == 5

    # Desglose de errores conservados:
    breakdown = data["errors_breakdown"]
    assert breakdown["perseverations"] == 2
    assert breakdown["phonetic_intrusions"] == 1
    assert breakdown["proper_nouns_not_allowed"] == 1
    assert breakdown["neologisms_paraphasias"] == 1
    assert breakdown["total_errors"] == 5

    # Verificar que las 9 respuestas se conservan en la base de datos con su clasificación
    assert len(data["responses"]) == 9
    valids = [r for r in data["responses"] if r["is_valid"] is True]
    invalids = [r for r in data["responses"] if r["is_valid"] is False]
    assert len(valids) == 4
    assert len(invalids) == 5

    for v in valids:
        assert float(v["score"]) == 1.0
        assert v["error_type"] is None

    for inv in invalids:
        assert float(inv["score"]) == 0.0
        assert inv["error_type"] is not None

    # 5. Consultar endpoint de puntuación por separado (GET .../score)
    get_score_res = await client.get(
        f"/api/v1/evaluations/{evaluation_id}/subtests/{subtest_f_id}/score",
        headers=headers,
    )
    assert get_score_res.status_code == 200
    score_data = get_score_res.json()
    assert score_data["valid_responses_count"] == 4
    assert score_data["error_responses_count"] == 5
    assert score_data["errors_breakdown"]["perseverations"] == 2

    # 6. Verificar que evaluation_subtests se actualizó con el score oficial
    eval_detail = await client.get(f"/api/v1/evaluations/{evaluation_id}", headers=headers)
    assert eval_detail.status_code == 200
    subtest_assocs = eval_detail.json()["evaluation_subtests"]
    f_assoc = next(a for a in subtest_assocs if a["subtest_id"] == subtest_f_id)
    assert float(f_assoc["score"]) == 4.0
    assert f_assoc["status"] == "COMPLETED"


@pytest.mark.integration
async def test_fas_evaluation_summary_score(client: AsyncClient, professional_token: str):
    """
    Verifica el resumen consolidado de la prueba FAS completa para la evaluación:
    subtotales fonéticos (F + A + S), subtotales semánticos y total acumulado.
    """
    headers = {"Authorization": f"Bearer {professional_token}"}

    # 1. Crear Paciente y Evaluación
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-FAS-SUMMARY",
            "first_name": "Lucía",
            "last_name": "Morales",
            "date_of_birth": "1955-11-03",
            "primary_language": "Español",
            "bilingual": False,
        },
        headers=headers,
    )
    patient_id = patient_res.json()["patient_id"]

    proto_res = await client.get("/api/v1/protocols", headers=headers)
    fas_proto = next(p for p in proto_res.json() if "FAS" in p["name"])
    protocol_id = fas_proto["protocol_id"]

    subtests_res = await client.get(f"/api/v1/protocols/{protocol_id}/subtests", headers=headers)
    subtests = subtests_res.json()
    sub_f = next(s for s in subtests if "F" in s["name"] or s.get("code") == "FAS_F")
    sub_animals = next(s for s in subtests if "Animales" in s["name"] or s.get("code") == "FAS_ANIMALS")

    eval_res = await client.post(
        f"/api/v1/patients/{patient_id}/evaluations",
        json={"protocol_id": protocol_id, "evaluation_date": "2026-10-22T11:00:00Z"},
        headers=headers,
    )
    evaluation_id = eval_res.json()["evaluation_id"]

    # 2. Registrar condición F (3 válidas, 1 intrusión)
    await client.post(
        f"/api/v1/evaluations/{evaluation_id}/subtests/{sub_f['subtest_id']}/responses",
        json={
            "responses": [
                {"response_text": "familia", "is_valid": True},
                {"response_text": "fresca", "is_valid": True},
                {"response_text": "frijol", "is_valid": True},
                {"response_text": "zapato", "is_valid": False, "error_type": "PHONETIC_INTRUSION"},
            ]
        },
        headers=headers,
    )

    # 3. Registrar condición Animales (4 válidas, 1 perseveración)
    await client.post(
        f"/api/v1/evaluations/{evaluation_id}/subtests/{sub_animals['subtest_id']}/responses",
        json={
            "auto_detect_perseverations": True,
            "responses": [
                {"response_text": "perro", "is_valid": True},
                {"response_text": "gato", "is_valid": True},
                {"response_text": "loro", "is_valid": True},
                {"response_text": "perro", "is_valid": True},  # Repetición automática
                {"response_text": "caballo", "is_valid": True},
            ]
        },
        headers=headers,
    )

    # 4. Consultar resumen general FAS de la evaluación
    summary_res = await client.get(f"/api/v1/evaluations/{evaluation_id}/fas-score", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()

    assert summary["evaluation_id"] == evaluation_id
    assert summary["patient_code"] == "PAC-FAS-SUMMARY"
    # Fonético: 3 válidas en F
    assert summary["phonetic_score"] == 3
    # Semántico: 4 válidas en Animales
    assert summary["semantic_score"] == 4
    # Total FAS: 3 + 4 = 7
    assert summary["total_fas_score"] == 7
    assert summary["total_responses"] == 9
    assert summary["total_errors"] == 2
    assert summary["errors_breakdown"]["phonetic_intrusions"] == 1
    assert summary["errors_breakdown"]["perseverations"] == 1
