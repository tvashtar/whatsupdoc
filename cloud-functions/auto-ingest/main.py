"""Cloud Function for automatic document ingestion into Vertex AI RAG Engine.
Triggered by Google Cloud Storage bucket events when documents are uploaded.
"""

import logging
import os
from typing import Any

import functions_framework
import vertexai
from cloudevents.http import CloudEvent
from vertexai import rag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
PROJECT_ID = os.environ.get('PROJECT_ID')
LOCATION = os.environ.get('LOCATION', 'us-central1')
RAG_CORPUS_ID = os.environ.get('RAG_CORPUS_ID')

# Supported file types for RAG ingestion
SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.docx', '.html', '.md'}

# Log startup
logger.info(f"🚀 Auto-ingest function initialized! PROJECT_ID: {PROJECT_ID}, RAG_CORPUS_ID: {RAG_CORPUS_ID}")


class RAGIngestionClient:
    """Client for ingesting documents into Vertex AI RAG Engine."""

    def __init__(self, project_id: str, location: str, rag_corpus_id: str):
        self.project_id = project_id
        self.location = location
        self.rag_corpus_id = rag_corpus_id

        # Initialize Vertex AI with project and location
        vertexai.init(project=project_id, location=location)

        # Extract corpus ID from full resource name if needed
        if '/' in rag_corpus_id:
            # Full resource name like projects/xxx/locations/xxx/ragCorpora/123
            self.corpus_resource_name = rag_corpus_id
        else:
            # Just the numeric ID
            self.corpus_resource_name = f"projects/{project_id}/locations/{location}/ragCorpora/{rag_corpus_id}"

        logger.info(f"Initialized RAG ingestion client for corpus: {self.corpus_resource_name}")

    def ingest_file(self, gcs_uri: str, display_name: str) -> dict[str, Any]:
        """Ingest a file from GCS into the RAG corpus using high-level helper.
        
        Args:
            gcs_uri: GCS URI of the file (gs://bucket/path/file.pdf)
            display_name: Display name for the file in RAG corpus
            
        Returns:
            Operation response

        """
        try:
            # Use high-level Vertex AI RAG helper
            response = rag.import_files(
                corpus_name=self.corpus_resource_name,
                paths=[gcs_uri],
                transformation_config=rag.TransformationConfig(
                    rag.ChunkingConfig(
                        chunk_size=4000,
                        chunk_overlap=200
                    )
                )
            )

            logger.info(f"Successfully initiated ingestion for {gcs_uri}")
            logger.info(f"Import response: {response}")

            # Return operation info
            return {
                "status": "initiated",
                "gcs_uri": gcs_uri,
                "imported_count": getattr(response, "imported_rag_files_count", None)
            }

        except Exception as e:
            logger.error(f"Failed to ingest {gcs_uri}: {str(e)}")
            raise


def is_supported_file(filename: str) -> bool:
    """Check if file type is supported for RAG ingestion."""
    _, ext = os.path.splitext(filename.lower())
    return ext in SUPPORTED_EXTENSIONS


@functions_framework.cloud_event
def auto_ingest_documents(cloud_event: CloudEvent) -> str:
    """Cloud Function triggered by GCS bucket events.
    Automatically ingests supported documents into RAG corpus.
    """
    logger.info(f"🔥 Function triggered! Event type: {cloud_event['type']}")
    logger.info(f"🔥 Event source: {cloud_event['source']}")
    logger.info(f"🔥 Event data: {cloud_event.data}")

    try:
        # Extract event data from CloudEvent
        data = cloud_event.data
        bucket_name = data['bucket']
        file_name = data['name']
        event_type = cloud_event['type']

        logger.info(f"Processing GCS event: {event_type} for {bucket_name}/{file_name}")

        # Only process finalize events (new uploads)
        if event_type != 'google.cloud.storage.object.v1.finalized':
            logger.info(f"Ignoring event type: {event_type}")
            return "Ignored non-finalize event"

        # Check if file type is supported
        if not is_supported_file(file_name):
            logger.info(f"File type not supported for ingestion: {file_name}")
            return f"Skipped unsupported file type: {file_name}"

        # Skip temporary or system files
        if file_name.startswith('.') or '/.' in file_name:
            logger.info(f"Skipping system/temporary file: {file_name}")
            return f"Skipped system file: {file_name}"

        # Construct GCS URI
        gcs_uri = f"gs://{bucket_name}/{file_name}"

        # Create display name from filename
        display_name = os.path.basename(file_name)

        # Initialize RAG client and ingest file
        rag_client = RAGIngestionClient(PROJECT_ID, LOCATION, RAG_CORPUS_ID)
        result = rag_client.ingest_file(gcs_uri, display_name)

        logger.info(f"Successfully processed {gcs_uri}")
        return f"Successfully ingested {gcs_uri}"

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")

        # Re-raise for Cloud Functions to handle retry logic
        raise
