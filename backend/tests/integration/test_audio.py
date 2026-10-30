import io
import struct
import uuid
import wave
from decimal import Decimal
import pytest
from httpx import AsyncClient


def create_synthetic_wav(duration_seconds: float = 2.0, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Genera un archivo de audio WAV sintético válido en memoria para pruebas de integración."""
    buffer = io.BytesIO()
    total_samples = int(duration_seconds * sample_rate * channels)
    with wave.open(buffer, "wb") as wav_out:
        wav_out.setnchannels(channels)
        wav_out.setsampwidth(2)  # 16 bits por muestra
        wav_out.setframerate(sample_rate)
        raw_samples = struct.pack(f"<{total_samples}h", *([0] * total_samples))
        wav_out.writeframes(raw_samples)
    return buffer.getvalue()


@pytest.fixture
async def sample_evaluation(client: AsyncClient, professional_token: str):
    """Crea un paciente, obtiene el protocolo FAS y genera una evaluación clínica para pruebas."""
    headers = {"Authorization": f"Bearer {professional_token}"}

    # 1. Crear Paciente
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": f"PAC-AUD-{uuid.uuid4().hex[:6].upper()}",
            "first_name": "Elena",
            "last_name": "Rojas",
            "date_of_birth": "1965-08-20",
            "primary_language": "Español",
            "bilingual": False,
        },
        headers=headers,
    )
    assert patient_res.status_code == 201
    patient_id = patient_res.json()["patient_id"]

    # 2. Obtener protocolo FAS
    proto_res = await client.get("/api/v1/protocols", headers=headers)
    assert proto_res.status_code == 200
    fas_proto = next(p for p in proto_res.json() if "FAS" in p["name"])
    protocol_id = fas_proto["protocol_id"]

    # 3. Crear Evaluación
    eval_res = await client.post(
        f"/api/v1/patients/{patient_id}/evaluations",
        json={
            "protocol_id": protocol_id,
            "evaluation_date": "2026-10-25T11:00:00Z",
            "status": "IN_PROGRESS",
        },
        headers=headers,
    )
    assert eval_res.status_code == 201
    return eval_res.json()


@pytest.mark.integration
async def test_upload_audio_recording_with_metadata_and_storage_reference(
    client: AsyncClient, professional_token: str, sample_evaluation: dict
):
    """
    Verifica los criterios de aceptación de la Historia de Usuario 10 (US-10):
    1. Grabar o cargar audio asociado a la evaluación.
    2. Audio guardado con metadatos técnicos (sample_rate, canales, tamaño, formato).
    3. Duración precisa extraída o reportada.
    4. Referencia persistida a Storage y URL firmada para reproducción.
    """
    headers = {"Authorization": f"Bearer {professional_token}"}
    evaluation_id = sample_evaluation["evaluation_id"]

    # Generar audio WAV de 2.5 segundos, 16kHz, mono
    wav_bytes = create_synthetic_wav(duration_seconds=2.5, sample_rate=16000, channels=1)

    files = {
        "file": ("fas_letra_f_paciente.wav", wav_bytes, "audio/wav")
    }

    # Cargar audio a la evaluación
    upload_res = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/audio",
        files=files,
        headers=headers,
    )
    assert upload_res.status_code == 201
    data = upload_res.json()

    assert "audio" in data
    audio = data["audio"]
    assert audio["audio_id"] is not None
    assert audio["evaluation_id"] == evaluation_id
    assert audio["file_name"] == "fas_letra_f_paciente.wav"
    assert audio["file_path"].startswith(f"evaluations/{evaluation_id}/")
    assert audio["file_format"] == "wav"
    assert audio["mime_type"] == "audio/wav"
    assert audio["file_size_bytes"] == len(wav_bytes)
    assert audio["sample_rate"] == 16000
    assert audio["channels"] == 1
    # Duración calculada por wave: 2.5 seg
    assert Decimal(str(audio["duration_seconds"])) == Decimal("2.5")
    assert audio["signed_url"] is not None
    assert audio["active"] is True


@pytest.mark.integration
async def test_list_and_get_audio_recording_details(
    client: AsyncClient, professional_token: str, sample_evaluation: dict
):
    """Verifica la consulta y listado de audios de una evaluación con URLs firmadas."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    evaluation_id = sample_evaluation["evaluation_id"]

    # Subir dos audios distintos
    wav1 = create_synthetic_wav(duration_seconds=1.0, sample_rate=16000, channels=1)
    wav2 = create_synthetic_wav(duration_seconds=3.0, sample_rate=44100, channels=2)

    await client.post(
        f"/api/v1/evaluations/{evaluation_id}/audio",
        files={"file": ("fonetica_f.wav", wav1, "audio/wav")},
        headers=headers,
    )
    res2 = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/audio",
        files={"file": ("fonetica_a.wav", wav2, "audio/wav")},
        headers=headers,
    )
    audio2_id = res2.json()["audio"]["audio_id"]

    # 1. Listar audios de la evaluación
    list_res = await client.get(f"/api/v1/evaluations/{evaluation_id}/audio", headers=headers)
    assert list_res.status_code == 200
    audios = list_res.json()
    assert len(audios) >= 2
    filenames = [a["file_name"] for a in audios]
    assert "fonetica_f.wav" in filenames
    assert "fonetica_a.wav" in filenames

    # 2. Consultar detalle de audio individual
    detail_res = await client.get(
        f"/api/v1/evaluations/{evaluation_id}/audio/{audio2_id}",
        headers=headers,
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["audio_id"] == audio2_id
    assert detail["sample_rate"] == 44100
    assert detail["channels"] == 2
    assert Decimal(str(detail["duration_seconds"])) == Decimal("3.0")
    assert "signed_url" in detail and detail["signed_url"]


@pytest.mark.integration
async def test_get_signed_playback_url(
    client: AsyncClient, professional_token: str, sample_evaluation: dict
):
    """Verifica la generación de una URL firmada dedicada con expiración configurable."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    evaluation_id = sample_evaluation["evaluation_id"]

    wav = create_synthetic_wav(duration_seconds=1.5)
    upload_res = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/audio",
        files={"file": ("prueba_signed.wav", wav, "audio/wav")},
        headers=headers,
    )
    audio_id = upload_res.json()["audio"]["audio_id"]

    # Solicitar URL firmada válida por 1800 segundos
    signed_res = await client.get(
        f"/api/v1/evaluations/{evaluation_id}/audio/{audio_id}/playback-url?expires_in_seconds=1800",
        headers=headers,
    )
    assert signed_res.status_code == 200
    signed_data = signed_res.json()
    assert signed_data["audio_id"] == audio_id
    assert signed_data["expires_in_seconds"] == 1800
    assert signed_data["signed_url"]


@pytest.mark.integration
async def test_upload_audio_with_explicit_duration_and_form_data(
    client: AsyncClient, professional_token: str, sample_evaluation: dict
):
    """Verifica que si el cliente reporta duración explícita (ej. grabador web MediaRecorder), se preserve."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    evaluation_id = sample_evaluation["evaluation_id"]

    wav = create_synthetic_wav(duration_seconds=1.0)

    upload_res = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/audio",
        files={"file": ("fas_letra_s.wav", wav, "audio/wav")},
        data={"duration_seconds": "60.0000"},
        headers=headers,
    )
    assert upload_res.status_code == 201
    audio = upload_res.json()["audio"]
    # Debe tomar la duración oficial de 60 segundos del formulario de grabación
    assert Decimal(str(audio["duration_seconds"])) == Decimal("60.0000")


@pytest.mark.integration
async def test_soft_delete_audio_recording(
    client: AsyncClient, professional_token: str, sample_evaluation: dict
):
    """Verifica que el borrado lógico desactiva el audio y no vuelve a figurar en las consultas activas."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    evaluation_id = sample_evaluation["evaluation_id"]

    wav = create_synthetic_wav(duration_seconds=1.0)
    upload_res = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/audio",
        files={"file": ("to_delete.wav", wav, "audio/wav")},
        headers=headers,
    )
    audio_id = upload_res.json()["audio"]["audio_id"]

    # Borrar lógicamente
    delete_res = await client.delete(
        f"/api/v1/evaluations/{evaluation_id}/audio/{audio_id}",
        headers=headers,
    )
    assert delete_res.status_code == 204

    # Al consultar detalle, debe retornar 404 (borrado lógico)
    get_res = await client.get(
        f"/api/v1/evaluations/{evaluation_id}/audio/{audio_id}",
        headers=headers,
    )
    assert get_res.status_code == 404


@pytest.mark.integration
async def test_upload_audio_to_nonexistent_evaluation_returns_404(
    client: AsyncClient, professional_token: str
):
    """Verifica que intentar asociar audio a una evaluación inexistente retorne 404."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    fake_eval_id = uuid.uuid4()
    wav = create_synthetic_wav(duration_seconds=1.0)

    res = await client.post(
        f"/api/v1/evaluations/{fake_eval_id}/audio",
        files={"file": ("fake.wav", wav, "audio/wav")},
        headers=headers,
    )
    assert res.status_code == 404


@pytest.mark.integration
async def test_upload_empty_audio_returns_422(
    client: AsyncClient, professional_token: str, sample_evaluation: dict
):
    """Verifica que intentar subir un archivo de audio vacío (0 bytes) retorne 422."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    evaluation_id = sample_evaluation["evaluation_id"]

    res = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/audio",
        files={"file": ("empty.wav", b"", "audio/wav")},
        headers=headers,
    )
    assert res.status_code == 422
