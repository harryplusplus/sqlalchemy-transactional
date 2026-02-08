# sqlalchemy-transactional

## Development

### Prerequisites
- Python 3.10+
- `uv` (dependency management + project commands)

### Setup
```bash
uv sync --group dev
```

### Test
```bash
scripts/test.sh
```

`scripts/test.sh` runs tests in 2 phases:
1. `uv run --group dev pytest` (normal project environment)
2. `uv run --isolated --group dev --with "sqlalchemy[asyncio]==2.0.0" pytest` (minimum supported SQLAlchemy check)

Pass pytest options through:

```bash
scripts/test.sh -k transactional
```

Override the minimum SQLAlchemy version if needed:

```bash
MIN_SQLALCHEMY_VERSION=2.0.1 scripts/test.sh
```
