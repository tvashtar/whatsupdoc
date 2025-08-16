# Project Context: Multi-Interface RAG System

## Project Overview
This is a multi-interface RAG (Retrieval-Augmented Generation) system that allows users to query a company knowledge base (1000 PDFs) using natural language. The system uses Google Cloud's Vertex AI RAG Engine for proper chunk-based retrieval and Gemini for answer generation, with multiple interfaces and deployment options.

## Architecture
- **Knowledge Base**: Vertex AI RAG Engine (handles document ingestion, chunking, embedding, and retrieval)
- **Answer Generation**: Gemini API for RAG-based response generation
- **Interfaces**:
  - Slack bot responding to mentions and slash commands
  - Web API (FastAPI) for programmatic access
  - Gradio admin interface for testing and management
- **Hosting**: Cloud Run (serverless, auto-scaling)
- **Language**: Python with Slack Bolt framework and FastAPI

## Core Files Implemented

### Slack Bot
- `src/whatsupdoc/slack/app.py` - Main Slack bot application
- `src/whatsupdoc/slack/handlers.py` - Slack event handlers

### Web Interface
- `src/whatsupdoc/web/api.py` - FastAPI REST API
- `src/whatsupdoc/web/app.py` - Gradio admin interface launcher
- `src/whatsupdoc/web/gradio_interface.py` - Gradio interface components
- `src/whatsupdoc/web/service.py` - Unified web RAG service
- `src/whatsupdoc/web/models.py` - API request/response models
- `src/whatsupdoc/web/config.py` - Web-specific configuration

### Core RAG Components
- `src/whatsupdoc/core/vertex_rag_client.py` - Vertex AI RAG Engine integration
- `src/whatsupdoc/core/gemini_rag.py` - Gemini RAG answer generation
- `src/whatsupdoc/core/config.py` - Configuration management

### Infrastructure
- `pyproject.toml` - Python dependencies and project configuration
- `Dockerfile` - For Cloud Run deployment
- `.env` - Environment variables (configured, and gitignored)
- `scripts/launch_web.py` - Web interface launcher script
- `tests/` - Comprehensive test suite

## Key Features

### 1. **Slack Bot Interface**:
   - Handle @mentions (`@KnowledgeBot what is our PTO policy?`)
   - Handle slash commands (`/ask what is our PTO policy?`)
   - Handle DMs (direct messages)
   - Rich response formatting with Slack blocks
   - Loading messages for better UX
   - Error handling with user-friendly messages

### 2. **Web API (FastAPI)**:
   - RESTful API endpoints (`/api/chat`, `/api/health`)
   - JSON request/response format
   - Rate limiting (10 requests/minute per IP)
   - CORS support for web frontends
   - OpenAPI/Swagger documentation at `/api/docs`
   - Structured error handling

### 3. **Gradio Admin Interface**:
   - Web-based testing interface at `http://localhost:7860`
   - Basic authentication with configurable credentials
   - Interactive query testing with adjustable parameters
   - Real-time results display (answer, confidence, sources)
   - Connection testing for service health checks
   - Processing time monitoring

### 4. **Vertex AI RAG Engine Integration**:
   - Natural language query processing
   - Proper chunk-based document retrieval
   - Full document context (not just snippets)
   - Confidence scoring based on relevance
   - Efficient embedding-based search

### 5. **Advanced Features**:
   - Query preprocessing and optimization
   - Conversation context tracking
   - Configurable result limits and confidence thresholds
   - Unified service layer for all interfaces
   - Comprehensive logging and monitoring

## Current Status
**✅ COMPLETED**: Multi-interface RAG system with Slack bot, Web API, and admin interface
**✅ DEPLOYED**: Slack bot running on Cloud Run
**✅ WORKING**: True RAG generation with complete Gemini integration across all interfaces
**✅ OPTIMIZED**: Auto-scaling with scale-to-zero for cost efficiency

## Quick Start

### Development Setup
```bash
# Install dependencies
uv sync                        # Install all dependencies (main + dev)
uv run pre-commit install      # Set up automated code quality checks

# Run tests
uv run pytest
```

### Running Interfaces

#### Slack Bot
```bash
uv run whatsupdoc             # Start Slack bot locally
```

#### Web API (FastAPI)
```bash
python scripts/launch_web.py  # Start FastAPI server on port 8000
# Access API docs: http://localhost:8000/api/docs
```

#### Gradio Admin Interface
```bash
uv run python src/whatsupdoc/web/app.py  # Start Gradio on port 7860
# Access interface: http://localhost:7860
# Credentials: Set GRADIO_ADMIN_USERNAME/GRADIO_ADMIN_PASSWORD in .env
```

## Documentation
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Cloud Run deployment, IAM permissions, environment setup
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development workflow, testing, dependency management
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Implementation history and lessons learned
- **[TODO.md](docs/TODO.md)** - Comprehensive project roadmap and completed features, this is gitignored

## Success Criteria (Met)
- ✅ Bot responds to queries within 5 seconds
- ✅ Returns relevant results for 90%+ of queries
- ✅ Handles 100+ queries per day without issues
- ✅ Clear source attribution for all answers
- ✅ Graceful error handling
