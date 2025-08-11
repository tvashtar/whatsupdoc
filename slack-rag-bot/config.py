import os
from typing import Optional


class Config:
    def __init__(self):
        # GCP Settings
        self.project_id = os.getenv("PROJECT_ID", "")
        self.location = os.getenv("LOCATION", "global")
        self.data_store_id = os.getenv("DATA_STORE_ID", "")
        self.app_id = os.getenv("APP_ID", "")
        
        # Slack Settings
        self.slack_bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        self.slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")
        self.slack_app_token = os.getenv("SLACK_APP_TOKEN", "")
        self.slack_client_id = os.getenv("SLACK_CLIENT_ID", "")
        self.slack_client_secret = os.getenv("SLACK_CLIENT_SECRET", "")
        
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
    
    def validate(self) -> list[str]:
        errors = []
        
        if not self.project_id:
            errors.append("PROJECT_ID is required")
        if not self.data_store_id:
            errors.append("DATA_STORE_ID is required")
        if not self.app_id:
            errors.append("APP_ID is required")
        if not self.slack_bot_token:
            errors.append("SLACK_BOT_TOKEN is required")
        if not self.slack_signing_secret:
            errors.append("SLACK_SIGNING_SECRET is required")
        if not self.slack_app_token:
            errors.append("SLACK_APP_TOKEN is required")
            
        return errors