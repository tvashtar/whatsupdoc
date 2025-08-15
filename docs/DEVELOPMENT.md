# Development Guide

## ⚠️ Important: Background Process Management

**CRITICAL REMINDER for Claude Code**: When testing web servers (uvicorn, flask, gradio) using `run_in_background=true`,
killing the bash session does NOT kill the child processes. Always check for and manually kill remaining processes:

```bash
# Check for running servers
ps aux | grep -E "(uvicorn|flask|gradio)"
lsof -i :8000  # Check specific ports

# Kill processes properly
kill -9 <PID>  # Use actual process IDs, not bash session IDs
```

**Better approach**: Use foreground processes for testing or track PIDs explicitly for cleanup.

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

# Web Interface (NEW)
python scripts/launch_web.py                         # Launch complete web interface (FastAPI + Gradio)
uv run python src/whatsupdoc/web/app.py              # Gradio admin interface only (port 7860)
uvicorn whatsupdoc.web.api:app --reload              # FastAPI + Gradio web service (port 8000)
uv run python tests/web/test_web_interface.py        # Web interface integration tests
uv run python tests/web/demo_web_interface.py        # Web interface demo

# Testing
uv run pytest                                    # Run all tests
uv run tests/test_rag_engine_connection.py      # RAG Engine connection test
uv run tests/test_gemini_integration.py         # Gemini integration test
uv run tests/test_slack_connection.py           # Slack connection test
uv run tests/run_all_tests.py                   # Run comprehensive test suite
uv run python tests/web/test_web_interface.py   # Web interface tests

# Code Quality (optional - pre-commit runs automatically)
uv run ruff check --fix .                       # Lint and fix code
uv run ruff format .                             # Format code
uv run mypy .                                    # Type checking
```

## Pre-commit Hook Configuration

**✅ AUTOMATED QUALITY CHECKS**: Run before every commit with optimized performance
- **Targeted File Scanning**: Only runs on Python files in `src/`, `tests/`, `scripts/`, and `cloud-functions/`
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

### Multi-Interface Support
The system now supports three interfaces:
- **Slack Bot**: Original chat interface for internal use
- **Web API**: REST endpoints for external integrations (`/api/health`, `/api/chat`)
- **Admin UI**: Gradio interface for RAG testing and management (`/admin`)

### Dual Mode Support
The bot supports both development and production modes:
- **Socket Mode**: For local development (uses SLACK_APP_TOKEN)
- **HTTP Mode**: For Cloud Run deployment (uses PORT environment variable)

### Configuration
- Uses `pydantic-settings` for environment variable management with modern v2 syntax
- `.env` file for local development
- Environment variables set directly in Cloud Run for production
- **Type-safe configuration**: All settings validated with Pydantic models

### RAG Search Configuration

#### Distance Threshold Findings
**Key Discovery**: The Vertex AI RAG API uses `vector_distance_threshold` (not similarity), where:
- **Distance = 1 - Cosine Similarity** for normalized vectors
- **Lower distance = Higher similarity** (counter-intuitive parameter naming)
- **Range**: 0.0 (identical) to 2.0 (opposite vectors)

#### Optimal Threshold Settings
Through comprehensive testing, we determined:
- **0.8 (recommended)**: Allows moderate to low similarity matches, works with semantic reranker
- **0.6**: Works for most queries but may miss some edge cases
- **0.3**: Too restrictive, misses relevant content for broader queries
- **< 0.3**: Fails to return chunks even for reasonable queries

#### Why Use a Threshold?
Despite having a semantic reranker, the threshold serves important purposes:
1. **Pre-filtering**: Applied BEFORE semantic reranking to reduce candidates
2. **Performance**: Reduces expensive reranking operations
3. **Cost optimization**: Semantic reranking has usage costs
4. **Quality baseline**: Prevents completely irrelevant chunks from being ranked

#### Testing Approach
Use the comprehensive RAG functionality tests in `tests/e2e/rag_functionality_tester.py`:
```bash
uv run python tests/e2e/rag_functionality_tester.py
```
This validates:
- Actual chunk retrieval across threshold ranges
- Full RAG pipeline (query → chunks → answer generation)
- End-to-end webhook integration
- Real functionality vs. just HTTP status codes

## Web Interface Architecture

### Components Added (Phase 14 ✅)
**Three new modules in `src/whatsupdoc/web/`:**

**1. `models.py`** - Pydantic schemas for web API
- `ChatRequest/ChatResponse` - Main chat endpoint schemas
- `HealthResponse` - Service status and dependency health
- `ErrorResponse` - Standardized error handling

**2. `service.py`** - WebRAGService integration layer
- Combines `VertexRAGClient` + `GeminiRAGService`
- Unified query processing with timing and error handling
- Source attribution and confidence scoring

**3. `api.py`** - FastAPI application
- `GET /api/health` - Service health with dependency status
- `POST /api/chat` - Main RAG query endpoint (rate limited)
- Global error handling and request tracking
- CORS configuration for specified domains

**4. `gradio_interface.py`** - Admin testing interface
- Authentication-protected Gradio app
- Real-time RAG pipeline testing
- Connection testing and service monitoring
- Adjustable query parameters (confidence, max results)

### Deployment Options
**Option 1: Standalone Gradio** (development/testing)
```bash
python -m whatsupdoc.web.gradio_interface
# Access: http://localhost:7860 (admin/changeme123!)
```

**Option 2: Integrated FastAPI** (production)
```bash
uvicorn whatsupdoc.web.api:app --host 0.0.0.0 --port 8000
# API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin
# Docs: http://localhost:8000/docs
```

### Security Features
- **Rate Limiting**: 10 requests/minute per IP (SlowAPI)
- **CORS Restrictions**: Limited to specified domains
- **Authentication**: Basic auth for admin interface
- **Input Validation**: Pydantic schemas with length/range limits
- **Error Tracking**: Request IDs and structured logging

### Testing
```bash
# Test web interface components
uv run python tests/web/test_web_interface.py

# Demo web interface functionality
uv run python tests/web/demo_web_interface.py

# Test API endpoints
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is our policy?"}'
```

### Next Phase: Embeddable Widget
- JavaScript widget for website integration
- Shadow DOM for style isolation
- One-line embedding with `<script>` tag
- Domain-based security restrictions
