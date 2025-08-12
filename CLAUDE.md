# Project Context: Slack RAG Chatbot

## Project Overview
This is a Slack bot that allows employees to query a company knowledge base (1000 PDFs) using natural language. The bot uses Google Cloud's Vertex AI RAG Engine for proper chunk-based retrieval and Gemini for answer generation, deployed on Cloud Run.

## Architecture
- **Knowledge Base**: Vertex AI RAG Engine (handles document ingestion, chunking, embedding, and retrieval)
- **Answer Generation**: Gemini API for RAG-based response generation
- **Interface**: Slack bot responding to mentions and slash commands  
- **Hosting**: Cloud Run (serverless, auto-scaling)
- **Language**: Python with Slack Bolt framework

## My Implementation Scope
I need to implement the code in **Section 2** of the PRD:

### Core Files Implemented:
- `src/whatsupdoc/app.py` - Main Slack bot application
- `src/whatsupdoc/vertex_rag_client.py` - Vertex AI RAG Engine integration  
- `src/whatsupdoc/gemini_rag.py` - Gemini RAG answer generation
- `src/whatsupdoc/config.py` - Configuration management
- `pyproject.toml` - Python dependencies and project configuration
- `Dockerfile` - For Cloud Run deployment
- `.env` - Environment variables (configured)
- `tests/` - Comprehensive test suite

### Key Features to Implement:
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

4. **Deployment & Testing**:
   - Production-ready Dockerfile
   - Cloud Run deployment configuration
   - Unit and integration tests
   - Monitoring and logging setup

## Environment Variables:
**CONFIGURED**: The `.env` file contains all required environment variables:
- **GCP credentials**: PROJECT_ID, LOCATION, RAG_CORPUS_ID
- **Slack tokens**: SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN
- **RAG configuration**: ENABLE_RAG_GENERATION, MAX_CONTEXT_LENGTH, ANSWER_TEMPERATURE
- **Gemini settings**: GEMINI_MODEL, USE_VERTEX_AI
- **Feature settings**: MAX_RESULTS, RESPONSE_TIMEOUT
- **Google Cloud auth**: Using Application Default Credentials (ADC)

## Setup Status:
**COMPLETED**: User has successfully:
- ✅ Created Vertex AI RAG Engine corpus with 1000 PDFs
- ✅ Configured Slack app with proper permissions
- ✅ Set up all required environment variables
- ✅ Tested RAG Engine functionality in AI Studio
- ✅ Deployed to Cloud Run successfully
- ✅ Bot is live and responding to queries

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
uv run tests/test_rag_engine_connection.py
uv run tests/test_gemini_integration.py
uv run tests/test_slack_connection.py

# Run all tests
uv run tests/run_all_tests.py

# Run the bot
uv run whatsupdoc
```

## Testing Status:
✅ **IMPLEMENTED**: Complete test suite covering:
- RAG Engine connection and search functionality
- Gemini integration and response generation
- Slack bot configuration and API connection
- Package imports and dependencies
- GCP authentication and access

## Cloud Run Deployment

### Prerequisites - Required IAM Permissions
Before deploying, ensure these IAM roles are granted to the appropriate service accounts:

```bash
# Grant permissions to Cloud Build service account (PROJECT_NUMBER@cloudbuild.gserviceaccount.com)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Grant permissions to Compute Engine default service account (PROJECT_NUMBER-compute@developer.gserviceaccount.com)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com run.googleapis.com

# Create Artifact Registry repository for Cloud Build
gcloud artifacts repositories create cloud-run-source-deploy \
  --repository-format=docker \
  --location=us-central1 \
  --description="Cloud Run source deployments"
```

### Deployment Command
```bash
gcloud run deploy whatsupdoc-slack-bot \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --memory 1Gi \
  --cpu 2 \
  --timeout 60 \
  --service-account rag-bot-sa@PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars "PROJECT_ID=PROJECT_ID,LOCATION=us-central1,RAG_CORPUS_ID=YOUR_RAG_CORPUS_ID,SLACK_BOT_TOKEN=xoxb-xxx,SLACK_SIGNING_SECRET=xxx,USE_GROUNDED_GENERATION=True,MAX_RESULTS=5,RESPONSE_TIMEOUT=30,BOT_NAME=whatsupdoc,RATE_LIMIT_PER_USER=10,RATE_LIMIT_WINDOW=60,GEMINI_MODEL=gemini-2.5-flash-lite,USE_VERTEX_AI=True,ENABLE_RAG_GENERATION=True,MAX_CONTEXT_LENGTH=100000,ANSWER_TEMPERATURE=0.1" \
  --quiet
```

### Slack App Configuration for Cloud Run
After deployment, configure your Slack app:
1. **Disable Socket Mode** (Settings → Socket Mode → Toggle OFF)
2. **Configure Event Subscriptions**:
   - Enable Events
   - Request URL: `https://YOUR-SERVICE-URL.run.app/slack/events`
   - Subscribe to bot events: `app_mention`, `message.channels`, `message.groups`, `message.im`, `message.mpim`
3. **Update Slash Commands**:
   - Set `/ask` command URL to: `https://YOUR-SERVICE-URL.run.app/slack/events`
4. **Update Interactivity & Shortcuts** (if used):
   - Request URL: `https://YOUR-SERVICE-URL.run.app/slack/events`

## Implementation Lessons Learned

### 1. Slack Bolt Async/Sync Issues
**Problem**: Mixing async functions with Slack Bolt event handlers causes "dispatch_failed" errors.
**Solution**: Use synchronous event handlers and wrap async calls with `asyncio.run()`:
```python
# ❌ Don't do this
@self.app.command("/ask")
async def handle_ask_command(ack, respond, command, client):
    await ack()
    # async code here

# ✅ Do this instead
@self.app.command("/ask")
def handle_ask_command(ack, respond, command, client):
    ack()
    asyncio.run(self._handle_async_logic(command, respond, client))
```

### 2. Socket Mode OAuth Configuration
**Problem**: Having `SLACK_CLIENT_ID` and `SLACK_CLIENT_SECRET` in environment triggers OAuth mode, causing authorization failures.
**Solution**: For Socket Mode, only use `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`. Comment out OAuth variables in `.env`.

### 3. Google Protobuf Data Structures
**Problem**: Vertex AI Search returns protobuf `RepeatedComposite` and `MapComposite` objects that don't behave like regular Python lists/dicts.
**Solution**: Convert and access properly:
```python
# Convert RepeatedComposite to list
snippets_list = list(derived_data["snippets"])
# Access MapComposite with bracket notation
snippet_content = first_snippet["snippet"]
```

### 4. Slack Response Function Consistency
**Problem**: Different Slack event types (`say`, `respond`, `client.chat_update`) have different async/sync behaviors.
**Solution**: Don't await these functions when called from synchronous handlers. They return immediately in sync context.

### 5. Vertex AI Search Configuration Paths
**Problem**: Vertex AI Search has two different serving config path formats that may work differently.
**Solution**: Implement fallback logic:
```python
# Try data store path first
serving_config = f"projects/{project_id}/locations/{location}/dataStores/{data_store_id}/servingConfigs/default_config"
# Fallback to app path
app_serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{app_id}/servingConfigs/default_config"
```

### 6. RAG Engine Migration & Optimization
**Problem**: Using Discovery Engine with snippet-based search limited chunks to ~50 tokens each.
**Solution**: Migrated to Vertex AI RAG Engine for proper chunk-based retrieval with 4000-5000+ character chunks.

### 7. Context Length Optimization
**Problem**: Context limit of 8,000 characters was preventing all retrieved chunks from being passed to Gemini.
**Solution**: Increased to 100,000 characters, allowing all 5 chunks (~20k total) to be passed for comprehensive answers.

### 8. Model Optimization
**Problem**: Using older Gemini 2.0 Flash model.
**Solution**: Upgraded to Gemini 2.5 Flash Lite for better performance and lower cost.

### 9. Cloud Run Deployment Challenges
**Problem**: Bot worked locally with Socket Mode but failed on Cloud Run.
**Solutions**:
- Modified bot to support both Socket Mode (local dev) and HTTP mode (Cloud Run)
- Made SLACK_APP_TOKEN optional when PORT env var is set (Cloud Run mode)
- Fixed .dockerignore and .gcloudignore to include README.md needed for pip install
- Changed Dockerfile CMD from `python -m whatsupdoc` to `whatsupdoc` entry point

### 10. Current Status & Achievement
**✅ COMPLETED**: Full-featured Slack RAG bot deployed to production
**✅ DEPLOYED**: Running on Cloud Run at https://whatsupdoc-slack-bot-530988540591.us-central1.run.app
**✅ WORKING**: True RAG generation with complete Gemini integration
**✅ FIXED**: All major issues resolved:
- ✅ Confidence scoring now uses actual relevance scores (not hardcoded 50%)
- ✅ All 5 chunks (20k+ characters) passed to Gemini for superior answer quality
- ✅ Using optimized Gemini 2.5 Flash Lite model
- ✅ Proper chunk-based retrieval from RAG Engine
- ✅ Comprehensive error handling and debugging
- ✅ Socket Mode for local dev, HTTP mode for Cloud Run
- ✅ Auto-scaling with scale-to-zero for cost efficiency