# What's Up Doc? 🤖

A production-ready Slack RAG chatbot that allows employees to query your company knowledge base using natural language. Built with Google Cloud's Vertex AI RAG Engine for document retrieval and Gemini for answer generation.

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

**Components:**
- **Knowledge Base**: Vertex AI RAG Engine (handles document ingestion, chunking, embedding, and retrieval)
- **Answer Generation**: Gemini 2.5 Flash Lite for RAG-based response generation
- **Interface**: Slack bot responding to @mentions, slash commands, and DMs
- **Auto-Ingest**: Cloud Function for automatic document processing from GCS uploads
- **Document Storage**: Google Cloud Storage bucket with automatic processing triggers
- **Hosting**: Google Cloud Run (serverless, auto-scaling, scale-to-zero)
- **Language**: Python 3.11 with Slack Bolt framework and Flask for HTTP mode

## 📋 Features

- 🔍 Natural language search across 1000+ PDF documents
- 💬 Multiple interaction methods:
  - @mentions: `@KnowledgeBot what is our PTO policy?`
  - Slash commands: `/ask what is our remote work policy?`
- 📚 Rich responses with source attribution and confidence scores
- ⚡ Responses within 5 seconds
- 🛡️ Rate limiting and error handling
- 📊 Conversation context for follow-up questions
- 🔄 **Auto-document ingestion** from GCS bucket uploads
- 📁 **Multi-format support** (PDF, DOCX, TXT, HTML, MD)
- 🎯 **True RAG generation** with 100k+ character context
- 💰 **Scale-to-zero cost optimization** when idle

## 💰 Cost Optimization

**Scale-to-zero architecture**: Near-$0 cost when idle (~$0.02-0.10/month for document storage), pay-per-use during active queries. Perfect for cost-effective production deployments.

## 🚀 Quick Start

```bash
# 1. Setup development environment
uv sync
cp .env.example .env  # Edit with your credentials

# 2. Run locally
uv run whatsupdoc

# 3. Run tests
uv run pytest
```

**For complete setup instructions**, including Google Cloud configuration, Slack app setup, and deployment, see:

- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Local development setup and workflow
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment to Cloud Run


## 📚 Usage Examples

Once deployed, your team can interact with the bot in several ways:

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


## 📚 Documentation

- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Local development setup, testing, code quality
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment and configuration
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Implementation history and lessons learned

## 📈 Performance

- ⚡ Response time < 5 seconds
- 🎯 46,000+ character context for comprehensive answers
- 📊 Scale-to-zero cost optimization
- 🔒 Enterprise-grade security with least privilege
