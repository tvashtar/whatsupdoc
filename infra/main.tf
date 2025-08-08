terraform {
  required_version = ">= 1.6.0"

  backend "gcs" {
    bucket = "whatsupdoc-tfstate"
    prefix = "terraform/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  default = "whatsupdoc-468323"
}
variable "region" {
  default = "us-central1"
}

variable "docker_image_url" {
  default = "us-central1-docker.pkg.dev/whatsupdoc-468323/whatsupdoc/whatsupdoc:latest"
}

variable "openai_api_key" {
  description = "OpenAI API key"
  sensitive   = true
}

# --- APIs ---
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "compute.googleapis.com",
    "storage.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com"
  ])
  project = var.project_id
  service = each.key
}

# --- Terraform State Bucket ---
resource "google_storage_bucket" "tf_state" {
  name                        = "whatsupdoc-tfstate"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  versioning { enabled = true }
}

# --- Private Docs Bucket ---
resource "google_storage_bucket" "rag_docs" {
  name                        = "whatsupdoc-rag-docs"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  lifecycle_rule {
    action    { type = "Delete" }
    condition { age = 365 }
  }
}

# --- Secret Manager ---
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "OPENAI_API_KEY"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openai_api_key_version" {
  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key
}

# --- IAM for Cloud Run to read bucket & secret ---
resource "google_storage_bucket_iam_binding" "rag_bucket_binding" {
  bucket = google_storage_bucket.rag_docs.name
  role   = "roles/storage.objectViewer"
  members = [
    "serviceAccount:${var.project_id}@appspot.gserviceaccount.com"
  ]
}

resource "google_secret_manager_secret_iam_binding" "secret_access" {
  secret_id = google_secret_manager_secret.openai_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  members   = [
    "serviceAccount:${var.project_id}@appspot.gserviceaccount.com"
  ]
}



# --- Cloud Run ---
resource "google_cloud_run_service" "chatbot_api" {
  name     = "whatsupdoc-api"
  location = var.region


  template {
    spec {
      containers {
        image = var.docker_image_url
        ports {
          container_port = 8080
        }
        env {
          name  = "GCS_BUCKET"
          value = google_storage_bucket.rag_docs.name
        }
        env {
          name  = "OPENAI_API_KEY_SECRET"
          value = google_secret_manager_secret.openai_api_key.name
        }
      }
    }
  }

  autogenerate_revision_name = true
}

resource "google_cloud_run_service_iam_binding" "public_invoker" {
  location = var.region
  service  = google_cloud_run_service.chatbot_api.name
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}

output "chatbot_url" {
  value = google_cloud_run_service.chatbot_api.status[0].url
}
