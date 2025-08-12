import os
from typing import Optional


class Config:
    def __init__(self):
        # GCP Settings - RAG Engine Configuration
        self.project_id = os.getenv("PROJECT_ID", "")
        self.location = os.getenv("LOCATION", "us-central1")
        self.rag_corpus_id = os.getenv("RAG_CORPUS_ID", "")
        
        # Slack Settings
        self.slack_bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        self.slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")
        self.slack_app_token = os.getenv("SLACK_APP_TOKEN", "")
        
        # Feature Configuration
        self.use_grounded_generation = os.getenv("USE_GROUNDED_GENERATION", "True").lower() == "true"
        self.max_results = int(os.getenv("MAX_RESULTS", "5"))
        self.response_timeout = int(os.getenv("RESPONSE_TIMEOUT", "30"))
        
        # Bot Configuration
        self.bot_name = os.getenv("BOT_NAME", "KnowledgeBot")
        self.rate_limit_per_user = int(os.getenv("RATE_LIMIT_PER_USER", "10"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
        # Google Cloud Authentication
        self.google_credentials_path: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Gemini Settings
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.use_vertex_ai = os.getenv("USE_VERTEX_AI", "True").lower() == "true"
        
        # RAG Generation Settings
        self.enable_rag_generation = os.getenv("ENABLE_RAG_GENERATION", "True").lower() == "true"
        self.max_context_length = int(os.getenv("MAX_CONTEXT_LENGTH", "100000"))
        self.answer_temperature = float(os.getenv("ANSWER_TEMPERATURE", "0.3"))
    
    def validate(self) -> list[str]:
        errors = []
        
        if not self.project_id:
            errors.append("PROJECT_ID is required")
        if not self.rag_corpus_id:
            errors.append("RAG_CORPUS_ID is required")
        if not self.slack_bot_token:
            errors.append("SLACK_BOT_TOKEN is required")
        if not self.slack_signing_secret:
            errors.append("SLACK_SIGNING_SECRET is required")
        
        # Only require app token if not running in Cloud Run (no PORT env var)
        if not os.getenv("PORT") and not self.slack_app_token:
            errors.append("SLACK_APP_TOKEN is required for Socket Mode")
            
        return errors