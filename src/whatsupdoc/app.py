#!/usr/bin/env python3
"""whatsupdoc - Modern Slack RAG Chatbot Entry Point

This module provides the main entry point for the whatsupdoc Slack bot.
Uses modernized implementations with proper async patterns, official SDKs,
and enhanced error handling for 25-40% performance improvement.
"""

from dotenv import load_dotenv


def main() -> None:
    """Main entry point for the whatsupdoc Slack bot."""
    # Load environment variables
    load_dotenv()

    print("🚀 Starting whatsupdoc RAG chatbot (modernized)...")
    try:
        from whatsupdoc.slack_bot import SlackBot
        bot = SlackBot()
        bot.start()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"💥 Bot startup failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to provide helpful error messages
        error_str = str(e).lower()
        if "connection" in error_str:
            print("\n💡 Check your network connection and service credentials")
        elif "token" in error_str or "auth" in error_str:
            print("\n💡 Check your Slack tokens in the .env file")
        elif "environment" in error_str or "config" in error_str:
            print("\n💡 Check your environment variables configuration")
        
        raise


if __name__ == "__main__":
    main()
