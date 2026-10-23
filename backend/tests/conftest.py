import asyncio
import uuid
from decimal import Decimal
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import create_mock_access_token
from app.db.base import Base
from app.db.models.catalogs import AphasiaType, SeverityLevel
from app.db.models.protocol import Protocol
from app.db.models.role import Role
from app.db.models.subtest import Subtest
from app.db.models.user import User
from app.dependencies.database import get_db
from app.main import app

# Base de datos SQLite en memoria compartida mediante StaticPool
test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def setup_test_database():
    """Crea el esquema relacional en SQLite en memoria antes de cada prueba y limpia después."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_test_database) -> AsyncGenerator[AsyncSession, None]:
    """Sesión de base de datos asíncrona para pruebas."""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def seed_data(db_session: AsyncSession):
    """Inserta roles, catálogos, protocolos y usuarios clínicos iniciales para tests."""
    # 1. Roles
    roles = {}
    for r_name in ["admin", "professional", "researcher"]:
        stmt = select(Role).where(Role.name == r_name)
        role = (await db_session.execute(stmt)).scalars().first()
        if not role:
            role = Role(role_id=uuid.uuid4(), name=r_name, description=f"Rol {r_name}")
            db_session.add(role)
            await db_session.flush()
        roles[r_name] = role

    # 2. Tipos de afasia
    for a_name in ["Broca", "Wernicke", "Mixta", "No clasificada"]:
        stmt = select(AphasiaType).where(AphasiaType.name == a_name)
        if not (await db_session.execute(stmt)).scalars().first():
            db_session.add(AphasiaType(aphasia_type_id=uuid.uuid4(), name=a_name))

    # 3. Niveles de severidad
    for s_name in ["Leve", "Moderada", "Severa"]:
        stmt = select(SeverityLevel).where(SeverityLevel.name == s_name)
        if not (await db_session.execute(stmt)).scalars().first():
            db_session.add(SeverityLevel(severity_level_id=uuid.uuid4(), name=s_name))

    # 4. Protocolo FAS y Subpruebas
    stmt = select(Protocol).where(Protocol.name == "Fluencia Verbal FAS")
    proto = (await db_session.execute(stmt)).scalars().first()
    if not proto:
        proto = Protocol(
            protocol_id=uuid.uuid4(),
            name="Fluencia Verbal FAS",
            version="1.0",
            description="FAS test",
        )
        db_session.add(proto)
        await db_session.flush()

        # Subprueba 1: Letra F
        sub1 = Subtest(
            subtest_id=uuid.uuid4(),
            protocol_id=proto.protocol_id,
            name="FAS Fonológico F",
            code="FAS_F",
            order_number=1,
            description="Evocación F",
        )
        # Subprueba 2: Semántica Animales
        sub2 = Subtest(
            subtest_id=uuid.uuid4(),
            protocol_id=proto.protocol_id,
            name="FAS Semántica Animales",
            code="FAS_ANIMALS",
            order_number=2,
            description="Evocación Animales",
        )
        db_session.add_all([sub1, sub2])

    # 5. Protocolo Externo (para validar rechazo de subpruebas cruzadas)
    stmt = select(Protocol).where(Protocol.name == "Protocolo Alternativo")
    alt_proto = (await db_session.execute(stmt)).scalars().first()
    if not alt_proto:
        alt_proto = Protocol(
            protocol_id=uuid.uuid4(),
            name="Protocolo Alternativo",
            version="1.0",
        )
        db_session.add(alt_proto)
        await db_session.flush()

        foreign_sub = Subtest(
            subtest_id=uuid.uuid4(),
            protocol_id=alt_proto.protocol_id,
            name="Subprueba Ajena",
            code="SUB_FOREIGN",
            order_number=1,
        )
        db_session.add(foreign_sub)

    # 6. Usuarios clínicos de prueba
    prof_uuid = uuid.UUID("11111111-1111-1111-1111-111111111111")
    stmt = select(User).where(User.user_id == prof_uuid)
    prof_user = (await db_session.execute(stmt)).scalars().first()
    if not prof_user:
        prof_user = User(
            user_id=prof_uuid,
            role_id=roles["professional"].role_id,
            username="fonoaudiologo_ana",
            email="ana.profesional@lingua.neurotech.org",
            first_name="Ana",
            last_name="García",
        )
        db_session.add(prof_user)

    admin_uuid = uuid.UUID("22222222-2222-2222-2222-222222222222")
    stmt = select(User).where(User.user_id == admin_uuid)
    admin_user = (await db_session.execute(stmt)).scalars().first()
    if not admin_user:
        admin_user = User(
            user_id=admin_uuid,
            role_id=roles["admin"].role_id,
            username="admin_carlos",
            email="carlos.admin@lingua.neurotech.org",
            first_name="Carlos",
            last_name="Mendoza",
        )
        db_session.add(admin_user)

    researcher_uuid = uuid.UUID("33333333-3333-3333-3333-333333333333")
    stmt = select(User).where(User.user_id == researcher_uuid)
    researcher_user = (await db_session.execute(stmt)).scalars().first()
    if not researcher_user:
        researcher_user = User(
            user_id=researcher_uuid,
            role_id=roles["researcher"].role_id,
            username="investigador_pedro",
            email="pedro.investigador@lingua.neurotech.org",
            first_name="Pedro",
            last_name="Vargas",
        )
        db_session.add(researcher_user)

    await db_session.commit()
    return {
        "roles": roles,
        "professional_user": prof_user,
        "admin_user": admin_user,
        "researcher_user": researcher_user,
        "protocol": proto,
        "alt_protocol": alt_proto,
    }


@pytest.fixture
def professional_token() -> str:
    """Token Bearer simulado para el usuario con rol 'professional'."""
    return create_mock_access_token(
        sub="11111111-1111-1111-1111-111111111111",
        email="ana.profesional@lingua.neurotech.org",
    )


@pytest.fixture
def admin_token() -> str:
    """Token Bearer simulado para el usuario con rol 'admin'."""
    return create_mock_access_token(
        sub="22222222-2222-2222-2222-222222222222",
        email="carlos.admin@lingua.neurotech.org",
    )


@pytest.fixture
def researcher_token() -> str:
    """Token Bearer simulado para el usuario con rol 'researcher'."""
    return create_mock_access_token(
        sub="33333333-3333-3333-3333-333333333333",
        email="pedro.investigador@lingua.neurotech.org",
    )


@pytest_asyncio.fixture(scope="function")
async def client(seed_data) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTPX asíncrono configurado con la base de datos de test en memoria."""
    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
