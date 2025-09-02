# Repository Guidelines

## Project Structure & Module Organization
- `src/fullon_cache_api/`: Core library (types, models, routers, base classes).
- `tests/`: Pytest suite (unit/integration). Name files `test_*.py`.
- `examples/`: Minimal scripts showing typical usage.
- `docs/` (@docs): Design notes and structure docs.
- `README.md`: Overview, setup, quickstart, and high-level API notes.
- `Makefile`: Common dev tasks (prefer `make <target>`).
- `run_test.py`: Full local check runner.

## Build, Test, and Development Commands
- `make setup`: Install deps with Poetry, set up pre-commit, copy `.env`.
- `make test`: Run pytest. Full checks: `poetry run python run_test.py`.
- `make test-cov`: Tests with coverage (HTML at `htmlcov/index.html`).
- `make lint` / `make format`: Ruff + mypy; Black/auto-fix.
- `make check`: Black check, Ruff, mypy, tests — run before PRs.
- `make dev` / `make prod`: Start FastAPI/WebSocket app via Uvicorn.

## Coding Style & Naming Conventions
- Python 3.13; 4-space indent; max line length 88.
- Tools: Black (format), Ruff (lint/imports), mypy (strict typing).
- Naming: modules `snake_case.py`; classes `PascalCase`; funcs/vars `snake_case`.
- Public APIs are fully typed; avoid `Any` and untyped defs.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio`, `pytest-cov`.
- Place tests in `tests/`; name `test_*.py`. Async tests use `pytest.mark.asyncio`.
- Target 100% coverage on new/changed code. Run `make test-cov` and inspect `htmlcov/`.

## Commit & Pull Request Guidelines
- Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, etc. Example: `feat: implement WebSocket base classes (#22)`.
- Reference issues/PRs (e.g., `#123`) and keep scope focused.
- Before opening a PR: `make check` passes; tests updated; docs adjusted if behavior changes.
- PR description: problem + approach, linked issue, and test evidence (logs or coverage screenshot).

## Security & Configuration Tips
- Copy env: `cp .env.example .env`. Never commit secrets.
- Redis/WS settings live in `.env`; keep production creds external (vault/CI secrets).
- Use Poetry for reproducible deps (`poetry shell`, `make deps-update`).

## Agent-Specific Instructions
- Architecture patterns: see `CLAUDE.md`.
- Constraints: READ-ONLY cache API, async iterators for streaming, no callbacks.
- Codex CLI: keep diffs small; use `apply_patch`; prefer `rg` for search; validate with `make check`.

## References
- `README.md`: Setup, local run, and repo overview.
- `docs/` (@docs): Design deep dives, architecture notes, ADRs.
- `CLAUDE.md`: Architecture rationale and agent patterns used here.
