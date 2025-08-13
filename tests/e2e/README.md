# End-to-End Tests

This directory contains end-to-end tests for the WhatsUpDoc Slack RAG bot.

## 🧪 **Test Scripts**

### **slack_webhook_tester.py**
Comprehensive webhook testing suite that simulates various Slack interactions:
- Health checks
- Slash commands (`/ask`)
- Event subscriptions (@mentions, DMs)
- URL verification
- Proper Slack signature verification

### **slash_command_tester.py**
Simple focused test for slash command functionality with multiple query examples.

## 🚀 **Usage**

### **Prerequisites**
```bash
# Install dependencies
pip install requests python-dotenv

# Set environment variables
export SLACK_SIGNING_SECRET="your_signing_secret_here"
```

### **Running Tests**
```bash
# Full test suite
python tests/e2e/slack_webhook_tester.py

# Simple slash command tests
python tests/e2e/slash_command_tester.py
```

### **Configuration**
Update the webhook URL in the scripts to match your deployment:
```python
webhook_url = "https://your-service-url.run.app/slack/events"
```

## 🔒 **Security Notes**

- **NEVER commit real Slack secrets or tokens**
- **Use fake/test channel IDs in examples**
- **Keep production URLs in environment variables**
- **Test scripts use fake data by design**

## 📊 **Expected Results**

- **Slash Commands**: Should return `200 OK` 
- **Event Handlers**: May return `500` with fake channels (normal)
- **Health Checks**: Should return `200 OK` with service status
- **URL Verification**: Should return `200 OK` with challenge response

## 🛠️ **Customization**

To test with different queries, modify the test payloads or create new test methods:

```python
tester = SlackWebhookTester(webhook_url, signing_secret)
response = tester.test_slash_command("Your custom query here")
```