# Project Context: Slack RAG Chatbot

## Project Overview
This is a Slack bot that allows employees to query a company knowledge base (1000 PDFs) using natural language. The bot uses Google Cloud's Vertex AI Search for RAG capabilities and is deployed on Cloud Run.

## Architecture
- **Knowledge Base**: Vertex AI Search (handles ingestion, embedding, retrieval)
- **Interface**: Slack bot responding to mentions and slash commands  
- **Hosting**: Cloud Run (serverless, auto-scaling)
- **Language**: Python with Slack Bolt framework

## My Implementation Scope
I need to implement the code in **Section 2** of the PRD:

### Core Files to Create:
- `slack-rag-bot/app.py` - Main Slack bot application
- `slack-rag-bot/vertex_search.py` - Vertex AI Search integration
- `slack-rag-bot/config.py` - Configuration management
- `slack-rag-bot/requirements.txt` - Python dependencies
- `slack-rag-bot/Dockerfile` - For Cloud Run deployment
- `slack-rag-bot/.env.example` - Example environment variables
- `slack-rag-bot/README.md` - Setup and deployment instructions

### Key Features to Implement:
1. **Slack Bot Features**:
   - Handle @mentions (`@KnowledgeBot what is our PTO policy?`)
   - Handle slash commands (`/ask what is our PTO policy?`)
   - Handle DMs (direct messages)
   - Rich response formatting with Slack blocks
   - Loading messages for better UX
   - Error handling with user-friendly messages

2. **Vertex AI Search Integration**:
   - Natural language query processing
   - API calls to Vertex AI Search
   - Result formatting with snippets and sources
   - Confidence scoring
   - Pagination support

3. **Advanced Features**:
   - Query preprocessing and optimization
   - Conversation context tracking
   - Rate limiting (max 10 queries per user per minute)
   - Grounded generation toggle
   - Configurable result limits and confidence thresholds

4. **Deployment & Testing**:
   - Production-ready Dockerfile
   - Cloud Run deployment configuration
   - Unit and integration tests
   - Monitoring and logging setup

## Environment Variables:
**IMPORTANT**: The user has created a `.env` file in the project root with all required environment variables. Reference this file during implementation - it contains all the actual values I need for:
- GCP credentials (PROJECT_ID, LOCATION, DATA_STORE_ID, APP_ID)
- Slack tokens (SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET) 
- Feature configuration (USE_GROUNDED_GENERATION, MAX_RESULTS, RESPONSE_TIMEOUT)
- Google Cloud auth: User is using Application Default Credentials (ADC) locally

The `.env` file is ready with all actual credentials populated. The user has completed all manual setup steps from Section 1 of the PRD.

## User's Responsibilities:
The user handles all GCP console setup (Section 1) and post-deployment tasks (Section 3):
- Setting up Vertex AI Search with PDF ingestion
- Creating Slack app and configuring permissions
- Setting up service accounts and IAM
- Post-deployment: adding bot to channels, monitoring

## Success Criteria:
- Bot responds to queries within 5 seconds
- Returns relevant results for 90%+ of queries  
- Handles 100+ queries per day without issues
- Clear source attribution for all answers
- Graceful error handling

## Development Commands:
Use `uv` for all Python development tasks:

```bash
# Install dependencies
uv sync

# Run verification tests
uv run tests/test_gcp_connection.py
uv run tests/test_slack_connection.py

# Run the bot (once implemented)
uv run slack-rag-bot/app.py

# Run tests (once implemented)
uv run -m pytest tests/
```

## Testing Commands:
After implementation, I should run:
- Unit tests for search functionality
- Integration tests with test data store
- Slack message formatting tests
- Error handling scenarios
- Rate limiting tests

## Deployment Commands:
```bash
gcloud run deploy slack-rag-bot \
  --source . \
  --region us-central1 \
  --service-account rag-bot-sa@PROJECT-ID.iam.gserviceaccount.com \
  --set-env-vars-from-file .env.production \
  --min-instances 0 \
  --max-instances 10
```
- remember to use uv and uv run where needed