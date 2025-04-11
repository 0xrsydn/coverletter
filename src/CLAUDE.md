# CLAUDE.md - CoverLetter Backend Guide

## Development Commands
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run locally: `uvicorn main:app --reload`
- Docker local: `docker-compose -f docker-compose.local.yml up -d`
- Docker prod: `docker-compose up -d`
- Health check: `curl -f http://localhost:8000/health`

## Code Style Guidelines
- **Imports**: Standard lib → Third-party → Internal (separated by newlines)
- **Naming**: snake_case (variables/functions), CamelCase (classes), UPPER_CASE (constants)
- **Type hints**: Always use typing annotations for parameters and return values
- **Error handling**: Use custom exceptions from modules.errors, proper try/except blocks
- **Documentation**: Triple double-quote docstrings with Args/Returns/Raises sections
- **Structure**: Modular design with clear separation of concerns (company, job, cover_letter)
- **Logging**: Use structured logging with request ID tracking
- **Monitoring**: Timing metrics via StepTimer, Prometheus instrumentation
- **Testing**: Follow FastAPI testing patterns with TestClient

When contributing, maintain the existing architecture and follow established patterns for consistency.