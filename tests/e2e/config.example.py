#!/usr/bin/env python3
"""Example configuration for E2E tests.

Copy this to config.py and update with your values.
DO NOT commit config.py with real secrets!
"""

# Example webhook URL (update with your deployment)
WEBHOOK_URL = "https://your-service-name.run.app/slack/events"

# Slack signing secret (get from Slack app settings)
# NEVER commit real secrets - use environment variables instead!
SLACK_SIGNING_SECRET = "your_signing_secret_here"

# Example test queries
TEST_QUERIES = [
    "What is our PTO policy?",
    "How do I submit expenses?",
    "What are the office hours?",
    "Tell me about health benefits",
    "How do I request vacation?"
]

# Test user/channel IDs (these are fake - safe to commit)
FAKE_USER_ID = "U2147483697"
FAKE_CHANNEL_ID = "C2147483705" 
FAKE_DM_CHANNEL_ID = "D0LAN2Q65"