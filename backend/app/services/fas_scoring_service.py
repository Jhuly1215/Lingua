import unicodedata
import uuid
from decimal import Decimal
from typing import Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.db.models.evaluation import Evaluation, EvaluationSubtest
from app.db.models.pipeline import Response
from app.db.models.subtest import Subtest
from app.repositories.evaluation_repository import EvaluationRepository
from app.repositories.protocol_repository import ProtocolRepository
from app.repositories.response_repository import ResponseRepository
from app.schemas.response import (
    FASConditionResponsesCreate,
    FASConditionScoreResponse,
    FASErrorsBreakdown,
    FASErrorType,
    FASEvaluationSummaryResponse,
    ResponseResponse,
)


def normalize_word(word: Optional[str]) -> str:
    """
    Normaliza una palabra para detección clínica de perseveraciones:
    Convierte a minúsculas, elimina tildes/diacríticos y espacios en blanco.
    Ejemplo: 'Árbol ' -> 'arbol', 'flor' -> 'flor'.
    """
    if not word:
        return ""
    text = word.strip().lower()
    # Eliminar diacríticos (tildes)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


class FASScoringService:
    """
    Servicio de Puntuación FAS (Historia de Usuario 9).
    Gestiona el cálculo de respuestas válidas por condición, aplicando la regla clínica
    de que las repeticiones e intrusiones no suman al puntaje pero se conservan para investigación.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.eval_repo = EvaluationRepository(session)
        self.protocol_repo = ProtocolRepository(session)
        self.response_repo = ResponseRepository(session)

    async def record_condition_responses(
        self,
        evaluation_id: uuid.UUID,
        subtest_id: uuid.UUID,
        data: FASConditionResponsesCreate,
    ) -> FASConditionScoreResponse:
        """
        Registra y puntúa las respuestas emitidas en una condición de FAS (ej. F, A, S, Animales).
        Actualiza el puntaje oficial en evaluation_subtests.score con el conteo de válidas.
        """
        # 1. Validar existencia de la evaluación activa
        evaluation = await self.eval_repo.get_by_id(evaluation_id, only_active=True)
        if not evaluation:
            raise EntityNotFoundException("Evaluación", evaluation_id)

        # 2. Validar que la subprueba exista
        subtest = await self.protocol_repo.get_subtest_by_id(subtest_id)
        if not subtest:
            raise EntityNotFoundException("Subprueba", subtest_id)

        # 3. Validar pertenencia de la subprueba al protocolo de la evaluación
        if subtest.protocol_id != evaluation.protocol_id:
            raise ValidationException(
                f"La subprueba '{subtest.name}' no pertenece al protocolo asignado a esta evaluación."
            )

        # 4. Asegurar la asociación en evaluation_subtests
        eval_subtest = await self.eval_repo.get_subtest_association(evaluation_id, subtest_id)
        if not eval_subtest:
            # Si no estaba vinculada previamente, la vinculamos automáticamente
            eval_subtest = EvaluationSubtest(
                evaluation_subtest_id=uuid.uuid4(),
                evaluation_id=evaluation_id,
                subtest_id=subtest_id,
                duration_seconds=data.duration_seconds or Decimal("60.000"),
                status="IN_PROGRESS",
            )
            eval_subtest = await self.eval_repo.add_subtest_to_evaluation(eval_subtest)
        elif data.duration_seconds is not None:
            eval_subtest.duration_seconds = data.duration_seconds
            self.session.add(eval_subtest)

        # 5. Obtener o crear el Item clínico correspondiente a esta subprueba
        item = await self.response_repo.get_or_create_subtest_item(
            subtest_id=subtest_id,
            item_code=subtest.code,
            stimulus_text=subtest.name,
            instruction_text=subtest.instructions,
        )

        # 6. Procesar respuestas y aplicar reglas clínicas de puntuación
        seen_words: Set[str] = set()
        responses_to_create: List[Response] = []

        for idx, item_input in enumerate(data.responses):
            raw_text = item_input.response_text.strip() if item_input.response_text else ""
            norm = normalize_word(raw_text)

            is_valid = item_input.is_valid
            error_type = item_input.error_type.value if item_input.error_type else None

            # Detección clínica automática de perseveraciones / repeticiones
            if data.auto_detect_perseverations and norm:
                if norm in seen_words:
                    is_valid = False
                    error_type = FASErrorType.PERSEVERATION.value
                elif is_valid:
                    seen_words.add(norm)
                else:
                    # Registró un error explícito (ej. intrusión)
                    seen_words.add(norm)
            elif is_valid and norm:
                seen_words.add(norm)

            # Regla de puntuación clínica:
            # - Si es válida: score = 1.0000
            # - Si es error/repetición/intrusión: score = 0.0000 (NO suma al puntaje)
            score = Decimal("1.0000") if is_valid else Decimal("0.0000")
            if not is_valid and not error_type:
                error_type = FASErrorType.OTHER.value

            resp_obj = Response(
                response_id=uuid.uuid4(),
                evaluation_id=evaluation_id,
                item_id=item.item_id,
                response_text=raw_text or None,
                score=score,
                is_valid=is_valid,
                error_type=error_type,
                response_time_ms=item_input.response_time_ms,
                response_order=item_input.response_order or (idx + 1),
                start_time_ms=item_input.start_time_ms,
                end_time_ms=item_input.end_time_ms,
                examiner_observation=item_input.examiner_observation,
            )
            responses_to_create.append(resp_obj)

        saved_responses = await self.response_repo.bulk_create(responses_to_create)

        # 7. Calcular conteo de respuestas válidas y desglose de errores
        valid_count = sum(1 for r in saved_responses if r.is_valid)
        errors_breakdown = self._calculate_errors_breakdown(saved_responses)

        # 8. Actualizar el puntaje en evaluation_subtests
        eval_subtest.score = Decimal(valid_count)
        eval_subtest.status = "COMPLETED"
        self.session.add(eval_subtest)
        await self.session.flush()
        await self.session.refresh(eval_subtest)

        return FASConditionScoreResponse(
            evaluation_id=evaluation_id,
            subtest_id=subtest_id,
            subtest_name=subtest.name,
            subtest_code=subtest.code,
            duration_seconds=eval_subtest.duration_seconds,
            total_responses=len(saved_responses),
            valid_responses_count=valid_count,
            error_responses_count=len(saved_responses) - valid_count,
            errors_breakdown=errors_breakdown,
            responses=[ResponseResponse.model_validate(r) for r in saved_responses],
        )

    async def get_condition_score(
        self,
        evaluation_id: uuid.UUID,
        subtest_id: uuid.UUID,
    ) -> FASConditionScoreResponse:
        """
        Recupera el conteo de respuestas válidas y el desglose de errores de una condición específica.
        Cumple la historia de usuario US-09.
        """
        evaluation = await self.eval_repo.get_by_id(evaluation_id, only_active=True)
        if not evaluation:
            raise EntityNotFoundException("Evaluación", evaluation_id)

        subtest = await self.protocol_repo.get_subtest_by_id(subtest_id)
        if not subtest:
            raise EntityNotFoundException("Subprueba", subtest_id)

        eval_subtest = await self.eval_repo.get_subtest_association(evaluation_id, subtest_id)
        duration_seconds = eval_subtest.duration_seconds if eval_subtest else None

        responses = await self.response_repo.list_by_evaluation_and_subtest(evaluation_id, subtest_id)
        valid_count = sum(1 for r in responses if r.is_valid)
        errors_breakdown = self._calculate_errors_breakdown(responses)

        return FASConditionScoreResponse(
            evaluation_id=evaluation_id,
            subtest_id=subtest_id,
            subtest_name=subtest.name,
            subtest_code=subtest.code,
            duration_seconds=duration_seconds,
            total_responses=len(responses),
            valid_responses_count=valid_count,
            error_responses_count=len(responses) - valid_count,
            errors_breakdown=errors_breakdown,
            responses=[ResponseResponse.model_validate(r) for r in responses],
        )

    async def get_evaluation_fas_summary(
        self,
        evaluation_id: uuid.UUID,
    ) -> FASEvaluationSummaryResponse:
        """
        Calcula el resumen consolidado de la prueba FAS completa para la evaluación:
        - Subtotal fonético (F + A + S)
        - Subtotal semántico (Animales, etc.)
        - Puntuación total general de la prueba
        - Desglose consolidado de perseveraciones e intrusiones.
        """
        evaluation = await self.eval_repo.get_by_id_detailed(evaluation_id)
        if not evaluation:
            raise EntityNotFoundException("Evaluación", evaluation_id)

        patient = evaluation.patient
        patient_code = patient.patient_code if patient else "UNKNOWN"

        eval_subtests = await self.eval_repo.list_evaluation_subtests(evaluation_id)

        condition_scores: List[FASConditionScoreResponse] = []
        phonetic_score = 0
        semantic_score = 0
        all_responses: List[Response] = []

        for es in eval_subtests:
            cond_score = await self.get_condition_score(evaluation_id, es.subtest_id)
            condition_scores.append(cond_score)

            sub_code = (cond_score.subtest_code or "").upper()
            sub_name = cond_score.subtest_name.upper()

            # Clasificación clínica: semántica vs fonológica
            is_semantic = (
                "SEMANT" in sub_name
                or "SEMANT" in sub_code
                or "ANIMAL" in sub_name
                or "ANIMAL" in sub_code
                or "COCINA" in sub_name
                or "PAIS" in sub_name
            )

            if is_semantic:
                semantic_score += cond_score.valid_responses_count
            else:
                phonetic_score += cond_score.valid_responses_count

        all_responses = await self.response_repo.list_by_evaluation(evaluation_id)
        consolidated_errors = self._calculate_errors_breakdown(all_responses)
        total_valid = sum(c.valid_responses_count for c in condition_scores)

        return FASEvaluationSummaryResponse(
            evaluation_id=evaluation_id,
            patient_id=evaluation.patient_id,
            patient_code=patient_code,
            phonetic_score=phonetic_score,
            semantic_score=semantic_score,
            total_fas_score=total_valid,
            total_responses=len(all_responses),
            total_errors=len(all_responses) - total_valid,
            errors_breakdown=consolidated_errors,
            conditions=condition_scores,
        )

    async def list_evaluation_responses(
        self,
        evaluation_id: uuid.UUID,
    ) -> List[ResponseResponse]:
        """Lista todas las respuestas emitidas en una evaluación."""
        evaluation = await self.eval_repo.get_by_id(evaluation_id, only_active=True)
        if not evaluation:
            raise EntityNotFoundException("Evaluación", evaluation_id)

        responses = await self.response_repo.list_by_evaluation(evaluation_id)
        return [ResponseResponse.model_validate(r) for r in responses]

    def _calculate_errors_breakdown(self, responses: List[Response]) -> FASErrorsBreakdown:
        """Calcula el conteo de cada categoría de error clínico."""
        breakdown: Dict[str, int] = {
            "perseverations": 0,
            "phonetic_intrusions": 0,
            "semantic_intrusions": 0,
            "proper_nouns_not_allowed": 0,
            "neologisms_paraphasias": 0,
            "prolonged_pauses": 0,
            "other_errors": 0,
        }

        for r in responses:
            if not r.is_valid:
                etype = (r.error_type or "").upper()
                if etype == FASErrorType.PERSEVERATION.value:
                    breakdown["perseverations"] += 1
                elif etype == FASErrorType.PHONETIC_INTRUSION.value:
                    breakdown["phonetic_intrusions"] += 1
                elif etype == FASErrorType.SEMANTIC_INTRUSION.value:
                    breakdown["semantic_intrusions"] += 1
                elif etype == FASErrorType.PROPER_NOUN_NOT_ALLOWED.value:
                    breakdown["proper_nouns_not_allowed"] += 1
                elif etype == FASErrorType.NEOLOGISM_PARAPHASIA.value:
                    breakdown["neologisms_paraphasias"] += 1
                elif etype == FASErrorType.PROLONGED_PAUSE.value:
                    breakdown["prolonged_pauses"] += 1
                else:
                    breakdown["other_errors"] += 1

        total_errs = sum(breakdown.values())
        return FASErrorsBreakdown(
            perseverations=breakdown["perseverations"],
            phonetic_intrusions=breakdown["phonetic_intrusions"],
            semantic_intrusions=breakdown["semantic_intrusions"],
            proper_nouns_not_allowed=breakdown["proper_nouns_not_allowed"],
            neologisms_paraphasias=breakdown["neologisms_paraphasias"],
            prolonged_pauses=breakdown["prolonged_pauses"],
            other_errors=breakdown["other_errors"],
            total_errors=total_errs,
        )
