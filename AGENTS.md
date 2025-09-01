# Repository Guidelines

## Project Structure & Module Organization
- `src/fullon_cache_api/`: Core library (types, base classes, models, routers).
- `tests/`: Pytest suite (unit/integration); name files `test_*.py`.
- `examples/`: Minimal usage snippets and scripts.
- `docs/`: Additional design and structure docs.
- `Makefile`: Common dev tasks; prefer `make <target>`.
- `run_test.py`: Full local check runner (tests, lint, types, coverage).

## Build, Test, and Development Commands
- `make setup`: Install deps, setup pre-commit, create `.env` from example.
- `make test`: Run pytest suite. Example: `poetry run python run_test.py` for full checks.
- `make test-cov`: Tests with coverage report (HTML + terminal).
- `make lint` / `make format`: Ruff + mypy; Black/auto-fix.
- `make check`: Black check, Ruff, mypy, tests – run before PRs.
- `make dev` / `make prod`: Start FastAPI/WS app via Uvicorn.

## Coding Style & Naming Conventions
- Python 3.13; 4-space indent; max line length 88.
- Tools: Black (format), Ruff (lint/imports), mypy (types, strict settings).
- Naming: modules/files `snake_case.py`; classes `PascalCase`; functions/vars `snake_case`.
- Type hints required for public APIs; avoid `Any` and untyped defs.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio`, `pytest-cov`.
- Place tests in `tests/`; name `test_*.py`; async tests use `pytest.mark.asyncio`.
- Target: maintain 100% coverage for new/modified code; keep tests deterministic.
- Useful: `make test-cov` and open `htmlcov/index.html` for gaps.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, etc. Example: `feat: implement WebSocket base classes (#22)`.
- Reference issues/PRs (e.g., `#123`) and keep scope small.
- Before opening a PR: `make check` passes; add/adjust tests; update docs if behavior changes.
- PR description: problem/approach, linked issue, test evidence (logs or screenshots of coverage where relevant).

## Security & Configuration Tips
- Copy config: `cp .env.example .env`; never commit secrets.
- Redis/WS settings live in `.env`; keep production creds external (vault/CI secrets).
- Use Poetry (`poetry shell`, `make deps-update`) to manage dependencies reproducibly.

## Agent-Specific Instructions
- Deep architecture and implementation patterns: see `CLAUDE.md`.
- Codex CLI users:
  - Keep diffs small and focused; use `apply_patch` for edits.
  - Prefer `rg` for search; read files in small chunks (<250 lines).
  - Validate before PRs: `make check` or `poetry run python run_test.py`.
  - Respect constraints: READ-ONLY cache API, async iterators for streaming, no callbacks.
  - Never commit secrets or `.env`; avoid network calls unless explicitly required.
