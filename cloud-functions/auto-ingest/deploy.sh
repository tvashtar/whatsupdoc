#!/bin/bash

# Deploy auto-ingest Cloud Function
# Usage: ./deploy.sh [BUCKET_NAME]

set -e

# Load environment variables from parent .env file
if [ -f "../../.env" ]; then
    set -a
    source ../../.env
    set +a
    echo "✅ Loaded RAG_CORPUS_ID from .env: ${RAG_CORPUS_ID}"
else
    echo "❌ Warning: .env file not found. RAG_CORPUS_ID must be set manually."
fi

# Configuration from environment variables
FUNCTION_NAME=${CLOUD_FUNCTION_NAME:-"auto-ingest-documents"}
REGION="us-central1"  # Function deployment region
TRIGGER_LOCATION="us"  # Must match bucket location for trigger
SERVICE_ACCOUNT=${RAG_SERVICE_ACCOUNT:-"rag-bot-sa@${PROJECT_ID}.iam.gserviceaccount.com"}

# Get bucket name from argument or use environment variable
TRIGGER_BUCKET=${1:-$GCS_DOCUMENTS_BUCKET}

# Validate required variables
if [ -z "$PROJECT_ID" ] || [ -z "$RAG_CORPUS_ID" ] || [ -z "$TRIGGER_BUCKET" ]; then
    echo "❌ Error: Missing required environment variables:"
    [ -z "$PROJECT_ID" ] && echo "  - PROJECT_ID"
    [ -z "$RAG_CORPUS_ID" ] && echo "  - RAG_CORPUS_ID" 
    [ -z "$TRIGGER_BUCKET" ] && echo "  - GCS_DOCUMENTS_BUCKET"
    echo ""
    echo "Please set these in your .env file or as environment variables."
    exit 1
fi

echo "Deploying Cloud Function: $FUNCTION_NAME"
echo "Trigger bucket: $TRIGGER_BUCKET"
echo "Service account: $SERVICE_ACCOUNT"
echo "Region: $REGION"

# Deploy the Cloud Function
gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime python311 \
  --region $REGION \
  --source . \
  --entry-point auto_ingest_documents \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=${TRIGGER_BUCKET}" \
  --trigger-location=$TRIGGER_LOCATION \
  --service-account $SERVICE_ACCOUNT \
  --memory 1GB \
  --timeout 540 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "PROJECT_ID=${PROJECT_ID},LOCATION=${REGION},RAG_CORPUS_ID=${RAG_CORPUS_ID}" \
  --quiet

echo "✅ Cloud Function deployed successfully!"
echo "📁 Monitoring bucket: gs://$TRIGGER_BUCKET"
echo "🔗 Function name: $FUNCTION_NAME"
echo ""
echo "To test, upload a PDF to the bucket:"
echo "gsutil cp test.pdf gs://$TRIGGER_BUCKET/"