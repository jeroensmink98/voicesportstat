Prompt for coding agent

This Python project uses the uv package manager instead of pip/poetry/pipenv.

Key points for you to know:

Dependencies are declared in pyproject.toml and locked in uv.lock.

Install with:

uv sync


Run commands in the environment with:

uv run <command>


Example:

uv run fastapi dev
uv run pytest


Add new dependencies with:

uv add <package>


Task:
When suggesting code changes, dependency additions, or commands, always use uv commands instead of pip or poetry.