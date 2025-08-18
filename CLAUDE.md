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
  - Embeddable JavaScript widget for public websites
- **Hosting**: Cloud Run (serverless, auto-scaling)
- **Static Assets**: Google Cloud Storage for widget and demo files
- **Language**: Python with Slack Bolt framework, FastAPI, and modern JavaScript
- **Security**: CORS validation, origin verification, and rate limiting

## Core Files Implemented

### Slack Bot
- `src/whatsupdoc/slack/app.py` - Main Slack bot application
- `src/whatsupdoc/slack/handlers.py` - Slack event handlers

### Web Interface
- `src/whatsupdoc/web/api.py` - FastAPI REST API with CORS and security middleware
- `src/whatsupdoc/web/app.py` - Gradio admin interface launcher
- `src/whatsupdoc/web/gradio_interface.py` - Gradio interface components
- `src/whatsupdoc/web/service.py` - Unified web RAG service
- `src/whatsupdoc/web/models.py` - API request/response models
- `src/whatsupdoc/web/config.py` - Web-specific configuration
- `src/whatsupdoc/web/middleware.py` - Origin validation and security middleware

### Widget & Static Assets
- `src/whatsupdoc/web/widget/src/whatsupdoc-widget.js` - JavaScript widget source
- `src/whatsupdoc/web/static/widget/` - Built widget files (minified)
- `src/whatsupdoc/web/static/demo.html` - Widget demonstration page
- `scripts/deploy_static.sh` - Automated GCS deployment script

### Core RAG Components
- `src/whatsupdoc/core/vertex_rag_client.py` - Vertex AI RAG Engine integration
- `src/whatsupdoc/core/gemini_rag.py` - Gemini RAG answer generation
- `src/whatsupdoc/core/config.py` - Configuration management

### Infrastructure
- `pyproject.toml` - Python dependencies and project configuration
- `Dockerfile` - Multi-mode Cloud Run deployment (Slack bot + Web API)
- `.env` - Environment variables (configured, and gitignored)
- `scripts/launch_web.py` - Web interface launcher script
- `scripts/deploy_static.sh` - Automated static asset deployment to GCS
- `scripts/wsgi_web.py` - Web API WSGI entry point for production
- `tests/` - Comprehensive test suite including CORS validation

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
   - CORS validation with specific origin allowlist
   - Origin validation middleware for enhanced security
   - OpenAPI/Swagger documentation at `/api/docs`
   - Structured error handling with request tracking

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
   - Distance-based filtering with configurable thresholds
   - Efficient embedding-based search

### 5. **Embeddable JavaScript Widget**:
   - Modern Web Components with Shadow DOM for style isolation
   - One-line integration for any website
   - Floating Action Button (FAB) with customizable positioning
   - Real-time RAG responses with loading states and error handling
   - Theme support (light/dark) and customizable colors
   - Mobile-responsive design with proper viewport handling
   - Conversation persistence with localStorage
   - Production-ready with CDN deployment on Google Cloud Storage

### 6. **Advanced Features**:
   - Query preprocessing and optimization
   - Conversation context tracking
   - Configurable result limits and distance thresholds (env: `DISTANCE_THRESHOLD=0.8`)
   - Single-point filtering at Vertex AI level (no redundant filtering)
   - Unified service layer for all interfaces
   - Comprehensive logging and monitoring
   - Production security with CORS validation and origin verification

## Current Status
**✅ COMPLETED**: Multi-interface RAG system with Slack bot, Web API, admin interface, and embeddable widget
**✅ DEPLOYED**: Production deployment on Cloud Run with static assets on Google Cloud Storage
**✅ SECURED**: CORS validation, origin verification, and comprehensive security middleware
**✅ WORKING**: True RAG generation with complete Gemini integration across all interfaces
**✅ OPTIMIZED**: Auto-scaling with scale-to-zero for cost efficiency
**✅ REFACTORED**: Simplified single distance threshold filtering (Aug 2024)

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

#### Widget Development
```bash
cd src/whatsupdoc/web/widget
npm install                               # Install widget dependencies (one-time)
npm run dev                              # Development server with hot reload (port 3000)
npm run build                            # Build widget for production
npm run watch                            # Build widget in watch mode
# Demo page: http://localhost:8000/static/demo.html
```

#### Static Asset Deployment
```bash
bash scripts/deploy_static.sh           # Deploy widget and demo to Google Cloud Storage
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
