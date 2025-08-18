#!/bin/bash
# Script to update demo.html with actual Cloud Run URL

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <cloud-run-url>"
    echo "Example: $0 https://whatsupdoc-web-api-xxxxx-uc.a.run.app"
    exit 1
fi

CLOUD_RUN_URL=$1
DEMO_FILE="src/whatsupdoc/web/static/demo.html"

echo "🔄 Updating demo.html with Cloud Run URL: $CLOUD_RUN_URL"

# Replace placeholder with actual URL
sed -i '' "s|REPLACE_WITH_CLOUD_RUN_URL|$CLOUD_RUN_URL|g" "$DEMO_FILE"

echo "✅ Demo page updated successfully!"
echo "📄 Updated file: $DEMO_FILE"