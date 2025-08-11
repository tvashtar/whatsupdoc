#!/usr/bin/env python3
"""
Test script to verify Slack bot connection and configuration.
Run this to make sure your Slack setup is working before building the full bot.
"""

import os
from dotenv import load_dotenv

def test_env_variables():
    """Test that all required Slack environment variables are set."""
    print("🔍 Testing Slack environment variables...")
    
    required_vars = [
        'SLACK_BOT_TOKEN',
        'SLACK_SIGNING_SECRET',
        'SLACK_APP_TOKEN',
        'SLACK_CLIENT_ID',
        'SLACK_CLIENT_SECRET'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            # Show partial value for security
            if 'TOKEN' in var or 'SECRET' in var:
                display_value = f"{value[:8]}...{value[-4:]}"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
    
    if missing:
        print(f"  ❌ Missing variables: {', '.join(missing)}")
        return False
    
    print("  ✅ All Slack environment variables found!")
    return True

def test_token_formats():
    """Verify token formats are correct."""
    print("\n🔍 Testing token formats...")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    app_token = os.getenv('SLACK_APP_TOKEN')
    client_id = os.getenv('SLACK_CLIENT_ID')
    
    success = True
    
    if bot_token and not bot_token.startswith('xoxb-'):
        print(f"  ❌ SLACK_BOT_TOKEN should start with 'xoxb-'")
        success = False
    else:
        print(f"  ✅ Bot token format correct")
    
    if app_token and not app_token.startswith('xapp-'):
        print(f"  ❌ SLACK_APP_TOKEN should start with 'xapp-'")
        success = False
    else:
        print(f"  ✅ App token format correct")
    
    if client_id and '.' not in client_id:
        print(f"  ❌ SLACK_CLIENT_ID should contain a dot (format: number.number)")
        success = False
    else:
        print(f"  ✅ Client ID format correct")
    
    return success

def test_slack_api_connection():
    """Test connection to Slack API."""
    print("\n🔍 Testing Slack API connection...")
    
    try:
        from slack_sdk import WebClient
        
        bot_token = os.getenv('SLACK_BOT_TOKEN')
        if not bot_token:
            print("  ❌ No bot token found")
            return False
        
        client = WebClient(token=bot_token)
        
        # Test API connection with auth.test
        response = client.auth_test()
        
        if response.get("ok"):
            print(f"  ✅ Successfully connected to Slack!")
            print(f"  🤖 Bot user: @{response.get('user')}")
            print(f"  🏢 Team: {response.get('team')}")
            print(f"  🆔 User ID: {response.get('user_id')}")
            return True
        else:
            print(f"  ❌ API call failed: {response.get('error')}")
            return False
            
    except ImportError:
        print("  ❌ Missing slack-sdk package")
        print("  💡 Install with: pip install slack-sdk")
        return False
    except Exception as e:
        print(f"  ❌ Slack API connection failed: {e}")
        return False

def test_socket_mode():
    """Test Socket Mode connection capability."""
    print("\n🔍 Testing Socket Mode setup...")
    
    try:
        from slack_bolt import App
        from slack_bolt.adapter.socket_mode import SocketModeHandler
        
        app_token = os.getenv('SLACK_APP_TOKEN')
        bot_token = os.getenv('SLACK_BOT_TOKEN')
        
        if not app_token or not bot_token:
            print("  ❌ Missing tokens for Socket Mode test")
            return False
        
        # Create a minimal app (don't start it)
        app = App(token=bot_token)
        handler = SocketModeHandler(app, app_token)
        
        print("  ✅ Socket Mode handler created successfully!")
        print("  💡 Socket Mode is ready (handler not started in test)")
        
        return True
        
    except ImportError:
        print("  ❌ Missing slack-bolt package")
        print("  💡 Install with: pip install slack-bolt")
        return False
    except Exception as e:
        print(f"  ❌ Socket Mode setup failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Slack Bot Setup Verification\n")
    
    # Load environment variables
    load_dotenv()
    
    # Run tests
    tests = [
        test_env_variables,
        test_token_formats, 
        test_slack_api_connection,
        test_socket_mode
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    # Summary
    print("="*50)
    if passed == len(tests):
        print("🎉 All tests passed! Your Slack setup is ready.")
        print("💡 You can now invite the bot to channels and start building!")
    else:
        print(f"❌ {len(tests) - passed} test(s) failed. Please fix the issues above.")
    
    print("="*50)

if __name__ == "__main__":
    main()