#!/bin/bash
# Deployment script for WhatsUpDoc Static Files
# Deploys widget and demo page to Google Cloud Storage

set -e

echo "📦 Deploying WhatsUpDoc Static Files to GCS..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Load environment variables from .env
set -a
source .env
set +a

BUCKET_NAME="whatsupdoc-widget-static"
STATIC_DIR="src/whatsupdoc/web/static"

echo "📦 Project: $PROJECT_ID"
echo "🪣 Bucket: $BUCKET_NAME"

# Check if bucket exists, create if not
if ! gsutil ls gs://$BUCKET_NAME >/dev/null 2>&1; then
    echo "🔨 Creating bucket $BUCKET_NAME..."
    gsutil mb -p $PROJECT_ID gs://$BUCKET_NAME
    
    # Make bucket publicly accessible for static website hosting
    gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
    
    # Configure bucket for static website hosting
    gsutil web set -m demo.html -e demo.html gs://$BUCKET_NAME
    
    echo "✅ Bucket created and configured for static hosting"
else
    echo "✅ Bucket $BUCKET_NAME already exists"
fi

# Build widget if build script exists (check for package.json in widget dir)
WIDGET_DIR="$STATIC_DIR/widget"
if [ -f "$WIDGET_DIR/package.json" ]; then
    echo "🔨 Building widget..."
    cd "$WIDGET_DIR"
    npm install
    npm run build
    cd - > /dev/null
    echo "✅ Widget built successfully"
else
    echo "ℹ️  No widget build script found, using existing files"
fi

# Upload static files
echo "📤 Uploading static files..."

# Upload widget files with long cache headers (1 week for JS files)
if [ -d "$STATIC_DIR/widget" ]; then
    gsutil -m cp -r "$STATIC_DIR/widget" gs://$BUCKET_NAME/
    gsutil -m setmeta -h "Cache-Control:public, max-age=604800" gs://$BUCKET_NAME/widget/**/*.js
    gsutil -m setmeta -h "Cache-Control:public, max-age=604800" gs://$BUCKET_NAME/widget/**/*.map
    echo "✅ Widget files uploaded"
fi

# Upload demo.html with shorter cache (1 hour)
if [ -f "$STATIC_DIR/demo.html" ]; then
    gsutil cp "$STATIC_DIR/demo.html" gs://$BUCKET_NAME/
    gsutil setmeta -h "Cache-Control:public, max-age=3600" gs://$BUCKET_NAME/demo.html
    echo "✅ Demo page uploaded"
fi

# Upload any other static assets
for ext in css js png jpg jpeg gif svg ico; do
    for file in "$STATIC_DIR"/*."$ext"; do
        if [ -f "$file" ]; then
            gsutil cp "$file" gs://$BUCKET_NAME/
            echo "✅ Uploaded $(basename "$file")"
        fi
    done
done

echo ""
echo "✅ Static files deployment complete!"
echo ""
echo "🔗 Your demo page is available at:"
echo "   https://storage.googleapis.com/$BUCKET_NAME/demo.html"
echo ""
echo "🔗 Widget script URL:"
echo "   https://storage.googleapis.com/$BUCKET_NAME/widget/whatsupdoc-widget.js"