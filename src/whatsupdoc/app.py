#!/usr/bin/env python3
"""
whatsupdoc - Slack RAG Chatbot Entry Point

This module provides the main entry point for the whatsupdoc Slack bot.
It handles initialization, environment setup, and bot startup.
"""

import os
from dotenv import load_dotenv
from whatsupdoc.slack_bot import ResearchPaperBot


def main():
    """Main entry point for the whatsupdoc Slack bot."""
    # Load environment variables
    load_dotenv()
    
    print("🌟 Starting whatsupdoc RAG chatbot...")
    try:
        bot = ResearchPaperBot()
        bot.start()
    except Exception as e:
        print(f"💥 Bot startup failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()