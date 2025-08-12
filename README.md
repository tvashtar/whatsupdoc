# What's Up Doc? 🤖

A production-ready Slack RAG (Retrieval-Augmented Generation) chatbot that allows employees to query company knowledge base using natural language. Built with Google Cloud's Vertex AI RAG Engine for document retrieval and Gemini for answer generation, deployed on Cloud Run for serverless auto-scaling.

**Ready for Production**: Complete implementation with deployment guides and testing suite!

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
  - Direct messages to the bot
- 📚 Rich responses with source attribution and confidence scores
- ⚡ Responses within 5 seconds
- 🛡️ Rate limiting and error handling
- 📊 Conversation context for follow-up questions
- 🔄 **Auto-document ingestion** from GCS bucket uploads
- 📁 **Multi-format support** (PDF, DOCX, TXT, HTML, MD)
- 🎯 **True RAG generation** with 100k+ character context
- 💰 **Scale-to-zero cost optimization** when idle

## 💰 Costs

This architecture **scales down to near-$0 cost** when not in use, making it ideal for reference implementations and low-traffic scenarios.

### ✅ True Scale-to-Zero Components
- **Cloud Run**: Bot application with `--min-instances 0`, only charged during active queries
- **Cloud Functions Gen2**: Auto-ingest function only charged during document processing
- **Eventarc Triggers**: No cost when idle, minimal per-event charges when active
- **Pub/Sub**: No cost when no messages flowing

### 💰 Minimal Fixed Costs (When Idle)
- **GCS Document Storage**: ~$0.020/GB/month for Standard storage
- **Vertex AI RAG Corpus Storage**: ~$0.020/GB/month for ingested/chunked documents
- **Cloud Logging**: 50GB free tier, then $0.50/GB (negligible for this use case)

### 📊 Estimated Monthly Cost When Idle
- **Total idle cost**: ~$0.02-0.10/month (assuming <5GB of documents)
- **Active usage**: Pay-per-use for:
  - Cloud Run execution time during queries
  - Cloud Function execution during document uploads
  - Gemini API calls for answer generation
  - RAG Engine API calls for document search
  - Eventarc event delivery

**Perfect for**: Reference implementations, development environments, and low-traffic production workloads that need to minimize costs while maintaining full functionality.

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- Slack workspace with admin access
- gcloud CLI installed and configured

### 1. Environment Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Follow the setup sections below to populate your `.env` file with the required values.

### 2. Google Cloud Setup

#### Enable Required APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
```

Or enable manually in the GCP Console:
1. Go to "APIs & Services" → "Library"
2. Enable:
   - Vertex AI API
   - Cloud Run API
   - Cloud Storage API

#### Create Cloud Storage Bucket for PDFs

1. **Create Bucket**:
   - Go to GCP Console → "Storage" → "Buckets" → "Create"
   - **Name**: Pick unique name (e.g., `company-knowledge-base-docs`)
   - **Location type**: Choose Region (same as your RAG Engine location)
   - **Storage class**: Standard
   - Leave other settings as defaults → Click "Create"

2. **Upload Your PDFs**:
   - Open your new bucket
   - Click "Upload Files" or "Upload Folder"
   - Add your company PDF documents
   - Wait for upload to complete

#### Create Vertex AI RAG Engine Corpus

1. **Navigate to Vertex AI**:
   - Go to GCP Console → "Vertex AI" → "RAG Engine"
   - Click "Create RAG Corpus"

2. **Configure RAG Corpus**:
   - **Name**: Enter a name (e.g., "whatsupdoc")
   - **Display Name**: Enter a display name
   - **Description**: Add a description
   - Click "Create"

3. **Import Documents**:
   - Once corpus is created, click "Import Files"
   - **Data source**: Choose "Cloud Storage"
   - Select the bucket with your PDFs
   - Configure chunking settings:
     - Chunk size: 512 tokens (recommended)
     - Chunk overlap: 100 tokens
   - Start import and wait for completion (10-30 minutes for 1000 PDFs)
   - **NOTE**: To add new documents later, you can either use the auto-ingest feature (recommended) or return here and repeat the import process

4. **Get Required Values for .env**:
   ```bash
   # Update these in your .env file:
   PROJECT_ID=your-actual-project-id           # From GCP Console
   LOCATION=us-central1                        # Or your chosen region
   RAG_CORPUS_ID=projects/PROJECT_ID/locations/LOCATION/ragCorpora/CORPUS_ID  # Full corpus resource name
   GCS_DOCUMENTS_BUCKET=your-bucket-name       # For auto-ingest feature
   ```

#### Create Service Account

1. **Create Service Account**:
```bash
gcloud iam service-accounts create rag-bot-sa \
  --display-name="RAG Bot Service Account" \
  --project=YOUR-PROJECT-ID
```

2. **Grant Required Permissions**:
```bash
# Vertex AI permissions for RAG Engine
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:rag-bot-sa@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Additional permission for RAG operations
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:rag-bot-sa@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.viewer"
```

3. **Service Account Authentication**:
   - **For Cloud Run deployment**: No JSON key needed! Cloud Run uses the service account directly via `--service-account` flag
   - **For local development only**: You can use Application Default Credentials:
   ```bash
   # Authenticate with your user account (for local testing)
   gcloud auth application-default login
   ```

**Note**: The deployment uses the service account directly without JSON keys, following Google Cloud security best practices.

### 3. Slack App Setup

#### Create Slack App

1. **Create New App**:
   - Go to [https://api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - **App Name**: Enter name (e.g., "Knowledge Bot" or "What's Up Doc")
   - **Workspace**: Select your workspace
   - Click "Create App"

#### Configure App Settings

2. **Enable Socket Mode** (do this first):
   - Go to "Socket Mode" → Toggle **Enable**
   - When prompted, create an App-Level Token:
     - **Token Name**: "socket-connection"
     - **Scopes**: Add `connections:write`
     - Click "Generate" and copy the token (starts with `xapp-`)
   - Update your `.env`: `SLACK_APP_TOKEN=xapp-your-actual-token`

3. **Configure Bot Token Scopes**:
   - Go to "OAuth & Permissions"
   - Scroll to "Scopes" → "Bot Token Scopes"
   - Click "Add an OAuth Scope" and add these scopes:
     - `app_mentions:read` (respond to @mentions)
     - `chat:write` (send messages)
     - `commands` (for slash commands)
     - `channels:history` (read channel messages)
     - `groups:history` (private channels)
     - `im:history` (direct messages)
     - `mpim:history` (group DMs)

4. **Install App to Workspace**:
   - Scroll up to "OAuth Tokens for Your Workspace"
   - Click "Install to Workspace"
   - Click "Allow" to authorize the permissions
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)
   - Update your `.env`: `SLACK_BOT_TOKEN=xoxb-your-actual-token`

5. **Get App Credentials**:
   - Go to "Basic Information" → "App Credentials"
   - Copy the **Signing Secret** → Update your `.env`: `SLACK_SIGNING_SECRET=your-signing-secret`

### 4. Verify Your Configuration

After completing the setup steps above, your `.env` file should look similar to this:

```bash
# GCP Settings (from your Vertex AI RAG Engine setup)
PROJECT_ID=your-project-id
LOCATION=us-central1
RAG_CORPUS_ID=projects/PROJECT_ID/locations/LOCATION/ragCorpora/CORPUS_ID

# Slack Settings (from your Slack app configuration)
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_APP_TOKEN=xapp-your-app-token-here

# Gemini Settings
GEMINI_MODEL=gemini-2.5-flash-lite
USE_VERTEX_AI=True

# RAG Generation Settings
ENABLE_RAG_GENERATION=True
MAX_CONTEXT_LENGTH=100000
ANSWER_TEMPERATURE=0.3

# Feature Configuration
USE_GROUNDED_GENERATION=True
MAX_RESULTS=5
RESPONSE_TIMEOUT=30

# Bot Configuration  
BOT_NAME=KnowledgeBot
RATE_LIMIT_PER_USER=10
RATE_LIMIT_WINDOW=60

# Auto-Ingest Configuration (optional)
GCS_DOCUMENTS_BUCKET=your-bucket-name
```

**✅ Configuration Complete!** Once all values are populated, you're ready to install dependencies and deploy the bot.

### 5. Auto-Ingest Setup (Optional)

To enable automatic document ingestion when files are uploaded to GCS:

```bash
# Deploy the auto-ingest Cloud Function
cd cloud-functions/auto-ingest
./deploy.sh
```

This creates a Cloud Function that automatically:
- Detects new document uploads to your GCS bucket
- Processes and chunks the documents
- Ingests them into your RAG corpus
- Makes them immediately searchable via the bot

Supported formats: PDF, DOCX, TXT, HTML, MD files.

## 🛠️ Development

### Setup Environment

1. **Install dependencies with uv**:
```bash
# Create virtual environment and install dependencies
uv sync
```

2. **Run locally (Socket Mode)**:
```bash
# Make sure your .env file contains all required variables
# The application will automatically load them

# Run the bot
uv run whatsupdoc
```

3. **Verify your setup**:
```bash
# Run all tests
uv run tests/run_all_tests.py

# Or run individual tests:
uv run tests/test_rag_engine_connection.py
uv run tests/test_gemini_integration.py
uv run tests/test_slack_connection.py
```

### Dual Mode Support

The bot supports two modes:
- **Socket Mode** (local development): Uses SLACK_APP_TOKEN for websocket connection
- **HTTP Mode** (Cloud Run): Uses Flask server listening on PORT environment variable

The bot automatically detects which mode to use based on the presence of the PORT environment variable.

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

**Direct messages:**
```
what is the process for requesting time off?
where can I find the employee handbook?
```

## 🔧 Configuration Options

All configuration is handled through environment variables in your `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_GROUNDED_GENERATION` | Enable grounded generation | `True` |
| `MAX_RESULTS` | Maximum search results to return | `5` |
| `RESPONSE_TIMEOUT` | Query timeout in seconds | `30` |
| `RATE_LIMIT_PER_USER` | Max queries per user | `10` |
| `RATE_LIMIT_WINDOW` | Rate limit window in seconds | `60` |
| `GCS_DOCUMENTS_BUCKET` | Auto-ingest source bucket | (optional) |
| `MAX_CONTEXT_LENGTH` | Max characters for Gemini | `100000` |
| `GEMINI_MODEL` | Gemini model version | `gemini-2.5-flash-lite` |

## 🚀 Deployment to Cloud Run

### Prerequisites - Required IAM Permissions

Before deploying, ensure the necessary service accounts have proper permissions:

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format='value(projectNumber)')

# Grant permissions to Cloud Build service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Grant permissions to Compute Engine default service account  
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com run.googleapis.com

# Create Artifact Registry repository for Cloud Build
gcloud artifacts repositories create cloud-run-source-deploy \
  --repository-format=docker \
  --location=us-central1 \
  --description="Cloud Run source deployments"
```

### Deploy to Cloud Run

1. **Easy deployment** (recommended):
```bash
# Make sure your .env file is configured with all required values
./deploy.sh
```

The deployment script will:
- Read all environment variables from your `.env` file
- Deploy to Cloud Run using those variables
- Display the service URL when complete

2. **Manual deployment** (alternative):
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
  --service-account rag-bot-sa@PROJECT-ID.iam.gserviceaccount.com \
  --set-env-vars "PROJECT_ID=PROJECT_ID,LOCATION=us-central1,RAG_CORPUS_ID=YOUR_RAG_CORPUS_ID,SLACK_BOT_TOKEN=xoxb-xxx,SLACK_SIGNING_SECRET=xxx,USE_GROUNDED_GENERATION=True,MAX_RESULTS=5,RESPONSE_TIMEOUT=30,BOT_NAME=whatsupdoc,RATE_LIMIT_PER_USER=10,RATE_LIMIT_WINDOW=60,GEMINI_MODEL=gemini-2.5-flash-lite,USE_VERTEX_AI=True,ENABLE_RAG_GENERATION=True,MAX_CONTEXT_LENGTH=100000,ANSWER_TEMPERATURE=0.1" \
  --quiet
```

3. **Configure Slack app for Cloud Run** (IMPORTANT):
   - **Disable Socket Mode**: Settings → Socket Mode → Toggle OFF
   - **Configure Event Subscriptions**:
     - Enable Events
     - Request URL: `https://YOUR-SERVICE-URL.run.app/slack/events`
     - Subscribe to bot events: `app_mention`, `message.channels`, `message.groups`, `message.im`, `message.mpim`
   - **Update Slash Commands**:
     - Set `/ask` command URL to: `https://YOUR-SERVICE-URL.run.app/slack/events`
   - **Update Interactivity & Shortcuts** (if used):
     - Request URL: `https://YOUR-SERVICE-URL.run.app/slack/events`

4. **Monitor logs**:
```bash
gcloud run logs read --service whatsupdoc-slack-bot --region us-central1
```

## 🔒 Security

- Service account follows principle of least privilege
- Slack tokens stored as environment variables
- No PDF content stored in application code
- Rate limiting prevents abuse
- Comprehensive audit logging

## 📈 Success Metrics

- ⚡ Response time < 5 seconds
- 🎯 Relevant results for 90%+ of queries
- 📊 Handle 100+ queries per day
- 📄 Clear source attribution for all answers
- 🛡️ Graceful error handling

## 🤝 Contributing

1. Follow the setup instructions above
2. Make sure all environment variables are properly configured
3. Test your changes locally before deploying

## 📞 Support

For issues with setup or deployment, create an issue in this repository or check the detailed documentation in the `cloud-functions/auto-ingest/README.md` for Cloud Function specific issues.
