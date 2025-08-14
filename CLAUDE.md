# Project Context: Slack RAG Chatbot

## Project Overview
This is a Slack bot that allows employees to query a company knowledge base (1000 PDFs) using natural language. The bot uses Google Cloud's Vertex AI RAG Engine for proper chunk-based retrieval and Gemini for answer generation, deployed on Cloud Run.

## Architecture
- **Knowledge Base**: Vertex AI RAG Engine (handles document ingestion, chunking, embedding, and retrieval)
- **Answer Generation**: Gemini API for RAG-based response generation
- **Interface**: Slack bot responding to mentions and slash commands
- **Hosting**: Cloud Run (serverless, auto-scaling)
- **Language**: Python with Slack Bolt framework

## Core Files Implemented
- `src/whatsupdoc/app.py` - Main Slack bot application
- `src/whatsupdoc/vertex_rag_client.py` - Vertex AI RAG Engine integration
- `src/whatsupdoc/gemini_rag.py` - Gemini RAG answer generation
- `src/whatsupdoc/config.py` - Configuration management
- `pyproject.toml` - Python dependencies and project configuration
- `Dockerfile` - For Cloud Run deployment
- `.env` - Environment variables (configured, and gitignored)
- `tests/` - Comprehensive test suite

## Key Features
1. **Slack Bot Features**:
   - Handle @mentions (`@KnowledgeBot what is our PTO policy?`)
   - Handle slash commands (`/ask what is our PTO policy?`)
   - Handle DMs (direct messages)
   - Rich response formatting with Slack blocks
   - Loading messages for better UX
   - Error handling with user-friendly messages

2. **Vertex AI RAG Engine Integration**:
   - Natural language query processing
   - Proper chunk-based document retrieval
   - Full document context (not just snippets)
   - Confidence scoring based on relevance
   - Efficient embedding-based search

3. **Advanced Features**:
   - Query preprocessing and optimization
   - Conversation context tracking
   - Rate limiting (max 10 queries per user per minute)
   - Grounded generation toggle
   - Configurable result limits and confidence thresholds

## Current Status
**✅ COMPLETED**: Full-featured Slack RAG bot deployed to production
**✅ DEPLOYED**: Running on Cloud Run at https://whatsupdoc-slack-bot-530988540591.us-central1.run.app
**✅ WORKING**: True RAG generation with complete Gemini integration
**✅ OPTIMIZED**: Auto-scaling with scale-to-zero for cost efficiency

## Quick Start
```bash
# Development setup
uv sync                        # Install all dependencies (main + dev)
uv run pre-commit install      # Set up automated code quality checks

# Run locally
uv run whatsupdoc

# Run tests
uv run pytest
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
