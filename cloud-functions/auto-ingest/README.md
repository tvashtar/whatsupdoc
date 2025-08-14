# Auto-Ingest Cloud Function

Automatically ingests documents uploaded to a Google Cloud Storage bucket into the Vertex AI RAG Engine.

## Features

- **Automatic Processing**: Triggered by GCS bucket uploads
- **File Type Support**: PDF, TXT, DOCX, HTML, MD files
- **Chunking Strategy**: 4000 characters with 200 character overlap
- **Error Handling**: Comprehensive logging and retry logic
- **Service Account**: Uses existing `rag-bot-sa` service account

## Deployment

### Prerequisites

#### 1. Required APIs
Enable the following Google Cloud APIs:
```bash
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable eventarc.googleapis.com
gcloud services enable pubsub.googleapis.com
```

#### 2. Service Account Permissions
The function uses the existing `rag-bot-sa` service account with these required permissions:

```bash
# Core RAG and Storage permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:rag-bot-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:rag-bot-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Eventarc permissions for Gen2 Cloud Functions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:rag-bot-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/eventarc.eventReceiver"

# Cloud Run invoker permissions (Gen2 functions run on Cloud Run)
# IMPORTANT: Replace FUNCTION_NAME with your actual function name
gcloud run services add-iam-policy-binding FUNCTION_NAME \
  --member="serviceAccount:rag-bot-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=us-central1

gcloud run services add-iam-policy-binding FUNCTION_NAME \
  --member="serviceAccount:service-PROJECT_NUMBER@gcp-sa-eventarc.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=us-central1
```

#### 3. GCS and Eventarc Service Account Permissions
Additional Google-managed service accounts need permissions:

```bash
# Eventarc service account (auto-created) needs storage access
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:service-PROJECT_NUMBER@gcp-sa-eventarc.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# GCS service account needs Pub/Sub publisher for Gen2 triggers
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:service-PROJECT_NUMBER@gs-project-accounts.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

#### 4. Environment Configuration
1. Ensure `GCS_DOCUMENTS_BUCKET` is set in your `.env` file
2. Verify the target GCS bucket exists
3. Confirm bucket location compatibility (see Multi-Region Buckets section)

**Note**: RAG_CORPUS_ID and GCS_DOCUMENTS_BUCKET are automatically loaded from `../../.env`

### Deploy
```bash
cd cloud-functions/auto-ingest
./deploy.sh [bucket-name]
```

Uses `GCS_DOCUMENTS_BUCKET` from .env, or specify a different bucket as argument.

### Multi-Region Buckets
If your GCS bucket is in a multi-region location (like `us`), the deployment script handles this automatically:
- **Function Region**: `us-central1` (where the function runs)
- **Trigger Location**: `us` (matches the bucket's multi-region location)
- **Eventarc**: Routes events from bucket region to function region

## Implementation Details

### Architecture
- **Trigger**: Eventarc listens for `google.cloud.storage.object.v1.finalized` events
- **Transport**: Events flow through Pub/Sub topic to Cloud Run service
- **Processing**: CloudEvents are handled by Functions Framework v2
- **Authentication**: Service account authentication for all API calls

### Gen2 vs Gen1 Differences
This implementation uses **Cloud Functions Gen2** (runs on Cloud Run):

| Aspect | Gen1 | Gen2 (This Implementation) |
|--------|------|----------------------------|
| **Event Format** | Legacy event objects | CloudEvents specification |
| **Runtime** | Custom runtime | Cloud Run (containerized) |
| **Triggers** | Direct integration | Eventarc + Pub/Sub |
| **Scaling** | Google-managed | Cloud Run scaling |
| **Authentication** | Function-level | Cloud Run IAM |

### Key Code Features
- **CloudEvents Support**: Uses `cloudevents.http.CloudEvent` for proper event handling
- **High-Level RAG SDK**: Uses `vertexai.rag.import_files()` for reliable document ingestion
- **Robust Error Handling**: Comprehensive logging and exception management
- **File Type Filtering**: Only processes supported document types
- **Chunking Strategy**: 4000 characters with 200 overlap for optimal retrieval
- **Automatic Authentication**: Uses service account credentials via Application Default Credentials

## Testing

Upload a document to test:
```bash
gsutil cp test.pdf gs://your-bucket-name/
```

Check the logs:
```bash
# Function execution logs
gcloud functions logs read auto-ingest-documents --region=us-central1 --limit=10

# Detailed Cloud Run logs (Gen2 functions)
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="auto-ingest-documents"' --limit=10 --format="table(timestamp,severity,textPayload)"

# Check Eventarc trigger status
gcloud eventarc triggers list --location=us
```

## Troubleshooting

### Common Issues

#### 1. "Permission Denied" Errors
- Verify all service account permissions are granted (see Prerequisites)
- Check that PROJECT_NUMBER is replaced with actual project number in commands
- Ensure APIs are enabled in the correct project

#### 2. Authentication Warnings
Persistent "request was not authenticated" warnings usually indicate:
- Missing `run.invoker` permissions for Eventarc service account
- Incorrect trigger configuration
- Service account authentication issues

#### 3. Function Not Triggered
If uploads don't trigger the function:
- Verify bucket location matches trigger location
- Check Eventarc trigger exists: `gcloud eventarc triggers list --location=us`
- Ensure GCS service account has `pubsub.publisher` role

#### 4. Import/Dependency Errors
- Use `google-cloud-aiplatform>=1.108.0` for proper RAG Engine support
- Verify `cloudevents>=1.11.0` is in requirements.txt
- Check that all required APIs are enabled
- Ensure function uses CloudEvents specification, not legacy events

#### 5. Stuck Deployments
If function deployment gets stuck:
- Delete function from Cloud Console if CLI shows permanent "DEPLOYING" state
- Redeploy with new function name: `CLOUD_FUNCTION_NAME="new-name" ./deploy.sh`
- CLI can lag behind Console state - check Console for actual status

### Debug Commands
```bash
# Get project number for service account commands
gcloud projects describe PROJECT_ID --format="value(projectNumber)"

# Get GCS service account email
gsutil kms serviceaccount -p PROJECT_ID

# Check function deployment status
gcloud functions describe auto-ingest-documents --region=us-central1

# Monitor real-time logs
gcloud functions logs tail auto-ingest-documents --region=us-central1
```

## Supported File Types
- `.pdf` - PDF documents
- `.txt` - Plain text files
- `.docx` - Microsoft Word documents
- `.html` - HTML files
- `.md` - Markdown files

## Environment Variables

### Required
- `PROJECT_ID` - Google Cloud project ID
- `LOCATION` - Region (default: us-central1)
- `RAG_CORPUS_ID` - Target RAG corpus ID
- `GCS_DOCUMENTS_BUCKET` - Source bucket for document uploads

### Optional
- `RAG_SERVICE_ACCOUNT` - Service account email (default: rag-bot-sa@PROJECT_ID)
- `CLOUD_FUNCTION_NAME` - Function name (default: auto-ingest-documents)

## Current Status

### ✅ Completed Implementation
- **Cloud Function Code**: Fully implemented with proper CloudEvents handling
- **Service Permissions**: All required IAM roles granted to service accounts
- **API Dependencies**: cloudfunctions.googleapis.com, eventarc.googleapis.com, pubsub.googleapis.com enabled
- **Multi-Region Support**: Handles GCS buckets in multi-region locations
- **Error Handling**: Comprehensive logging and exception management
- **RAG Integration**: Direct Vertex AI RAG Engine API integration

### ✅ Fully Working System
- **Document Ingestion**: Successfully ingesting uploaded files into RAG corpus
- **Event Triggering**: GCS uploads properly trigger function execution
- **Authentication**: All service account permissions configured correctly
- **RAG Integration**: Using optimized `vertexai.rag.import_files()` API

## Implementation Lessons Learned

### 1. Dependencies and SDK Version
**Issue**: Earlier versions of `google-cloud-aiplatform` didn't have proper RAG Engine support.
**Solution**: Use `google-cloud-aiplatform>=1.108.0` which includes RAG fixes and high-level helpers.

### 2. High-Level vs Low-Level API
**Issue**: Manual protobuf/gRPC calls with `v1beta1` API were complex and error-prone.
**Solution**: Switch to `vertexai.rag.import_files()` high-level helper - much simpler and more reliable.

### 3. Authentication in Cloud Functions Gen2
**Issue**: Manual credential management was unnecessary and problematic.
**Solution**: Cloud Functions automatically use service account via Application Default Credentials.

### 4. Cloud Run IAM for Gen2 Functions
**Critical**: Gen2 functions run on Cloud Run, so you need Cloud Run IAM permissions:
```bash
# Both service accounts need run.invoker permission
gcloud run services add-iam-policy-binding FUNCTION_NAME \
  --member="serviceAccount:rag-bot-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=us-central1

gcloud run services add-iam-policy-binding FUNCTION_NAME \
  --member="serviceAccount:service-PROJECT_NUMBER@gcp-sa-eventarc.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=us-central1
```

### 5. Testing and Verification
**Approach**: Verify success by checking RAG corpus file list, not just function logs.
**Command**: Check ingested files in Vertex AI Console → RAG Engine → Your Corpus

The system is **production-ready** and automatically ingests all uploaded documents into the RAG corpus for searchability via the Slack bot.
