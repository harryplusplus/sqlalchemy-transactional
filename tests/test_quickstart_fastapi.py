from collections.abc import Awaitable, Callable

import pytest
import pytest_asyncio
from conftest import Sessionmaker
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy_transactional.asyncio import (
    current_session,
    sessionmaker_context,
    transactional,
)
from sqlalchemy_transactional.common import Propagation, TransactionRequiredError
from starlette.responses import Response

users_table_ddl = text(
    "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
)


class CreateUserRequest(BaseModel):
    name: str


class UserService:
    @transactional  # default propagation = REQUIRED
    async def create_user(self, name: str) -> None:
        await self._validate_name(name)
        await self._insert_user(name)

    @transactional(Propagation.MANDATORY)
    async def _validate_name(self, name: str) -> None:
        result = await current_session().execute(
            text("SELECT 1 FROM users WHERE name = :name"),
            {"name": name},
        )
        if result.first() is not None:
            raise ValueError("name already exists")

    @transactional(Propagation.MANDATORY)
    async def _insert_user(self, name: str) -> None:
        await current_session().execute(
            text("INSERT INTO users (name) VALUES (:name)"),
            {"name": name},
        )


def create_app(
    sessionmaker: Sessionmaker,
    user_service: UserService,
) -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def transactional_context_middleware(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        async with sessionmaker_context(sessionmaker):
            return await call_next(request)

    @app.post("/users")
    async def create_user(  # pyright: ignore[reportUnusedFunction]
        payload: CreateUserRequest,
    ) -> dict[str, str]:
        await user_service.create_user(payload.name)
        return {"status": "ok"}

    return app


async def _user_names(sm: Sessionmaker) -> list[str]:
    async with sm() as session:
        result = await session.execute(text("SELECT name FROM users ORDER BY id"))
        return [row[0] for row in result.fetchall()]


@pytest_asyncio.fixture
async def setup_users_table(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(users_table_ddl)


@pytest.mark.asyncio
async def test_quickstart_fastapi_request_flow(
    setup_users_table: None,
    sessionmaker: Sessionmaker,
) -> None:
    user_service = UserService()
    app = create_app(sessionmaker, user_service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        first = await client.post("/users", json={"name": "harry"})
        assert first.status_code == 200
        assert first.json() == {"status": "ok"}

        with pytest.raises(ValueError, match="name already exists"):
            await client.post("/users", json={"name": "harry"})

    assert await _user_names(sessionmaker) == ["harry"]


@pytest.mark.asyncio
async def test_quickstart_mandatory_requires_existing_transaction(
    setup_users_table: None,
    sessionmaker: Sessionmaker,
) -> None:
    @transactional(Propagation.MANDATORY)
    async def mandatory_probe() -> None:
        await current_session().execute(text("SELECT 1"))

    async with sessionmaker_context(sessionmaker):
        with pytest.raises(TransactionRequiredError):
            await mandatory_probe()
