#!/bin/bash
# Deployment script for WhatsUpDoc Web API
# Deploys FastAPI service to Cloud Run

set -e

echo "🚀 Deploying WhatsUpDoc Web API to Cloud Run..."

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
echo "🔐 CORS Origins: ${WEB_CORS_ORIGINS:-https://storage.googleapis.com/whatsupdoc-widget-static}"

# Deploy to Cloud Run
gcloud run deploy whatsupdoc-web-api \
    --source . \
    --region="$LOCATION" \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=5 \
    --memory=1Gi \
    --cpu=1 \
    --timeout=60 \
    --service-account="rag-bot-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --set-env-vars="MODE=web,PROJECT_ID=$PROJECT_ID,LOCATION=$LOCATION,RAG_CORPUS_ID=$RAG_CORPUS_ID,GEMINI_MODEL=$GEMINI_MODEL,USE_VERTEX_AI=$USE_VERTEX_AI,ENABLE_RAG_GENERATION=$ENABLE_RAG_GENERATION,MAX_CONTEXT_LENGTH=$MAX_CONTEXT_LENGTH,ANSWER_TEMPERATURE=$ANSWER_TEMPERATURE,WEB_CORS_ORIGINS=${WEB_CORS_ORIGINS:-https://storage.googleapis.com/whatsupdoc-widget-static},GRADIO_ADMIN_USERNAME=$GRADIO_ADMIN_USERNAME,GRADIO_ADMIN_PASSWORD=$GRADIO_ADMIN_PASSWORD" \
    --quiet

echo "✅ Web API deployment complete!"
echo ""
echo "🔗 Your API will be available at:"
gcloud run services describe whatsupdoc-web-api --region="$LOCATION" --format="value(status.url)"