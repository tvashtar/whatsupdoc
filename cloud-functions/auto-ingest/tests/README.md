# Auto-Ingest Cloud Function Tests

Unit tests for the auto-ingest Cloud Function that monitors GCS bucket uploads and ingests documents into Vertex AI RAG Engine.

## Running Tests

From the repository root:

```bash
# Install optional cloud-functions dependencies and run tests
uv run --extra cloud-functions python cloud-functions/auto-ingest/tests/test_auto_ingest.py
```

## Test Coverage

The test suite validates:

1. **Import Tests**
   - Vertex AI SDK imports correctly
   - RAG module and components are available
   - Configuration objects can be created

2. **Main Module Tests**
   - Cloud Function module imports without errors
   - RAGIngestionClient initializes properly
   - File type filtering works correctly
   - Handles both numeric and full resource name corpus IDs

3. **CloudEvent Handling**
   - CloudEvent objects can be created and parsed
   - Event data is accessible in expected format
   - File filtering logic works with event data

4. **RAG Client Initialization**
   - Handles numeric corpus IDs
   - Handles full resource names
   - Handles string corpus IDs
   - Correctly formats corpus resource names

## Test Environment

Tests run with mock environment variables and don't require:
- Active GCP credentials
- Real RAG corpus
- Network connectivity

This ensures tests can run in CI/CD pipelines and local development without GCP access.