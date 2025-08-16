# Deployment Guide

## Cloud Run Deployment

### Quick Deploy (Using Script)
For convenience, you can use the automated deploy script:

```bash
# Ensure .env file is configured with all required variables
bash scripts/deploy.sh
```

The script reads environment variables from `.env` and handles the deployment automatically.

### Manual Deploy (Using gcloud CLI)

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

# Grant permissions to RAG Bot service account (for semantic ranking and RAG functionality)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:rag-bot-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Required for semantic reranking (semantic-ranker-default@latest)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:rag-bot-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/discoveryengine.viewer"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:rag-bot-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

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

## Environment Variables

**CONFIGURED**: The `.env` file contains all required environment variables:
- **GCP credentials**: PROJECT_ID, LOCATION, RAG_CORPUS_ID
- **Slack tokens**: SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN
- **RAG configuration**: ENABLE_RAG_GENERATION, MAX_CONTEXT_LENGTH, ANSWER_TEMPERATURE
- **Gemini settings**: GEMINI_MODEL, USE_VERTEX_AI
- **Feature settings**: MAX_RESULTS, RESPONSE_TIMEOUT
- **Google Cloud auth**: Using Application Default Credentials (ADC)

## Docker Production Optimization

### Lock File Usage
- `COPY uv.lock` ensures reproducible builds across environments
- `uv sync --frozen --no-dev --no-cache` excludes pytest, ruff, mypy from production
- `--no-cache` prevents bloating final image with unnecessary cache files
- `--frozen` skips dependency resolution using pre-computed lock file

## Web Interfaces (Development Only)

The project includes additional web interfaces for development and testing:

- **FastAPI REST API**: Not deployed to production (Slack bot only)
- **Gradio Admin Interface**: For local testing and development only
- **Local Usage**: See [DEVELOPMENT.md](DEVELOPMENT.md) for local setup instructions

These interfaces share the same RAG core but are intended for local development, testing, and administrative tasks.

### Current Status
**✅ DEPLOYED**: Slack bot running on Cloud Run
**✅ WORKING**: True RAG generation with complete Gemini integration across all interfaces
**✅ OPTIMIZED**: Auto-scaling with scale-to-zero for cost efficiency
