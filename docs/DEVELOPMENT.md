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

**✅ AUTOMATED QUALITY CHECKS**: Run before every commit with optimized performance
- **Targeted File Scanning**: Only runs on Python files in `src/`, `tests/`, `wsgi.py`, and `cloud-functions/`
- **Automated Formatting**: ruff --fix and ruff-format with auto-fixes
- **Comprehensive Type Checking**: mypy with practical configuration optimized for speed
- **Code Quality**: Removes trailing whitespace, validates YAML, prevents large files

### What Runs on Each Commit
1. **ruff --fix**: Automatically fixes code style issues (imports, formatting, etc.)
2. **ruff-format**: Formats code consistently
3. **mypy**: Type checking with optimized configuration:
   - `--ignore-missing-imports`: Skips third-party library stubs
   - `--disallow-untyped-defs`: Requires type hints on all functions
   - `--warn-return-any`: Warns about functions returning Any
   - Disabled error codes for practical development: `misc`, `call-arg`, `no-any-return`
4. **pre-commit-hooks**: Cleans trailing whitespace, validates YAML, checks file sizes

### Performance Optimizations
- **3-5x faster execution** through targeted file patterns
- **Practical mypy settings** that catch real issues without being overly strict
- **Smart ignore rules** for style-only ruff checks that don't affect functionality

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

## Code Quality Standards

### Type Safety
**✅ FULLY TYPED CODEBASE**: All functions and methods have comprehensive type hints
- **Return type annotations**: Added to all 174+ functions across the codebase
- **Parameter types**: Complete type hints for function parameters
- **Pydantic v2 compatibility**: Modern `SettingsConfigDict` usage
- **PEP 561 compliance**: `py.typed` marker file for package typing

### Ruff Configuration
**Smart ignore rules** for style-only checks that don't affect functionality:
- `D100`, `D104`: Missing module/package docstrings (not critical for functionality)
- `D203`, `D213`: Docstring formatting conflicts (allows either style)
- `D401`, `D205`, `D400`, `D415`: Imperative mood and summary formatting
- `PLR0913`: Too many function arguments (architectural choice)

### MyPy Integration
- **Strict type checking** with practical developer experience
- **Async/await patterns**: Proper handling without nested lambda issues
- **Flask integration**: Correct return type hints for WSGI applications
- **Third-party compatibility**: Graceful handling of untyped dependencies

## Architecture Notes

### Dual Mode Support
The bot supports both development and production modes:
- **Socket Mode**: For local development (uses SLACK_APP_TOKEN)
- **HTTP Mode**: For Cloud Run deployment (uses PORT environment variable)

### Configuration
- Uses `pydantic-settings` for environment variable management with modern v2 syntax
- `.env` file for local development
- Environment variables set directly in Cloud Run for production
- **Type-safe configuration**: All settings validated with Pydantic models
