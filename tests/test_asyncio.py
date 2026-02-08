from typing import cast

import pytest
from conftest import Sessionmaker
from sqlalchemy import text
from sqlalchemy_transactional.asyncio import (
    current_session,
    sessionmaker_context,
    transactional,
)
from sqlalchemy_transactional.common import (
    Propagation,
    SessionFactoryAlreadyBoundError,
    SessionFactoryNotBoundError,
    SessionNotBoundError,
    TransactionRequiredError,
    UnsupportedPropagationModeError,
)


async def _count_items(sm: Sessionmaker) -> int:
    async with sm() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM items"))
        return result.scalar_one()


async def _names(sm: Sessionmaker) -> list[str]:
    async with sm() as session:
        result = await session.execute(text("SELECT name FROM items ORDER BY id"))
        return [row[0] for row in result.fetchall()]


@pytest.mark.asyncio
async def test_sessionmaker_context_sets_and_resets(
    sessionmaker: Sessionmaker,
) -> None:
    @transactional
    async def requires_sessionmaker() -> None:
        current_session()

    with pytest.raises(SessionFactoryNotBoundError):
        await requires_sessionmaker()

    async with sessionmaker_context(sessionmaker):
        await requires_sessionmaker()


@pytest.mark.asyncio
async def test_sessionmaker_context_rejects_nested_binding(
    sessionmaker: Sessionmaker,
) -> None:
    async with sessionmaker_context(sessionmaker):
        with pytest.raises(SessionFactoryAlreadyBoundError):
            async with sessionmaker_context(sessionmaker):
                pass


@pytest.mark.asyncio
async def test_required_creates_session_and_commits(
    setup_db: None,
    sessionmaker: Sessionmaker,
) -> None:
    async with sessionmaker_context(sessionmaker):

        @transactional
        async def insert() -> None:
            session = current_session()
            await session.execute(
                text("INSERT INTO items (name) VALUES (:name)"),
                {"name": "required"},
            )

        await insert()

    assert await _count_items(sessionmaker) == 1

    with pytest.raises(SessionNotBoundError):
        current_session()


@pytest.mark.asyncio
async def test_required_reuses_existing_session(
    setup_db: None,
    sessionmaker: Sessionmaker,
) -> None:
    async with sessionmaker_context(sessionmaker):

        @transactional
        async def inner() -> int:
            return id(current_session())

        @transactional
        async def outer() -> tuple[int, int]:
            outer_session_id = id(current_session())
            inner_session_id = await inner()
            return outer_session_id, inner_session_id

        outer_session_id, inner_session_id = await outer()

    assert inner_session_id == outer_session_id


@pytest.mark.asyncio
async def test_mandatory_requires_existing_transaction(
    setup_db: None,
    sessionmaker: Sessionmaker,
) -> None:
    async with sessionmaker_context(sessionmaker):

        @transactional(Propagation.MANDATORY)
        async def insert_mandatory() -> None:
            session = current_session()
            await session.execute(
                text("INSERT INTO items (name) VALUES (:name)"),
                {"name": "mandatory"},
            )

        with pytest.raises(TransactionRequiredError):
            await insert_mandatory()

        @transactional
        async def outer() -> None:
            await insert_mandatory()

        await outer()

    assert await _count_items(sessionmaker) == 1


@pytest.mark.asyncio
async def test_requires_new_commits_independently(
    setup_db: None,
    sessionmaker: Sessionmaker,
) -> None:
    async with sessionmaker_context(sessionmaker):

        @transactional(Propagation.REQUIRES_NEW)
        async def inner(session_ids: list[int]) -> None:
            session_ids.append(id(current_session()))
            await current_session().execute(
                text("INSERT INTO items (name) VALUES (:name)"),
                {"name": "inner"},
            )

        @transactional
        async def outer() -> None:
            session_ids: list[int] = [id(current_session())]
            await inner(session_ids)
            await current_session().execute(
                text("INSERT INTO items (name) VALUES (:name)"),
                {"name": "outer"},
            )
            raise RuntimeError("force rollback")

        with pytest.raises(RuntimeError, match="force rollback"):
            await outer()

    assert await _names(sessionmaker) == ["inner"]


@pytest.mark.asyncio
async def test_nested_without_existing_session_acts_like_required(
    setup_db: None,
    sessionmaker: Sessionmaker,
) -> None:
    async with sessionmaker_context(sessionmaker):

        @transactional(Propagation.NESTED)
        async def insert() -> None:
            await current_session().execute(
                text("INSERT INTO items (name) VALUES (:name)"),
                {"name": "nested_root"},
            )

        await insert()

    assert await _names(sessionmaker) == ["nested_root"]


@pytest.mark.asyncio
async def test_nested_rollback_to_savepoint(
    setup_db: None,
    sessionmaker: Sessionmaker,
) -> None:
    async with sessionmaker_context(sessionmaker):

        @transactional(Propagation.NESTED)
        async def inner() -> None:
            await current_session().execute(
                text("INSERT INTO items (name) VALUES (:name)"),
                {"name": "nested"},
            )
            raise ValueError("nested fail")

        @transactional
        async def outer() -> None:
            await current_session().execute(
                text("INSERT INTO items (name) VALUES (:name)"),
                {"name": "outer"},
            )
            try:
                await inner()
            except ValueError:
                pass

        await outer()

    assert await _names(sessionmaker) == ["outer"]


@pytest.mark.asyncio
async def test_isolation_level_is_applied(
    setup_db: None,
    sessionmaker: Sessionmaker,
) -> None:
    async with sessionmaker_context(sessionmaker):

        @transactional(isolation_level="SERIALIZABLE")
        async def insert() -> None:
            await current_session().execute(
                text("INSERT INTO items (name) VALUES (:name)"),
                {"name": "isolation"},
            )

        await insert()

    assert await _names(sessionmaker) == ["isolation"]


@pytest.mark.asyncio
async def test_unsupported_propagation_raises_meaningful_error(
    sessionmaker: Sessionmaker,
) -> None:
    class UnsupportedPropagation:
        value = "unsupported"

    propagation = cast(Propagation, UnsupportedPropagation())

    async with sessionmaker_context(sessionmaker):

        @transactional(propagation)
        async def run() -> None:
            return None

        with pytest.raises(UnsupportedPropagationModeError) as exc_info:
            await run()

    assert exc_info.value.propagation is propagation
    assert "unsupported" in str(exc_info.value)
