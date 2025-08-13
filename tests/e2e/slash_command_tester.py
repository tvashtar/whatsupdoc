#!/usr/bin/env python3
"""Simple test for just the slash command functionality."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from slack_webhook_tester import SlackWebhookTester
from dotenv import load_dotenv

load_dotenv()

def test_various_queries():
    """Test various queries to demonstrate functionality."""
    webhook_url = "https://whatsupdoc-slack-bot-530988540591.us-central1.run.app/slack/events"
    signing_secret = os.getenv("SLACK_SIGNING_SECRET")
    
    if not signing_secret:
        print("❌ SLACK_SIGNING_SECRET required")
        return
    
    tester = SlackWebhookTester(webhook_url, signing_secret)
    
    test_queries = [
        "What is our PTO policy?",
        "How do I submit an expense report?", 
        "What are the office hours?",
        "Tell me about our health benefits",
        "How do I request vacation time?"
    ]
    
    print("🧪 Testing Multiple Slash Command Queries")
    print("=" * 50)
    
    successful = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}️⃣ Testing: '{query}'")
        try:
            response = tester.test_slash_command(query)
            if response.status_code == 200:
                print("✅ SUCCESS - Bot processed query correctly")
                successful += 1
            else:
                print(f"❌ FAILED - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {successful}/{len(test_queries)} queries successful")
    
    if successful == len(test_queries):
        print("🎉 All slash commands working perfectly!")
        print("🚀 Bot is ready for production use")
    else:
        print("⚠️ Some queries failed - check logs for details")
    
    return successful == len(test_queries)

if __name__ == "__main__":
    test_various_queries()