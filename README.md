# sqlalchemy-transactional

Transaction propagation decorators and context management for SQLAlchemy async sessions.

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


@transactional
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


async with sessionmaker_context(sessionmaker):
    await create_user("alice")
```

### Propagation Modes
- `REQUIRED`: Join the current transaction, or start one if none exists.
- `MANDATORY`: Require an active transaction; raise an error if none exists.
- `REQUIRES_NEW`: Always run in a new transaction.
- `NESTED`: Use a nested transaction (savepoint) if one exists, otherwise behave like `REQUIRED`.

## Contributing

Development workflow, checks, and test policies are defined in `AGENTS.md`.
