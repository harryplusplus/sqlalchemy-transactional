from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, AsyncGenerator, Callable, overload

from sqlalchemy.engine.interfaces import IsolationLevel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_transactional.common import (
    Propagation,
    SessionFactoryAlreadyBoundError,
    SessionNotBoundError,
)
from sqlalchemy_transactional.internal.runtime import (
    Sessionmaker,
    resolve_invoke,
    resolve_propagation,
    run_transactional,
    session_ctx_var,
    sessionmaker_ctx_var,
)


@asynccontextmanager
async def sessionmaker_context(
    sessionmaker: Sessionmaker,
) -> AsyncGenerator[Sessionmaker, None]:
    if sessionmaker_ctx_var.get() is not None:
        raise SessionFactoryAlreadyBoundError()

    token = sessionmaker_ctx_var.set(sessionmaker)
    try:
        yield sessionmaker
    finally:
        sessionmaker_ctx_var.reset(token)


def current_session() -> AsyncSession:
    session = session_ctx_var.get()
    if session is None:
        raise SessionNotBoundError()

    return session


@overload
def transactional(func_or_propagation: Callable[..., Any]) -> Callable[..., Any]: ...
@overload
def transactional(
    func_or_propagation: Propagation | None = None,
    *,
    isolation_level: IsolationLevel | None = None,
) -> Callable[..., Any]: ...
def transactional(
    func_or_propagation: Callable[..., Any] | Propagation | None = None,
    *,
    isolation_level: IsolationLevel | None = None,
) -> Callable[..., Any]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            propagation = resolve_propagation(func_or_propagation)
            invoke = resolve_invoke(func, args, kwargs)

            return await run_transactional(
                propagation,
                isolation_level,
                invoke,
            )

        return wrapper

    if callable(func_or_propagation):
        return decorator(func_or_propagation)

    return decorator
