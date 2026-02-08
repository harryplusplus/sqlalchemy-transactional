# sqlalchemy-transactional

Spring-style transactional boundaries for SQLAlchemy async sessions.
Inspired by Spring Framework's `@Transactional` model.

## Quick Start

```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from sqlalchemy_transactional.asyncio import (
    current_session,
    sessionmaker_context,
    transactional,
)
from sqlalchemy_transactional.common import Propagation

engine = create_async_engine("sqlite+aiosqlite:///app.db")
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


# 1) Bind async_sessionmaker once per request/job boundary
@app.middleware("http")
async def transactional_context_middleware(request, call_next):
    async with sessionmaker_context(sessionmaker):
        return await call_next(request)


# 2) Write service logic without manual begin/commit/rollback
@transactional  # default propagation = REQUIRED
async def create_user(name: str) -> None:
    await current_session().execute(
        text("INSERT INTO users (name) VALUES (:name)"),
        {"name": name},
    )


@transactional(Propagation.REQUIRES_NEW)
async def write_audit_log(message: str) -> None:
    await current_session().execute(
        text("INSERT INTO audit_logs (message) VALUES (:message)"),
        {"message": message},
    )
```

## Why Use This

- Keep transaction plumbing out of service code.
- Declare transaction scope at the function boundary.
- Use familiar propagation semantics from Spring (`REQUIRED`, `REQUIRES_NEW`, etc.).
- Apply isolation level declaratively when needed.
- Make service methods easier to read, test, and review.

## Propagation Modes

- `REQUIRED` (default): Join an active transaction, or create one if none exists.
- `MANDATORY`: Require an active transaction; raise an error if missing.
- `REQUIRES_NEW`: Always execute in a new transaction.
- `NESTED`: Use savepoint semantics inside an active transaction; otherwise behave like `REQUIRED`.

## Isolation Level

Set isolation level at the decorator boundary:

```python
@transactional(isolation_level="SERIALIZABLE")
async def run_settlement() -> None:
    await current_session().execute(...)
```

If `isolation_level` is omitted (`None`, the default), SQLAlchemy uses the engine/dialect default isolation behavior from your database driver.

Combine with propagation when needed:

```python
@transactional(Propagation.REQUIRES_NEW, isolation_level="SERIALIZABLE")
async def write_critical_audit_log() -> None:
    await current_session().execute(...)
```

When `isolation_level` is applied:
- The decorator creates a new transaction (`REQUIRES_NEW`, or `REQUIRED` / `NESTED` when no active transaction exists).

When `isolation_level` is not applied by this decorator:
- The function joins an already active transaction (`REQUIRED` with an active transaction, `MANDATORY`, or `NESTED` with an active transaction).

## Contributing

Development workflow, checks, and test policies are defined in `AGENTS.md`.
