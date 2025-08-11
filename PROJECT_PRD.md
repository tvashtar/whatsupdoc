# 🤖 Internal RAG Chatbot using Vertex AI Search + Slack

## 📋 Overview

Build a Slack bot that allows employees to query company knowledge base (1000 PDFs) using natural language. The bot will use Google Cloud's Vertex AI Search for RAG capabilities and be deployed on Cloud Run.

## 🏗️ Architecture

- **Knowledge Base**: Vertex AI Search (handles ingestion, embedding, retrieval)
- **Interface**: Slack bot responding to mentions and slash commands  
- **Hosting**: Cloud Run (serverless, auto-scaling)
- **Language**: Python with Slack Bolt framework

---

## 🔧 Section 1: Manual Setup Tasks (YOU DO THIS)

### 1.1 Vertex AI Search Setup

#### Enable APIs in GCP Console

1. Go to "APIs & Services" → Enable:
   - Vertex AI API
   - Discovery Engine API
   - Cloud Run API

#### Create Vertex AI Search App

1. Navigate to "Vertex AI" → "Search and Conversation"
2. Click "Create App" → Choose "Search" type
3. Select "Generic" content type
4. Name it (e.g., "company-knowledge-base")
5. Create a data store when prompted

#### Import PDFs

1. In your data store, click "Import Data"
2. Choose source: Cloud Storage (upload PDFs first) or direct upload
3. Wait for indexing to complete (10-30 mins for 1000 PDFs)

#### 📝 Note these values (needed for code)

- **Project ID**: `your-project-id`
- **Location**: `global` (or your chosen region)  
- **Data Store ID**: `your-datastore-id` (from the data store details page)
- **App ID**: `your-app-id` (from the app details page)

### 1.2 Slack App Setup

#### Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it (e.g., "Knowledge Bot")
4. Select your workspace

#### Configure Bot Token Scopes

1. Go to "OAuth & Permissions"
2. Add these Bot Token Scopes:
   - `app_mentions:read` (to respond to @mentions)
   - `chat:write` (to send messages)
   - `commands` (for slash commands)
   - `channels:history` (to read messages)
   - `groups:history` (for private channels)
   - `im:history` (for DMs)
   - `mpim:history` (for group DMs)

#### Install App to Workspace

1. Click "Install to Workspace" button
2. Authorize the permissions

#### Get Credentials (save these)

- **Bot User OAuth Token**: `xoxb-...`
- **Signing Secret**: (from Basic Information page)
- **App Token**: Create one in Basic Information → App-Level Tokens (with `connections:write` scope)

#### Enable Socket Mode

1. Go to "Socket Mode" → Enable it
2. This allows local development and Cloud Run deployment without public URL initially

### 1.3 Service Account Setup

#### Create Service Account
```bash
gcloud iam service-accounts create rag-bot-sa \
  --display-name="RAG Bot Service Account"
```

#### Grant Permissions
```bash
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:rag-bot-sa@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/discoveryengine.viewer"
```

#### Create and Download Key

1. Go to IAM & Admin → Service Accounts
2. Click on your service account → Keys → Add Key → JSON
3. Download and save as `service-account.json`

---

## 💻 Section 2: Code Requirements (CLAUDE CODE IMPLEMENTS)

### 2.1 Project Structure
```
slack-rag-bot/
├── app.py                 # Main Slack bot application
├── vertex_search.py       # Vertex AI Search integration
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── Dockerfile           # For Cloud Run deployment
├── .env.example         # Example environment variables
└── README.md           # Setup and deployment instructions
```

### 2.2 Core Functionality

#### Slack Bot (`app.py`)
- Initialize Slack Bolt app with socket mode for easy deployment
- Handle mentions (`@KnowledgeBot what is our PTO policy?`)
- Handle slash command (`/ask what is our PTO policy?`)
- Handle DMs (direct messages to the bot)
- Format responses with Slack markdown and blocks for better readability
- Error handling with user-friendly error messages
- Response streaming or loading messages for better UX during searches

#### Vertex AI Search Integration (`vertex_search.py`)
**Search function that:**
- Takes a natural language query
- Calls Vertex AI Search API
- Returns structured results with snippets and source documents
- Handles pagination if needed

**Configuration for:**
- Grounded generation (on/off toggle)
- Number of results to return
- Confidence threshold for responses

#### Message Handling Features
- **Query preprocessing**: Clean and optimize user queries
- **Response formatting**:
  - Show top 3 most relevant snippets
  - Include source document names
  - Add confidence indicators
  - Provide "View more results" option if available
- **Conversation context**: Track last few messages for follow-up questions
- **Rate limiting**: Prevent abuse (e.g., max 10 queries per user per minute)

### 2.3 Configuration (`config.py`)

Environment variables to manage:

```python
# GCP Settings
PROJECT_ID = "your-project-id"
LOCATION = "global"
DATA_STORE_ID = "your-datastore-id"
APP_ID = "your-app-id"

# Slack Settings
SLACK_BOT_TOKEN = "xoxb-..."
SLACK_SIGNING_SECRET = "..."
SLACK_APP_TOKEN = "xapp-..."

# Feature Flags
USE_GROUNDED_GENERATION = True
MAX_RESULTS = 5
RESPONSE_TIMEOUT = 30
```

### 2.4 Deployment Configuration

#### Dockerfile
- Python 3.11+ slim image
- Install dependencies
- Copy application code
- Set environment variables
- Run with gunicorn for production

#### Cloud Run Deployment Script
```bash
# Build and deploy script
gcloud run deploy slack-rag-bot \
  --source . \
  --region us-central1 \
  --service-account rag-bot-sa@PROJECT-ID.iam.gserviceaccount.com \
  --set-env-vars-from-file .env.production \
  --min-instances 0 \
  --max-instances 10
```

### 2.5 Example Interactions

**User**: `@KnowledgeBot what is our remote work policy?`

**Bot Response**:
```
📚 Based on the company documentation:

**Remote Work Policy** (Employee Handbook v2.3, page 15)
> Employees may work remotely up to 3 days per week with manager approval. Core hours are 10am-3pm in your local timezone...

**Additional Guidelines** (IT Security Policy, page 8)  
> When working remotely, employees must use company-provided VPN for accessing internal resources...

📄 Sources: Employee Handbook v2.3, IT Security Policy
✨ Confidence: High (95%)
```

### 2.6 Testing Requirements
- Unit tests for search functionality
- Integration test with test data store
- Slack message formatting tests
- Error handling scenarios
- Rate limiting tests

### 2.7 Monitoring & Logging
- Log all queries and response times
- Track error rates
- Monitor Cloud Run metrics
- Set up alerts for failures

---

## 🚀 Section 3: Post-Deployment Tasks (YOU DO THIS)

### Add Bot to Channels
- Invite bot to relevant channels: `/invite @KnowledgeBot`

### Create Slash Command (optional)
- In Slack App settings → Slash Commands
- Create `/ask` command pointing to your Cloud Run URL

### Switch from Socket Mode to HTTP (for production)
- Get Cloud Run URL after deployment
- Add URL to Slack Event Subscriptions
- Disable Socket Mode

### Monitor and Iterate
- Check Cloud Run logs
- Monitor Vertex AI Search metrics
- Gather user feedback
- Adjust confidence thresholds and result counts

---

## ✅ Success Criteria

- Bot responds to queries within 5 seconds
- Returns relevant results for 90%+ of queries
- Handles 100+ queries per day without issues
- Clear source attribution for all answers
- Graceful handling of errors and edge cases

## 🔒 Security Considerations

- Service account has minimal required permissions
- Slack tokens stored securely as environment variables
- No PDF content stored in application code
- Rate limiting prevents abuse
- Audit logging for compliance