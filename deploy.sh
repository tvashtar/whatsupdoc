#!/bin/bash
# Simple deployment script for WhatsUpDoc Slack Bot
# Reads environment variables from .env file and deploys to Cloud Run

set -e

echo "🚀 Deploying WhatsUpDoc to Cloud Run..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Load environment variables from .env
set -a
source .env
set +a

echo "📦 Project: $PROJECT_ID"
echo "🌍 Region: $LOCATION"

# Deploy to Cloud Run
gcloud run deploy whatsupdoc-slack-bot \
    --source . \
    --region="$LOCATION" \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=10 \
    --memory=1Gi \
    --cpu=2 \
    --timeout=60 \
    --service-account="rag-bot-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,LOCATION=$LOCATION,RAG_CORPUS_ID=$RAG_CORPUS_ID,SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN,SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET,USE_GROUNDED_GENERATION=$USE_GROUNDED_GENERATION,MAX_RESULTS=$MAX_RESULTS,RESPONSE_TIMEOUT=$RESPONSE_TIMEOUT,BOT_NAME=$BOT_NAME,RATE_LIMIT_PER_USER=$RATE_LIMIT_PER_USER,RATE_LIMIT_WINDOW=$RATE_LIMIT_WINDOW,GEMINI_MODEL=$GEMINI_MODEL,USE_VERTEX_AI=$USE_VERTEX_AI,ENABLE_RAG_GENERATION=$ENABLE_RAG_GENERATION,MAX_CONTEXT_LENGTH=$MAX_CONTEXT_LENGTH,ANSWER_TEMPERATURE=$ANSWER_TEMPERATURE" \
    --quiet

echo "✅ Deployment complete!"