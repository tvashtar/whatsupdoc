#!/usr/bin/env python3
"""WSGI entry point for production deployment."""

import os

from dotenv import load_dotenv
from flask import Flask

# Load environment variables
load_dotenv()


def create_app() -> Flask:
    """Create and configure the Flask app for WSGI deployment."""
    from whatsupdoc.slack_bot import SlackBot

    # Initialize the bot (this creates the Flask app internally)
    bot = SlackBot()

    # Return the Flask app for WSGI server
    return bot.get_flask_app()


# Create the WSGI application
application = create_app()

if __name__ == "__main__":
    # For local testing
    application.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
