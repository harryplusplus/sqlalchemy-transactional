from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, AsyncGenerator, Awaitable, Callable

from sqlalchemy.engine.interfaces import IsolationLevel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_transactional.common import (
    Propagation,
    SessionFactoryNotBoundError,
    TransactionRequiredError,
    UnsupportedPropagationModeError,
)

Sessionmaker = Callable[[], AsyncSession]
Invoke = Callable[[], Awaitable[Any]]

SessionmakerContext = ContextVar[Sessionmaker | None]
SessionContext = ContextVar[AsyncSession | None]

sessionmaker_ctx_var: SessionmakerContext = ContextVar(
    "sqlalchemy_transactional.asyncio.sessionmaker", default=None
)
session_ctx_var: SessionContext = ContextVar(
    "sqlalchemy_transactional.asyncio.session", default=None
)


def current_sessionmaker() -> Sessionmaker:
    sessionmaker = sessionmaker_ctx_var.get()
    if sessionmaker is None:
        raise SessionFactoryNotBoundError()

    return sessionmaker


@asynccontextmanager
async def session_context(
    session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    token = session_ctx_var.set(session)
    try:
        yield session
    finally:
        session_ctx_var.reset(token)


def resolve_propagation(
    func_or_propagation: Callable[..., Any] | Propagation | None,
) -> Propagation:
    if callable(func_or_propagation) or func_or_propagation is None:
        return Propagation.REQUIRED

    return func_or_propagation


def resolve_invoke(func: Callable[..., Any], args: Any, kwargs: Any) -> Invoke:
    async def invoke() -> Any:
        return await func(*args, **kwargs)

    return invoke


async def run_transactional(
    propagation: Propagation,
    isolation_level: IsolationLevel | None,
    invoke: Invoke,
) -> Any:
    if propagation == Propagation.REQUIRED:
        if session_ctx_var.get() is not None:
            return await invoke()

        return await create_transaction(isolation_level, invoke)

    if propagation == Propagation.MANDATORY:
        if session_ctx_var.get() is None:
            raise TransactionRequiredError()

        return await invoke()

    if propagation == Propagation.REQUIRES_NEW:
        return await create_transaction(isolation_level, invoke)

    if propagation == Propagation.NESTED:
        session = session_ctx_var.get()
        if session is None:
            return await create_transaction(isolation_level, invoke)

        async with session.begin_nested():
            return await invoke()

    raise UnsupportedPropagationModeError(propagation)


async def create_transaction(
    isolation_level: IsolationLevel | None,
    invoke: Invoke,
) -> Any:
    sessionmaker = current_sessionmaker()
    async with sessionmaker() as session:
        if isolation_level is None:
            return await run_with_transaction(session, invoke)

        return await run_with_isolation(session, isolation_level, invoke)


async def run_with_transaction(
    session: AsyncSession,
    invoke: Invoke,
) -> Any:
    async with session.begin():
        async with session_context(session):
            return await invoke()


async def run_with_isolation(
    session: AsyncSession,
    isolation_level: IsolationLevel,
    invoke: Invoke,
) -> Any:
    await session.connection(execution_options={"isolation_level": isolation_level})

    async with session_context(session):
        return await commit_or_rollback(session, invoke)


async def commit_or_rollback(
    session: AsyncSession,
    invoke: Invoke,
) -> Any:
    try:
        result = await invoke()
    except Exception:
        await session.rollback()
        raise

    await session.commit()
    return result
