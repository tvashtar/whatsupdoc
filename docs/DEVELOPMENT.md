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

# Web Interface
python scripts/launch_web.py                         # Launch FastAPI server (port 8000)
uv run python src/whatsupdoc/web/app.py              # Gradio admin interface (port 7860)
uvicorn whatsupdoc.web.api:app --reload              # FastAPI API only (port 8000)
uv run python tests/web/test_web_interface.py        # Web interface integration tests
# Note: FastAPI and Gradio run separately now - no more /admin mounting

# Widget Development
cd src/whatsupdoc/web/widget
npm install                                           # Install widget dependencies (one-time)
npm run dev                                          # Start widget development server (port 3000)
npm run build                                        # Build widget for production
npm run watch                                        # Build widget in watch mode
# Widget is served by FastAPI at: http://localhost:8000/static/widget/whatsupdoc-widget.js
# Demo page at: http://localhost:8000/static/demo.html

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
The system now supports four interfaces:
- **Slack Bot**: Original chat interface for internal team use
- **Web API**: REST endpoints for external integrations (`/api/health`, `/api/chat`)
- **Admin UI**: Gradio interface for RAG testing and management (port 7860)
- **Embeddable Widget**: JavaScript widget for public website integration (`/static/widget/`)

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

## Widget Development Architecture

### Widget Components (Phase 15 ✅)
**Built using modern Web Components with Vite build system:**

**1. Source Files** (`src/whatsupdoc/web/widget/`)
- `src/whatsupdoc-widget.js` - Main widget Web Component with Shadow DOM
- `package.json` - NPM dependencies (Vite, Terser for minification)
- `vite.config.js` - Build configuration for UMD output
- `README.md` - Widget documentation and integration guide

**2. Build Output** (`src/whatsupdoc/web/static/widget/`)
- `whatsupdoc-widget.js` - Minified UMD build for browser embedding
- `whatsupdoc-widget.js.map` - Source map for debugging

**3. Demo & Testing** (`src/whatsupdoc/web/static/`)
- `demo.html` - Complete demonstration page with configuration playground
- Served by FastAPI at `http://localhost:8000/static/demo.html`

### Widget Architecture Features
- **Web Components**: Native browser API with custom elements
- **Shadow DOM**: Complete style isolation from host website
- **UMD Build**: Universal module definition for maximum browser compatibility
- **Auto-initialization**: Detects DOM ready state and initializes automatically
- **Configuration**: Data attributes for theme, position, colors, API URL
- **Responsive Design**: Mobile-first design with proper viewport handling
- **Error Handling**: Comprehensive error states and user feedback

### Widget Configuration Options
```html
<div id="whatsupdoc-widget"
     data-api-url="https://your-api.com"
     data-theme="light"
     data-position="bottom-right"
     data-title="Ask Our AI"
     data-placeholder="How can I help?"
     data-primary-color="#3B82F6">
</div>
<script src="https://your-api.com/static/widget/whatsupdoc-widget.js"></script>
```

### Widget Security Status
**⚠️ CURRENT STATE**: No authentication - open to any domain
- Widget sends `X-Widget-Origin` header (informational only)
- API accepts requests from any origin (CORS: `*`)
- Rate limiting: 10 requests/minute per IP
- **NEXT**: Domain whitelisting and API authentication (Phase 16)

### Build Process

#### ⚠️ CRITICAL: Widget Build Requirements
**ALWAYS rebuild the widget after source changes** - the widget uses a compiled build process:

- **Source**: `src/whatsupdoc/web/widget/src/whatsupdoc-widget.js` (human-readable)
- **Output**: `src/whatsupdoc/web/static/widget/whatsupdoc-widget.js` (minified for browsers)

**Common Issue**: Editing source without rebuilding results in stale builds where changes don't appear in browser.

```bash
# Development workflow
cd src/whatsupdoc/web/widget
npm install                    # One-time setup
npm run dev                   # Development server with hot reload (port 3000)
npm run build                 # Production build (outputs to ../static/widget/) - REQUIRED after changes
npm run watch                 # Rebuild automatically on source changes - RECOMMENDED for development

# Verification after changes
ls -la ../static/widget/       # Check that files were updated with recent timestamps
```

#### Development Best Practices
1. **Use Watch Mode**: Run `npm run watch` during development to auto-rebuild on changes
2. **Verify Builds**: Check file timestamps in `../static/widget/` after making changes
3. **Test Locally**: Use local test server to verify widget behavior after rebuilds
4. **Debug Console**: Widget includes console logging - check browser dev tools for debug output

#### Troubleshooting Build Issues
```bash
# If widget behavior doesn't match source code:
cd src/whatsupdoc/web/widget
npm run build                  # Force rebuild
ls -la ../static/widget/       # Verify output files are fresh

# Check for build errors:
npm run build -- --verbose    # Detailed build output

# Clean rebuild:
rm -rf ../static/widget/*      # Clear old builds
npm run build                  # Fresh build
```

#### Build Output Files
- `whatsupdoc-widget.js` - Minified UMD build (CSS inlined)
- `whatsupdoc-widget.js.map` - Source maps for debugging (preserves original line numbers)

**Note**: No separate CSS files are generated - all styles are inlined into the JS bundle by Vite.

# Testing with Playwright MCP
# Use browser automation to test widget functionality in real browsers
# Validates: auto-initialization, FAB clicks, chat functionality, API integration
```

### Integration Testing
- **Playwright MCP**: Browser automation for full widget testing
- **Real Browser Testing**: Validates actual DOM manipulation and user interactions
- **API Integration**: Tests full chat flow with RAG responses
- **Cross-browser Compatibility**: Chrome, Firefox, Safari, Edge support
