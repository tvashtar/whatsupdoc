# WhatsUpDoc Widget

An embeddable chat widget that provides AI-powered document search capabilities to any website.

## Features

- 🚀 **Modern Web Components** - Built with native Web Components and Shadow DOM
- 🎨 **Tailwind CSS Styling** - Beautiful, responsive design with dark mode support
- 🔒 **Style Isolation** - Shadow DOM prevents CSS conflicts with host page
- 📱 **Mobile Responsive** - Works perfectly on desktop and mobile devices
- 🎯 **Easy Integration** - Just one line of code to embed
- 🔧 **Highly Customizable** - Configure theme, position, colors, and more
- 💾 **Conversation History** - Automatic conversation persistence with localStorage
- ⚡ **Rate Limiting** - Built-in rate limiting with user feedback
- 🌐 **CORS Support** - Works across different domains

## Quick Start

### 1. Include the Widget Script

```html
<script src="https://your-domain.com/static/widget/whatsupdoc-widget.js"></script>
```

### 2. Add the Widget Container

```html
<div id="whatsupdoc-widget"></div>
```

That's it! The widget will automatically initialize and appear as a floating button.

## Configuration Options

Customize the widget using data attributes:

```html
<div id="whatsupdoc-widget"
     data-api-url="https://your-api.com"
     data-theme="dark"
     data-position="bottom-left"
     data-title="Ask Our AI"
     data-placeholder="How can I help you?"
     data-primary-color="#10B981">
</div>
```

### Available Attributes

| Attribute | Default | Options | Description |
|-----------|---------|---------|-------------|
| `data-api-url` | Current origin | Any valid URL | API endpoint for your WhatsUpDoc instance |
| `data-theme` | `light` | `light`, `dark`, `auto` | Color theme for the widget |
| `data-position` | `bottom-right` | `bottom-right`, `bottom-left` | Position of the floating button |
| `data-title` | `Ask WhatsUpDoc` | Any string | Title displayed in chat header |
| `data-placeholder` | `Ask me anything...` | Any string | Placeholder text for input field |
| `data-primary-color` | `#3B82F6` | Any hex color | Primary brand color for buttons and accents |

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
cd src/whatsupdoc/web/widget
npm install
```

### Development Server

```bash
npm run dev
```

This starts a development server at `http://localhost:3000` with hot reload.

### Building

```bash
# Development build
npm run build

# Production build
npm run build:prod

# Watch mode (rebuilds on changes)
npm run watch
```

Built files are output to `../static/widget/` for serving by FastAPI.

### File Structure

```
widget/
├── src/
│   └── whatsupdoc-widget.js    # Main widget source
├── dist/                       # Built files (auto-generated)
├── package.json               # NPM configuration
├── vite.config.js            # Vite build configuration
└── README.md                 # This file
```

## Browser Support

- Chrome 63+
- Firefox 67+
- Safari 13.1+
- Edge 79+

The widget uses modern Web Components and ES2018 features. A legacy build is included for older browsers.

## API Integration

The widget communicates with your WhatsUpDoc API via the `/api/chat` endpoint:

### Request Format

```json
{
  "query": "User's question",
  "conversation_id": "unique-conversation-id",
  "max_results": 5,
  "distance_threshold": 0.8
}
```

### Response Format

```json
{
  "answer": "AI generated response",
  "confidence": 0.85,
  "sources": ["doc1.pdf", "doc2.pdf"],
  "conversation_id": "unique-conversation-id",
  "response_time_ms": 1250
}
```

## Security Considerations

- **Shadow DOM Isolation**: Styles and scripts are isolated from the host page
- **Content Security Policy**: Compatible with strict CSP policies
- **Rate Limiting**: Built-in protection against abuse
- **Origin Validation**: Optional domain whitelist support
- **XSS Protection**: All user input is properly sanitized

## Customization

### Custom Themes

The widget supports custom theming via CSS variables:

```css
whatsupdoc-widget {
  --primary-color: #your-brand-color;
  --background: #custom-background;
  --text-primary: #custom-text-color;
}
```

### Event Handling

Listen to widget events:

```javascript
document.addEventListener('whatsupdoc-widget-ready', (event) => {
  console.log('Widget is ready');
});

document.addEventListener('whatsupdoc-message-sent', (event) => {
  console.log('Message sent:', event.detail.message);
});
```

## Troubleshooting

### Widget Not Appearing

1. Check browser console for JavaScript errors
2. Verify the script URL is accessible
3. Ensure the container element exists in the DOM

### API Connection Issues

1. Check CORS configuration on your server
2. Verify the `data-api-url` is correct
3. Check network tab for failed requests

### Styling Issues

1. The widget uses Shadow DOM for style isolation
2. Host page styles should not affect the widget
3. Check for CSP restrictions on inline styles

## License

MIT License - see the main project LICENSE file for details.
