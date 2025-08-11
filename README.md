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
gcloud services enable storage.googleapis.com
```

Or enable manually in the GCP Console:
1. Go to "APIs & Services" → "Library"
2. Enable:
   - Vertex AI API
   - Discovery Engine API (powers Vertex AI Search)
   - Cloud Run API
   - Cloud Storage API

#### Create Cloud Storage Bucket for PDFs

1. **Create Bucket**:
   - Go to GCP Console → "Storage" → "Buckets" → "Create"
   - **Name**: Pick unique name (e.g., `company-knowledge-base-docs`)
   - **Location type**: Choose Region (same as planned Data Store location)
   - **Storage class**: Standard
   - Leave other settings as defaults → Click "Create"

2. **Upload Your PDFs**:
   - Open your new bucket
   - Click "Upload Files" or "Upload Folder"
   - Add your company PDF documents
   - Wait for upload to complete

#### Create Vertex AI Search Application

1. **Navigate to Agent Builder**:
   - Go to GCP Console → "Agent Builder" → "Vertex AI Search"
   - Click "Create Data Store"

2. **Configure Data Store**:
   - **Content type**: Select "Unstructured"
   - **Data source**: Choose "Cloud Storage"
   - Select the bucket you created above
   - Complete setup and wait for indexing (10-30 minutes for 1000 PDFs)
   - **Note the Data Store ID** from the details page

3. **Create Search App**:
   - Still in Agent Builder → Vertex AI Search
   - Click "Create App"
   - **Application type**: Select "Search"
   - **Content type**: Choose "Generic" 
   - **Link the Data Store** you created above
   - Name your app (e.g., "company-knowledge-base")
   - Save and **note the App ID** from details page

4. **Get Required Values for .env**:
   ```bash
   # Update these in your .env file:
   PROJECT_ID=your-actual-project-id           # From GCP Console
   LOCATION=global                            # Or your chosen region
   DATA_STORE_ID=your-actual-datastore-id     # From data store details page
   APP_ID=your-actual-app-id                  # From app details page
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
# Discovery Engine permissions for Vertex AI Search
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:rag-bot-sa@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/discoveryengine.viewer"

# Additional permission for search operations
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:rag-bot-sa@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

3. **Create and Download Key**:
```bash
gcloud iam service-accounts keys create service-account.json \
  --iam-account=rag-bot-sa@YOUR-PROJECT-ID.iam.gserviceaccount.com \
  --project=YOUR-PROJECT-ID
```

   Or create via GCP Console:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click on your service account → "Keys" → "Add Key" → "JSON"
   - Download and save as `service-account.json` in your project root

4. **Update your `.env` file**:
```bash
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
```

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
   - Copy the **Client ID** → Update your `.env`: `SLACK_CLIENT_ID=your-client-id`
   - Copy the **Client Secret** → Update your `.env`: `SLACK_CLIENT_SECRET=your-client-secret`
   - Copy the **Signing Secret** → Update your `.env`: `SLACK_SIGNING_SECRET=your-signing-secret`

### 4. Verify Your Configuration

After completing the setup steps above, your `.env` file should look similar to this:

```bash
# GCP Settings (from your Vertex AI Search setup)
PROJECT_ID=your-project-id
LOCATION=global
DATA_STORE_ID=your-datastore-id_1234567890
APP_ID=your-app-id

# Slack Settings (from your Slack app configuration)
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_CLIENT_ID=your-client-id-here
SLACK_CLIENT_SECRET=your-client-secret-here

# Feature Configuration
USE_GROUNDED_GENERATION=True
MAX_RESULTS=5
RESPONSE_TIMEOUT=30

# Service Account (path to your downloaded JSON key)
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# Bot Configuration  
BOT_NAME=KnowledgeBot
RATE_LIMIT_PER_USER=10
RATE_LIMIT_WINDOW=60
```

**✅ Setup Complete!** Once all values are populated, you're ready for code implementation.

## 🛠️ Development

### Setup Environment

1. **Install dependencies with uv**:
```bash
# Create virtual environment and install dependencies
uv sync
```

2. **Verify your setup**:
```bash
# Test GCP connection
uv run tests/test_gcp_connection.py

# Test Slack connection
uv run tests/test_slack_connection.py
```

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
