# Development Guide

## Setup

### Quick Start
```bash
# Full development setup
uv sync  # Installs both main and dev dependencies by default

# Install pre-commit hooks (one-time setup)
uv run pre-commit install
```

### Development Commands
```bash
# Run the bot locally
uv run whatsupdoc

# Testing
uv run pytest                                    # Run all tests
uv run tests/test_rag_engine_connection.py      # RAG Engine connection test
uv run tests/test_gemini_integration.py         # Gemini integration test
uv run tests/test_slack_connection.py           # Slack connection test
uv run tests/run_all_tests.py                   # Run comprehensive test suite

# Code Quality (optional - pre-commit runs automatically)
uv run ruff check --fix .                       # Lint and fix code
uv run ruff format .                             # Format code
uv run mypy .                                    # Type checking
```

## Pre-commit Hook Configuration

**✅ AUTOMATED QUALITY CHECKS**: Run before every commit
- **Automated Formatting**: ruff --fix and ruff-format
- **Type Checking**: mypy --strict prevents type errors
- **Code Quality**: Removes trailing whitespace, validates YAML, prevents large files

### What Runs on Each Commit
1. **ruff --fix**: Automatically fixes code style issues (imports, formatting, etc.)
2. **ruff-format**: Formats code consistently
3. **mypy --strict**: Type checking with strict configuration
4. **pre-commit-hooks**: Cleans trailing whitespace, validates YAML, checks file sizes

### Setup for New Developers
```bash
uv sync && uv run pre-commit install
```

## Dependency Management

### UV Workflow Clarified
- `uv sync` = Installs both main AND dev dependencies by default
- `uv sync --no-dev` = Production-only dependencies (used in Dockerfile)
- `uv sync --only-dev` = Development dependencies only

### Current Dev Dependencies
All pytest plugins are valuable and should be kept:
- `pytest-asyncio` - Essential for async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Better mocking capabilities
- `requests-mock` - HTTP request mocking for API tests

## Testing Status

**✅ COMPREHENSIVE TEST SUITE** covering:
- RAG Engine connection and search functionality
- Gemini integration and response generation
- Slack bot configuration and API connection
- Package imports and dependencies
- GCP authentication and access

## Architecture Notes

### Dual Mode Support
The bot supports both development and production modes:
- **Socket Mode**: For local development (uses SLACK_APP_TOKEN)
- **HTTP Mode**: For Cloud Run deployment (uses PORT environment variable)

### Configuration
- Uses `pydantic-settings` for environment variable management
- `.env` file for local development
- Environment variables set directly in Cloud Run for production
