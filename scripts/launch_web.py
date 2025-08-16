#!/usr/bin/env python3
"""Launch script for WhatsUpDoc web interface.

This script starts the FastAPI + Gradio web interface for local development.
"""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Launch the web interface."""
    print("🚀 Starting WhatsUpDoc Web Interface...")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src/whatsupdoc").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)

    # Check if .env exists
    if not Path(".env").exists():
        print("⚠️  Warning: .env file not found. Make sure environment variables are set.")
        print("   You may need to create .env with:")
        print("   - GOOGLE_CLOUD_PROJECT")
        print("   - VERTEX_AI_LOCATION")
        print("   - RAG_CORPUS_ID")
        print("   - GRADIO_ADMIN_USERNAME")
        print("   - GRADIO_ADMIN_PASSWORD")
        print()

    print("🌐 FastAPI Web Interface will be available at:")
    print("   - API Documentation: http://localhost:8000/api/docs")
    print("   - Health Check: http://localhost:8000/api/health")
    print("   - Chat API: http://localhost:8000/api/chat")
    print()
    print("💡 For Gradio Admin Interface (separate):")
    print("   - Run: uv run python src/whatsupdoc/web/app.py")
    print("   - Access: http://localhost:7860")
    print("   - Username/Password: Set via GRADIO_ADMIN_USERNAME/GRADIO_ADMIN_PASSWORD env vars")
    print()
    print("📝 Press Ctrl+C to stop the server")
    print("=" * 50)

    try:
        # Launch the web interface using uvicorn
        subprocess.run(
            [
                "uv",
                "run",
                "uvicorn",
                "whatsupdoc.web.api:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down web interface...")
    except FileNotFoundError:
        print("❌ Error: 'uv' command not found. Please install uv first.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting web interface: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
