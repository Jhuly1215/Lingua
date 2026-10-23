"""
Script idempotente para poblar catálogos iniciales de LINGUA:
- Roles del sistema (admin, professional, researcher)
- Tipos de afasia (Broca, Wernicke, Conducción, Mixta, No clasificada, etc.)
- Niveles de severidad clínica
- Protocolo FAS y sus subpruebas fonológicas y semánticas
"""
import asyncio
import logging
import os
import sys
import uuid
from decimal import Decimal

# Asegurar que el directorio raíz de backend esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import setup_logging
from app.db.models.catalogs import AphasiaType, SeverityLevel
from app.db.models.protocol import Protocol
from app.db.models.role import Role
from app.db.models.subtest import Subtest
from app.db.session import AsyncSessionLocal

logger = setup_logging("INFO")

ROLES_DATA = [
    {
        "name": "admin",
        "description": "Administrador de la plataforma LINGUA con gestión técnica y de usuarios.",
    },
    {
        "name": "professional",
        "description": "Profesional fonoaudiólogo/neurólogo habilitado para administrar evaluaciones clínicas.",
    },
    {
        "name": "researcher",
        "description": "Investigador autorizado para análisis lingüístico y reutilización de datos consentidos.",
    },
]

APHASIA_TYPES_DATA = [
    {"name": "Broca", "description": "Afasia no fluente con afectación predominante de la expresión y agramatismo."},
    {"name": "Wernicke", "description": "Afasia fluente con parafasias y severo compromiso de la comprensión auditiva."},
    {"name": "Conducción", "description": "Compromiso selectivo y severo de la repetición con lenguaje espontáneo relativamente fluente."},
    {"name": "Global", "description": "Afectación masiva de todas las modalidades del lenguaje (expresión, comprensión, repetición)."},
    {"name": "Anómica", "description": "Dificultad aislada o predominante para evocar palabras (anomia) con sintaxis y comprensión preservadas."},
    {"name": "Transcortical Motora", "description": "Similar a Broca pero con preservación notable de la capacidad de repetición."},
    {"name": "Transcortical Sensorial", "description": "Similar a Wernicke con repetición conservada y ecolalia."},
    {"name": "Transcortical Mixta", "description": "Aislamiento del área del lenguaje con severa afectación pero preservación de repetición."},
    {"name": "Mixta", "description": "Cuadro heterogéneo que combina características motoras y sensoriales sin encajar en un tipo puro."},
    {"name": "No clasificada", "description": "Estado transitorio o cuadro no categorizable en la evaluación inicial."},
]

SEVERITY_LEVELS_DATA = [
    {
        "name": "Normal / Sin afasia",
        "description": "Rendimiento lingüístico dentro de límites normativos esperados.",
        "min_score": Decimal("5.0"),
        "max_score": Decimal("5.0"),
    },
    {
        "name": "Leve",
        "description": "Dificultades lingüísticas sutiles, comunicación funcional independiente conservada.",
        "min_score": Decimal("4.0"),
        "max_score": Decimal("4.9"),
    },
    {
        "name": "Moderada",
        "description": "Afectación comunicativa evidente; requiere apoyos o repetición para intercambio conversacional.",
        "min_score": Decimal("2.5"),
        "max_score": Decimal("3.9"),
    },
    {
        "name": "Severa",
        "description": "Comunicación espontánea muy limitada; transmisión de mensajes fragmentaria o dependiente del examinador.",
        "min_score": Decimal("1.0"),
        "max_score": Decimal("2.4"),
    },
    {
        "name": "Profunda",
        "description": "Ausencia casi total de lenguaje funcional expresivo y/o receptivo.",
        "min_score": Decimal("0.0"),
        "max_score": Decimal("0.9"),
    },
]

FAS_PROTOCOL_DATA = {
    "name": "Fluencia Verbal FAS (Fonológica y Semántica)",
    "version": "1.0",
    "description": "Protocolo neuropsicológico clásico para evaluar fluidez verbal por clave fonológica (F, A, S) y semántica (Animales).",
    "subtests": [
        {
            "name": "FAS Fonológico — Letra F",
            "code": "FAS_PHONEMIC_F",
            "order_number": 1,
            "description": "Evocación oral de la mayor cantidad de palabras que inicien con la letra 'F' durante el intervalo aplicado.",
            "instructions": "Diga todas las palabras que pueda que empiecen con la letra F, evitando nombres propios o números.",
        },
        {
            "name": "FAS Fonológico — Letra A",
            "code": "FAS_PHONEMIC_A",
            "order_number": 2,
            "description": "Evocación oral de palabras que inicien con la letra 'A'.",
            "instructions": "Diga todas las palabras que pueda que empiecen con la letra A.",
        },
        {
            "name": "FAS Fonológico — Letra S",
            "code": "FAS_PHONEMIC_S",
            "order_number": 3,
            "description": "Evocación oral de palabras que inicien con la letra 'S'.",
            "instructions": "Diga todas las palabras que pueda que empiecen con la letra S.",
        },
        {
            "name": "FAS Semántico — Animales",
            "code": "FAS_SEMANTIC_ANIMALS",
            "order_number": 4,
            "description": "Evocación oral de la mayor cantidad de animales.",
            "instructions": "Diga todos los animales que recuerde en el tiempo establecido.",
        },
    ],
}


async def seed_all(session: AsyncSession) -> None:
    """Inserta catálogos iniciales de forma idempotente."""
    logger.info("Verificando catálogo de roles...")
    for role_item in ROLES_DATA:
        stmt = select(Role).where(Role.name == role_item["name"])
        existing = (await session.execute(stmt)).scalars().first()
        if not existing:
            role = Role(
                role_id=uuid.uuid4(),
                name=role_item["name"],
                description=role_item["description"],
            )
            session.add(role)
            logger.info("Rol '%s' insertado.", role_item["name"])

    logger.info("Verificando catálogo de tipos de afasia...")
    for aphasia_item in APHASIA_TYPES_DATA:
        stmt = select(AphasiaType).where(AphasiaType.name == aphasia_item["name"])
        existing = (await session.execute(stmt)).scalars().first()
        if not existing:
            atype = AphasiaType(
                aphasia_type_id=uuid.uuid4(),
                name=aphasia_item["name"],
                description=aphasia_item["description"],
            )
            session.add(atype)
            logger.info("Tipo de afasia '%s' insertado.", aphasia_item["name"])

    logger.info("Verificando catálogo de niveles de severidad...")
    for sev_item in SEVERITY_LEVELS_DATA:
        stmt = select(SeverityLevel).where(SeverityLevel.name == sev_item["name"])
        existing = (await session.execute(stmt)).scalars().first()
        if not existing:
            slevel = SeverityLevel(
                severity_level_id=uuid.uuid4(),
                name=sev_item["name"],
                description=sev_item["description"],
                min_score=sev_item.get("min_score"),
                max_score=sev_item.get("max_score"),
            )
            session.add(slevel)
            logger.info("Nivel de severidad '%s' insertado.", sev_item["name"])

    logger.info("Verificando protocolo FAS...")
    stmt = select(Protocol).where(Protocol.name == FAS_PROTOCOL_DATA["name"])
    existing_proto = (await session.execute(stmt)).scalars().first()
    if not existing_proto:
        proto = Protocol(
            protocol_id=uuid.uuid4(),
            name=FAS_PROTOCOL_DATA["name"],
            version=FAS_PROTOCOL_DATA["version"],
            description=FAS_PROTOCOL_DATA["description"],
        )
        session.add(proto)
        await session.flush()
        logger.info("Protocolo FAS insertado.")

        for sub_item in FAS_PROTOCOL_DATA["subtests"]:
            sub = Subtest(
                subtest_id=uuid.uuid4(),
                protocol_id=proto.protocol_id,
                name=sub_item["name"],
                code=sub_item["code"],
                order_number=sub_item["order_number"],
                description=sub_item["description"],
                instructions=sub_item["instructions"],
            )
            session.add(sub)
            logger.info("Subprueba '%s' asociada a FAS.", sub_item["name"])
    else:
        logger.info("Protocolo FAS ya existe en la base de datos.")

    await session.commit()
    logger.info("Población de catálogos completada con éxito.")


async def main():
    async with AsyncSessionLocal() as session:
        await seed_all(session)


if __name__ == "__main__":
    asyncio.run(main())
