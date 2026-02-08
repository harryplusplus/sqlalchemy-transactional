# sqlalchemy-transactional

Spring-style transactional boundaries for SQLAlchemy async sessions.
Inspired by Spring Framework's `@Transactional` model.

**Table of Contents**
<!-- markdown-toc-cli --prefix='* ' --indentation='  ' --minlevel=2 --maxlevel=2 -->

* [Quick Start](#quick-start)
* [Why Use This](#why-use-this)
* [Propagation Modes](#propagation-modes)
* [Isolation Level](#isolation-level)
* [Spring-to-FastAPI Mapping](#spring-to-fastapi-mapping)
* [Contributing](#contributing)

<!-- markdown-toc-cli-end -->

## Quick Start

This quick start uses a FastAPI integration example to show transaction boundaries in a real application flow, not as isolated snippets.
It assumes you already run FastAPI with an `async_sessionmaker` and want Spring-like declarative transaction boundaries in service methods.

```python
from fastapi import FastAPI, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from sqlalchemy_transactional.asyncio import (
    current_session,
    sessionmaker_context,
    transactional,
)
from sqlalchemy_transactional.common import Propagation

app = FastAPI()
engine = create_async_engine("sqlite+aiosqlite:///app.db")
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


# 1) Bind async_sessionmaker once per request boundary
@app.middleware("http")
async def transactional_context_middleware(request: Request, call_next):
    async with sessionmaker_context(sessionmaker):
        return await call_next(request)


class CreateUserRequest(BaseModel):
    name: str


# 2) Put transaction boundaries on service methods
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


user_service = UserService()


# 3) Route/controller stays thin
@app.post("/users")
async def create_user(payload: CreateUserRequest) -> dict[str, str]:
    await user_service.create_user(payload.name)
    return {"status": "ok"}
```

## Why Use This

- Keep transaction plumbing out of service code.
- Declare transaction scope at the function boundary.
- Use familiar propagation semantics from Spring (`REQUIRED`, `MANDATORY`, etc.).
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

## Spring-to-FastAPI Mapping

| Spring concept | FastAPI + sqlalchemy-transactional |
| --- | --- |
| `@Transactional` on service methods | `@transactional` on async service methods |
| `@Transactional(propagation = REQUIRED)` | `@transactional` (default = `Propagation.REQUIRED`) |
| `@Transactional(propagation = MANDATORY)` | `@transactional(Propagation.MANDATORY)` |
| Request filter/interceptor binds tx resources | `@app.middleware("http")` + `sessionmaker_context(sessionmaker)` |
| Current tx-bound resource lookup | `current_session()` |

## Contributing

Development workflow, checks, and test policies are defined in `AGENTS.md`.
