# What's Up Doc? 🤖

A Slack RAG (Retrieval-Augmented Generation) chatbot that allows employees to query company knowledge base using natural language. Built with Google Cloud's Vertex AI Search and deployed on Cloud Run.

## 🏗️ Architecture

- **Knowledge Base**: Vertex AI Search (handles PDF ingestion, embedding, and retrieval)
- **Interface**: Slack bot responding to @mentions, slash commands, and DMs
- **Hosting**: Google Cloud Run (serverless, auto-scaling)
- **Language**: Python with Slack Bolt framework

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

2. Follow the setup sections below to populate your `.env` file with actual values.

### 2. Google Cloud Setup

#### Enable Required APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable discoveryengine.googleapis.com
gcloud services enable run.googleapis.com
```

Or enable manually in the GCP Console:
1. Go to "APIs & Services" → "Library"
2. Enable:
   - Vertex AI API
   - Discovery Engine API
   - Cloud Run API

#### Create Vertex AI Search Application

1. **Navigate to Vertex AI Search**:
   - Go to GCP Console → "Vertex AI" → "Search and Conversation"
   - Click "Create App" → Choose "Search" type
   - Select "Generic" content type
   - Name it (e.g., "company-knowledge-base")

2. **Create Data Store**:
   - When prompted, create a new data store
   - Note the **Data Store ID** from the details page

3. **Import Your PDFs**:
   - In your data store, click "Import Data"
   - Choose source: Cloud Storage or direct upload
   - Upload your company documents (PDFs)
   - Wait for indexing to complete (10-30 minutes for 1000 PDFs)

4. **Get Required Values for .env**:
   ```bash
   # Update these in your .env file:
   PROJECT_ID=your-actual-project-id           # From GCP Console
   LOCATION=global                            # Or your chosen region
   DATA_STORE_ID=your-actual-datastore-id     # From data store details page
   APP_ID=your-actual-app-id                  # From app details page
   ```

#### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create rag-bot-sa \
  --display-name="RAG Bot Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:rag-bot-sa@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/discoveryengine.viewer"

# Create and download key
gcloud iam service-accounts keys create service-account.json \
  --iam-account=rag-bot-sa@YOUR-PROJECT-ID.iam.gserviceaccount.com
```

Update your `.env` file:
```bash
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
```

### 3. Slack App Setup

#### Create Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name it (e.g., "Knowledge Bot")
4. Select your workspace

#### Configure Bot Permissions

1. Go to "OAuth & Permissions"
2. Add these **Bot Token Scopes**:
   - `app_mentions:read` (respond to @mentions)
   - `chat:write` (send messages)
   - `commands` (slash commands)
   - `channels:history` (read channel messages)
   - `groups:history` (private channels)
   - `im:history` (direct messages)
   - `mpim:history` (group DMs)

#### Install App and Get Tokens

1. **Install to Workspace**:
   - Click "Install to Workspace"
   - Authorize the permissions

2. **Get Bot Token**:
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)
   - Update your `.env`: `SLACK_BOT_TOKEN=xoxb-your-actual-token`

3. **Get Signing Secret**:
   - Go to "Basic Information" → "App Credentials"
   - Copy the "Signing Secret"
   - Update your `.env`: `SLACK_SIGNING_SECRET=your-actual-secret`

4. **Create App Token**:
   - Go to "Basic Information" → "App-Level Tokens"
   - Click "Generate Token and Scopes"
   - Name it "socket-token" and add `connections:write` scope
   - Copy the token (starts with `xapp-`)
   - Update your `.env`: `SLACK_APP_TOKEN=xapp-your-actual-token`

#### Enable Socket Mode

1. Go to "Socket Mode" → Toggle **Enable**
2. This allows local development and Cloud Run deployment

### 4. Final Environment Configuration

Your `.env` file should now look like this:

```bash
# GCP Settings
PROJECT_ID=my-company-project
LOCATION=global
DATA_STORE_ID=my-datastore-id_1234567890
APP_ID=my-app-id_0987654321

# Slack Settings
SLACK_BOT_TOKEN=xoxb-1234567890-1234567890-abcdefghijklmnopqrstuvwx
SLACK_SIGNING_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
SLACK_APP_TOKEN=xapp-1-A01234567-1234567890-abcdefghijklmnopqrstuvwxyz1234567890abcdef

# Feature Configuration
USE_GROUNDED_GENERATION=True
MAX_RESULTS=5
RESPONSE_TIMEOUT=30

# Service Account
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# Bot Configuration
BOT_NAME=KnowledgeBot
RATE_LIMIT_PER_USER=10
RATE_LIMIT_WINDOW=60
```

## 🛠️ Development

Once your environment is set up, you'll be ready for the code implementation phase. The bot will be built with:

- **Python 3.11+**
- **Slack Bolt Framework** for Slack integration
- **Google Cloud Vertex AI Search** for document retrieval
- **Cloud Run** for serverless deployment

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

## 🚀 Deployment

Deployment instructions will be added once the code implementation is complete.

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

For issues with setup or deployment, check the troubleshooting section or create an issue in this repository.
