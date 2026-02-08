import pytest
from conftest import Sessionmaker
from sqlalchemy import text
from sqlalchemy_transactional.internal import runtime


async def _count_items(sm: Sessionmaker) -> int:
    async with sm() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM items"))
        return result.scalar_one()


@pytest.mark.asyncio
async def test_run_with_isolation_sets_context_and_commits(
    setup_db: None,
    sessionmaker: Sessionmaker,
) -> None:
    async with sessionmaker() as session:

        async def invoke() -> str:
            assert runtime.session_ctx_var.get() is session
            await session.execute(
                text("INSERT INTO items (name) VALUES (:name)"),
                {"name": "isolated"},
            )
            return "ok"

        result = await runtime.run_with_isolation(
            session,
            "SERIALIZABLE",
            invoke,
        )

    assert result == "ok"
    assert runtime.session_ctx_var.get() is None
    assert await _count_items(sessionmaker) == 1


@pytest.mark.asyncio
async def test_commit_or_rollback_rolls_back_on_error(
    setup_db: None,
    sessionmaker: Sessionmaker,
) -> None:
    async with sessionmaker() as session:

        async def invoke() -> None:
            await session.execute(
                text("INSERT INTO items (name) VALUES (:name)"),
                {"name": "rollback"},
            )
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            await runtime.commit_or_rollback(session, invoke)

    assert await _count_items(sessionmaker) == 0
