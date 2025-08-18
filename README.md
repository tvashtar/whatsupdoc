# What's Up Doc? 🤖

A production-ready multi-interface RAG system that allows employees to query your company knowledge base using natural language. Features Slack bot, Web API, and admin interfaces. Built with Google Cloud's Vertex AI RAG Engine for document retrieval and Gemini for answer generation.

**Status**: ✅ Deployed and running in production with comprehensive documentation

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     Slack       │    │   Cloud Run      │    │  Google Cloud   │
│                 │    │                  │    │                 │
│  @mentions      │───▶│  WhatsUpDoc Bot  │───▶│  Vertex AI      │
│  /ask commands  │    │                  │    │  RAG Engine     │
│  DMs            │    │  • Query proc.   │    │                 │
│                 │    │  • RAG retrieval │    │  • 1000+ PDFs   │
│                 │    │  • Answer gen.   │◀───│  • Chunking     │
│                 │◀───│  • Response fmt. │    │  • Embeddings   │
│  Rich responses │    │                  │    │  • Search       │
│  w/ sources     │    │  Python 3.11     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │    ▲                    │
                              ▼    │                    ▼
                       ┌──────────────────┐    ┌──────────────────┐
                       │     Gemini       │    │  Auto-Ingest     │
                       │  2.5 Flash Lite  │    │  Cloud Function  │
                       │                  │    │                  │
                       │  • RAG synthesis │    │  • GCS Trigger   │
                       │  • Answer gen.   │    │  • Auto-chunking │
                       │  • Citations     │    │  • RAG Import    │
                       └──────────────────┘    └──────────────────┘
                                                        ▲
                                                        │
                                               ┌──────────────────┐
                                               │  GCS Bucket      │
                                               │  Document Store  │
                                               │                  │
                                               │  • File uploads  │
                                               │  • Auto-detect   │
                                               │  • Multi-format  │
                                               └──────────────────┘
```

### Widget Integration Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Website       │    │   Cloud Run      │    │  Google Cloud   │
│                 │    │                  │    │                 │
│  Embedded       │───▶│  FastAPI Server  │───▶│  Vertex AI      │
│  JS Widget      │    │                  │    │  RAG Engine     │
│                 │    │  • CORS security │    │                 │
│  • FAB button   │    │  • Rate limiting │    │  • 1000+ PDFs   │
│  • Chat modal   │    │  • Origin valid. │◀───│  • Chunking     │
│  • Real-time    │◀───│  • API endpoints │    │  • Embeddings   │
│  • Mobile resp. │    │                  │    │  • Search       │
│                 │    │  Python 3.11     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                      │    ▲
         │                      ▼    │
┌─────────────────┐    ┌──────────────────┐
│  GCS CDN        │    │     Gemini       │
│                 │    │  2.5 Flash Lite  │
│  Widget delivery│    │                  │
│  • Minified JS  │    │  • RAG synthesis │
│  • Source maps  │    │  • Answer gen.   │
│  • Cache headers│    │  • Citations     │
└─────────────────┘    └──────────────────┘
```

**Components:**
- **Knowledge Base**: Vertex AI RAG Engine (handles document ingestion, chunking, embedding, and retrieval)
- **Answer Generation**: Gemini 2.5 Flash Lite for RAG-based response generation
- **Interfaces**:
  - Slack bot responding to @mentions, slash commands, and DMs
  - FastAPI REST API for programmatic access
  - Gradio admin interface for testing and management
  - **Embeddable JavaScript widget** for any website (NEW!)
- **Auto-Ingest**: Cloud Function for automatic document processing from GCS uploads
- **Document Storage**: Google Cloud Storage bucket with automatic processing triggers
- **Hosting**: Google Cloud Run (serverless, auto-scaling, scale-to-zero)
- **Language**: Python 3.11 with Slack Bolt framework, FastAPI, and Gradio

## 📋 Features

### 🔍 **Core RAG Capabilities**
- Natural language search across 1000+ PDF documents
- True RAG generation with 100k+ character context
- Rich responses with source attribution and confidence scores
- Responses within 5 seconds
- Auto-document ingestion from GCS bucket uploads
- Multi-format support (PDF, DOCX, TXT, HTML, MD)

### 💬 **Multiple Interfaces**

**Slack Bot:**
- @mentions: `@KnowledgeBot what is our PTO policy?`
- Slash commands: `/ask what is our remote work policy?`
- Direct messages for private queries
- Rich response formatting with Slack blocks

**Embeddable Widget:**
- Modern JavaScript Web Component with Shadow DOM
- One-line integration: `<script src="your-domain/static/widget/whatsupdoc-widget.js"></script>`
- Customizable themes (light/dark), positions, and colors
- Mobile-responsive with elegant floating chat interface
- Rate limiting protection and conversation history
- Works on any website without CSS conflicts

**Web API (FastAPI):**
- RESTful endpoints (`/api/chat`, `/api/health`)
- OpenAPI/Swagger documentation at `/api/docs`
- Rate limiting (10 requests/minute per IP)
- CORS support for frontend integration

**Gradio Admin Interface:**
- Web-based testing at `http://localhost:7860`
- Interactive query testing with adjustable parameters
- Real-time results display and service health checks
- Basic authentication for secure access

### 🛡️ **Production Features**
- Rate limiting and comprehensive error handling
- Conversation context for follow-up questions
- Scale-to-zero cost optimization when idle
- Enterprise-grade security with least privilege

## 💰 Cost Optimization

**Scale-to-zero architecture**: Near-$0 cost when idle (~$0.02-0.10/month for document storage), pay-per-use during active queries. Perfect for cost-effective production deployments.

## 🚀 Quick Start

### Development Setup
```bash
# 1. Setup environment
uv sync                        # Install dependencies
cp .env.example .env          # Edit with your credentials
uv run pre-commit install     # Set up code quality checks

# 2. Run tests
uv run pytest
```

### Running Interfaces

#### Slack Bot
```bash
uv run whatsupdoc             # Start Slack bot locally
```

#### Web API (FastAPI)
```bash
python scripts/launch_web.py  # Start on port 8000
# Access docs: http://localhost:8000/api/docs
```

#### Gradio Admin Interface
```bash
uv run python src/whatsupdoc/web/app.py  # Start on port 7860
# Access interface: http://localhost:7860
# Credentials: Set GRADIO_ADMIN_USERNAME/GRADIO_ADMIN_PASSWORD in .env
```

**For complete setup instructions**, including Google Cloud configuration, Slack app setup, and deployment, see:

- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Local development setup and workflow
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment to Cloud Run


## 📚 Usage Examples

### Slack Bot Interactions

**@Mentions in channels:**
```
@KnowledgeBot what is our remote work policy?
@KnowledgeBot how do I submit expenses?
```

**Slash commands:**
```
/ask what are the company holidays this year?
/ask who do I contact for IT support?
```

### Web API Usage

**REST API calls:**
```bash
# Health check
curl http://localhost:8000/api/health

# Chat query
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is our PTO policy?"}'
```

### Gradio Admin Interface

Access the web interface at `http://localhost:7860` to:
- Test queries interactively
- Adjust confidence thresholds and result limits
- Monitor service health and performance
- View detailed responses with source attribution


## 📚 Documentation

- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Local development setup, testing, code quality
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment and configuration
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Implementation history and lessons learned

## 📈 Performance

- ⚡ Response time < 5 seconds
- 🎯 46,000+ character context for comprehensive answers
- 📊 Scale-to-zero cost optimization
- 🔒 Enterprise-grade security with least privilege
