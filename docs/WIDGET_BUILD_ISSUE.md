# Widget Build Issue: Stale Vite Builds

## Problem Summary
The WhatsUpDoc widget's `loadConfig()` function appeared to not be running, causing the `apiUrl` to not be set correctly. This led to debugging confusion where the source code looked correct but the behavior was wrong.

## Root Cause
**Stale Vite build artifacts** - The widget source code was being modified in `src/whatsupdoc/web/widget/src/whatsupdoc-widget.js` but the compiled output in `src/whatsupdoc/web/static/widget/whatsupdoc-widget.js` was not being regenerated.

## Technical Details

### Widget Build Process
1. **Source**: `src/whatsupdoc/web/widget/src/whatsupdoc-widget.js` - Readable ES6+ source code
2. **Build Tool**: Vite with UMD output format (`vite.config.js`)
3. **Output**: `src/whatsupdoc/web/static/widget/whatsupdoc-widget.js` - Minified production build
4. **Source Maps**: `src/whatsupdoc/web/static/widget/whatsupdoc-widget.js.map` - For debugging

### Why Builds Became Stale
1. **Manual Build Process**: Vite builds are not automatic - require running `npm run build`
2. **Separate Directories**: Source and output are in different directories, making it easy to edit source without rebuilding
3. **No File Watching**: Development workflow wasn't using `npm run watch` for auto-rebuilding
4. **Git Tracking**: Both source and compiled files are tracked in git, making stale builds less obvious

### Debugging Symptoms
- Source code inspection showed correct `loadConfig()` implementation
- Browser console showed no debug logs from `loadConfig()`
- Widget appeared to load but configuration wasn't working
- `apiUrl` remained unset despite correct `data-api-url` attributes

## Resolution Steps

### Immediate Fix
```bash
cd src/whatsupdoc/web/widget
npm run build
```

### Verification
- Created local test server to verify widget loading
- Confirmed debug logs appeared after rebuild
- Widget configuration now working correctly

### Prevention Strategies

#### 1. Use Watch Mode During Development
```bash
cd src/whatsupdoc/web/widget
npm run watch  # Auto-rebuilds on source changes
```

#### 2. Build Check in Deploy Script
The deploy script (`scripts/deploy_static.sh`) already includes a build step:
```bash
# Build widget if build script exists
if [ -f "$WIDGET_DIR/package.json" ]; then
    echo "🔨 Building widget..."
    cd "$WIDGET_DIR"
    npm install
    npm run build
    cd - > /dev/null
fi
```

#### 3. Development Workflow
- Always run `npm run build` after modifying widget source
- Use `npm run watch` during active development
- Verify widget behavior in browser after changes

#### 4. Documentation Update
Added note to project README about widget build requirements.

## Files Involved

### Source Files
- `src/whatsupdoc/web/widget/src/whatsupdoc-widget.js` - Main source
- `src/whatsupdoc/web/widget/package.json` - Build configuration
- `src/whatsupdoc/web/widget/vite.config.js` - Vite build settings

### Output Files
- `src/whatsupdoc/web/static/widget/whatsupdoc-widget.js` - Compiled widget
- `src/whatsupdoc/web/static/widget/whatsupdoc-widget.js.map` - Source maps

### Configuration
- CSS is inlined into JS (no separate CSS files)
- UMD format for broad browser compatibility
- Source maps enabled for debugging
- Console logs preserved in build for debugging

## Lessons Learned
1. **Build awareness**: When using build tools, always verify compiled output matches source changes
2. **Automation**: Use watch mode during development to prevent stale builds
3. **Testing**: Local testing server helps catch build issues quickly
4. **Separation of concerns**: Clear distinction between source and build artifacts prevents confusion

## Related Issues Fixed
- Updated deploy script to cache `.map` files instead of non-existent `.css` files
- Ensured widget debug logging is preserved in production builds
