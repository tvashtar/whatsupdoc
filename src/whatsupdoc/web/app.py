#!/usr/bin/env python3
"""Web interface entry point for whatsupdoc RAG chatbot.

This module provides the main entry point for the Gradio admin interface.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Add src to Python path for imports
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from whatsupdoc.web.gradio_interface import create_gradio_interface  # noqa: E402


def main() -> None:
    """Main entry point for the Gradio admin interface."""
    # Load environment variables
    load_dotenv()

    print("🤖 WhatsUpDoc Gradio Admin Interface")
    print("=" * 40)
    print("🔐 Basic authentication enabled")
    print("📝 Testing RAG pipeline functionality")
    print("🌐 Starting Gradio interface...")
    print()

    # Create and launch Gradio interface
    try:
        interface = create_gradio_interface()
        interface.launch(server_name="0.0.0.0", server_port=7860, share=False, debug=True)
    except Exception as e:
        print(f"❌ Error starting Gradio interface: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
