#!/usr/bin/env python3
"""Modern app entry point with dual implementation support."""

import os

from dotenv import load_dotenv


def main() -> None:
    """Main entry point with support for both modern and legacy implementations."""
    # Load environment variables
    load_dotenv()

    print("🌟 Starting whatsupdoc RAG chatbot...")
    
    # Check if we should use modern implementation
    use_modern = os.getenv("USE_MODERN_IMPLEMENTATION", "false").lower() == "true"
    
    try:
        if use_modern:
            print("🚀 Using modern async implementation...")
            from whatsupdoc.modern_slack_bot import ModernSlackBot
            bot = ModernSlackBot()
            bot.start()
        else:
            print("🔄 Using legacy implementation...")
            from whatsupdoc.slack_bot import ResearchPaperBot
            bot = ResearchPaperBot()
            bot.start()
            
    except Exception as e:
        print(f"💥 Bot startup failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()