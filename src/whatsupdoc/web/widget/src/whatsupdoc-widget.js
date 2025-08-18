/**
 * WhatsUpDoc Embeddable Chat Widget
 * 
 * A modern, responsive chat widget that can be embedded on any website.
 * Uses Shadow DOM for style isolation and connects to the WhatsUpDoc RAG API.
 * 
 * Usage:
 * <script src="https://your-domain.com/static/widget/whatsupdoc-widget.js"></script>
 * <div id="whatsupdoc-widget" 
 *      data-api-url="https://your-api.com"
 *      data-theme="light"
 *      data-position="bottom-right">
 * </div>
 */

class WhatsUpDocWidget extends HTMLElement {
  constructor() {
    super();
    
    // Create shadow DOM for style isolation
    this.attachShadow({ mode: 'open' });
    
    // Widget state
    this.isOpen = false;
    this.isLoading = false;
    this.conversationId = this.generateUUID();
    this.messages = [];
    
    // Config will be loaded in connectedCallback after attributes are set
    this.config = null;
  }
  
  connectedCallback() {
    // Widget is added to DOM - load config and initialize
    this.loadConfig();
    this.init();
  }
  
  loadConfig() {
    // Configuration from data attributes - read after element is connected
    let apiUrl = this.getAttribute('data-api-url');
    let theme = this.getAttribute('data-theme');
    let position = this.getAttribute('data-position');
    let title = this.getAttribute('data-title');
    let placeholder = this.getAttribute('data-placeholder');
    let primaryColor = this.getAttribute('data-primary-color');
    
    // Fallback: if attributes are missing, try to read from the original container
    if (!apiUrl) {
      const container = document.getElementById('whatsupdoc-widget');
      if (container) {
        apiUrl = container.getAttribute('data-api-url');
        theme = theme || container.getAttribute('data-theme');
        position = position || container.getAttribute('data-position');
        title = title || container.getAttribute('data-title');
        placeholder = placeholder || container.getAttribute('data-placeholder');
        primaryColor = primaryColor || container.getAttribute('data-primary-color');
      }
    }
    
    this.config = {
      apiUrl: apiUrl || this.getDefaultApiUrl(),
      theme: theme || 'light',
      position: position || 'bottom-right',
      title: title || 'Ask WhatsUpDoc',
      placeholder: placeholder || 'Ask me anything...',
      primaryColor: primaryColor || '#3B82F6'
    };
    
    // Validation: ensure API URL is configured
    if (!this.config.apiUrl) {
      console.error('Widget configuration failed: No API URL specified. Please set data-api-url attribute.');
      throw new Error('Widget configuration failed: No API URL specified');
    }
    
    // Validation: warn if API URL looks wrong
    if (this.config.apiUrl === window.location.origin && window.location.hostname.includes('storage.googleapis.com')) {
      console.error('Invalid configuration: Widget is using GCS storage URL as API endpoint. Please set a proper API URL via data-api-url attribute.');
    }
  }
  
  getDefaultApiUrl() {
    // Intelligent default API URL selection
    // Never use storage.googleapis.com as an API URL
    if (window.location.hostname.includes('storage.googleapis.com')) {
      console.warn('Cannot use storage.googleapis.com as API URL. Please set data-api-url attribute.');
      return null; // This will cause an error, which is better than a silent failure
    }
    return window.location.origin;
  }
  
  disconnectedCallback() {
    // Cleanup when widget is removed
    this.cleanup();
  }
  
  init() {
    try {
      // Create the widget HTML structure
      this.shadowRoot.innerHTML = this.getHTML();
      
      // Apply styles
      this.applyStyles();
      
      // Set up event listeners after DOM is ready
      setTimeout(() => this.setupEventListeners(), 0);
      
      // Load conversation history from localStorage
      this.loadConversationHistory();
    } catch (error) {
      console.error('WhatsUpDoc Widget initialization failed:', error);
      this.showInitializationError();
    }
  }
  
  showInitializationError() {
    this.shadowRoot.innerHTML = `
      <div style="
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: #fee2e2;
        border: 1px solid #fecaca;
        color: #dc2626;
        padding: 12px 16px;
        border-radius: 8px;
        font-family: system-ui, sans-serif;
        font-size: 14px;
        z-index: 999999;
        max-width: 300px;
      ">
        ⚠️ WhatsUpDoc widget failed to load. Please check the console for details.
      </div>
    `;
  }
  
  getHTML() {
    return `
      <div class="whatsupdoc-widget" data-theme="${this.config.theme}">
        <!-- Floating Action Button -->
        <div class="fab-container ${this.config.position}">
          <button class="fab" id="fab-button" aria-label="Open chat">
            <svg class="fab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"></path>
            </svg>
            <span class="fab-badge" id="fab-badge" style="display: none;">1</span>
          </button>
        </div>
        
        <!-- Chat Window -->
        <div class="chat-window ${this.config.position}" id="chat-window" style="display: none;">
          <div class="chat-header">
            <div class="chat-header-content">
              <h3 class="chat-title">${this.config.title}</h3>
              <div class="chat-status" id="chat-status">Ready</div>
            </div>
            <button class="close-button" id="close-button" aria-label="Close chat">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          
          <div class="chat-messages" id="chat-messages">
            <div class="welcome-message">
              <div class="message bot-message">
                <div class="message-content">
                  <p>👋 Hi! I'm your AI assistant. I can help you find information from our knowledge base. What would you like to know?</p>
                </div>
              </div>
            </div>
          </div>
          
          <div class="chat-input-container">
            <div class="typing-indicator" id="typing-indicator" style="display: none;">
              <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span class="typing-text">AI is thinking...</span>
            </div>
            
            <form class="chat-input-form" id="chat-form">
              <div class="input-wrapper">
                <input 
                  type="text" 
                  class="chat-input" 
                  id="chat-input" 
                  placeholder="${this.config.placeholder}"
                  maxlength="5000"
                  autocomplete="off"
                />
                <button type="submit" class="send-button" id="send-button" aria-label="Send message">
                  <svg class="send-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22,2 15,22 11,13 2,9"></polygon>
                  </svg>
                </button>
              </div>
              
              <div class="rate-limit-warning" id="rate-limit-warning" style="display: none;">
                <small>Rate limit exceeded. Please wait before sending another message.</small>
              </div>
            </form>
          </div>
        </div>
      </div>
    `;
  }
  
  applyStyles() {
    const style = document.createElement('style');
    style.textContent = this.getCSS();
    this.shadowRoot.appendChild(style);
  }
  
  getCSS() {
    return `
      /* CSS Variables for theming */
      .whatsupdoc-widget {
        --primary-color: ${this.config.primaryColor};
        --primary-hover: ${this.adjustColor(this.config.primaryColor, -10)};
        --background: ${this.config.theme === 'dark' ? '#1f2937' : '#ffffff'};
        --surface: ${this.config.theme === 'dark' ? '#374151' : '#f9fafb'};
        --text-primary: ${this.config.theme === 'dark' ? '#f9fafb' : '#111827'};
        --text-secondary: ${this.config.theme === 'dark' ? '#d1d5db' : '#6b7280'};
        --border: ${this.config.theme === 'dark' ? '#4b5563' : '#e5e7eb'};
        --shadow: ${this.config.theme === 'dark' ? '0 10px 25px rgba(0, 0, 0, 0.3)' : '0 10px 25px rgba(0, 0, 0, 0.1)'};
        --shadow-lg: ${this.config.theme === 'dark' ? '0 25px 50px rgba(0, 0, 0, 0.4)' : '0 25px 50px rgba(0, 0, 0, 0.15)'};
      }
      
      * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }
      
      .whatsupdoc-widget {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-size: 14px;
        line-height: 1.5;
        color: var(--text-primary);
        position: fixed;
        z-index: 999999;
        isolation: isolate;
      }
      
      /* Floating Action Button */
      .fab-container {
        position: fixed;
        z-index: 1000001;
      }
      
      .fab-container.bottom-right {
        bottom: 24px;
        right: 24px;
      }
      
      .fab-container.bottom-left {
        bottom: 24px;
        left: 24px;
      }
      
      .fab {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: var(--primary-color);
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: var(--shadow-lg);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        color: white;
      }
      
      .fab:hover {
        background: var(--primary-hover);
        transform: scale(1.05);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
      }
      
      .fab:active {
        transform: scale(0.95);
      }
      
      .fab-icon {
        width: 24px;
        height: 24px;
        transition: transform 0.3s ease;
      }
      
      .fab.open .fab-icon {
        transform: rotate(45deg);
      }
      
      .fab-badge {
        position: absolute;
        top: -8px;
        right: -8px;
        background: #ef4444;
        color: white;
        border-radius: 12px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: 600;
        min-width: 20px;
        text-align: center;
        animation: pulse 2s infinite;
      }
      
      @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
      }
      
      /* Chat Window */
      .chat-window {
        position: fixed;
        width: 380px;
        height: 600px;
        max-height: calc(100vh - 120px);
        background: var(--background);
        border-radius: 16px;
        box-shadow: var(--shadow-lg);
        display: flex;
        flex-direction: column;
        z-index: 1000000;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border);
        animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }
      
      .chat-window.bottom-right {
        bottom: 100px;
        right: 24px;
      }
      
      .chat-window.bottom-left {
        bottom: 100px;
        left: 24px;
      }
      
      @keyframes slideIn {
        from {
          opacity: 0;
          transform: translateY(20px) scale(0.95);
        }
        to {
          opacity: 1;
          transform: translateY(0) scale(1);
        }
      }
      
      /* Chat Header */
      .chat-header {
        padding: 20px;
        border-bottom: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: var(--surface);
        border-radius: 16px 16px 0 0;
      }
      
      .chat-header-content {
        flex: 1;
      }
      
      .chat-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
      }
      
      .chat-status {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 4px;
      }
      
      .close-button {
        width: 32px;
        height: 32px;
        border: none;
        background: none;
        cursor: pointer;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-secondary);
        transition: all 0.2s ease;
      }
      
      .close-button:hover {
        background: var(--border);
        color: var(--text-primary);
      }
      
      .close-button svg {
        width: 18px;
        height: 18px;
      }
      
      /* Messages Area */
      .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      
      .chat-messages::-webkit-scrollbar {
        width: 4px;
      }
      
      .chat-messages::-webkit-scrollbar-track {
        background: transparent;
      }
      
      .chat-messages::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 2px;
      }
      
      .message {
        display: flex;
        gap: 12px;
        max-width: 85%;
        animation: messageSlideIn 0.3s ease-out;
      }
      
      .message.user-message {
        align-self: flex-end;
        flex-direction: row-reverse;
      }
      
      .message.bot-message {
        align-self: flex-start;
      }
      
      @keyframes messageSlideIn {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      
      .message-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--primary-color);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 12px;
        flex-shrink: 0;
      }
      
      .user-message .message-avatar {
        background: var(--text-secondary);
      }
      
      .message-content {
        background: var(--surface);
        padding: 12px 16px;
        border-radius: 18px;
        border: 1px solid var(--border);
        position: relative;
      }
      
      .user-message .message-content {
        background: var(--primary-color);
        color: white;
        border: none;
      }
      
      .message-content p {
        margin: 0;
        word-wrap: break-word;
      }
      
      .message-content pre {
        background: rgba(0, 0, 0, 0.1);
        padding: 8px;
        border-radius: 6px;
        margin: 8px 0;
        overflow-x: auto;
        font-size: 13px;
      }
      
      .message-content code {
        background: rgba(0, 0, 0, 0.1);
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 13px;
      }
      
      .message-sources {
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid var(--border);
        font-size: 12px;
        color: var(--text-secondary);
      }
      
      .message-sources strong {
        display: block;
        margin-bottom: 4px;
      }
      
      .source-link {
        color: var(--primary-color);
        text-decoration: none;
        display: block;
        margin: 2px 0;
      }
      
      .source-link:hover {
        text-decoration: underline;
      }
      
      .message-timestamp {
        font-size: 11px;
        color: var(--text-secondary);
        margin-top: 4px;
        opacity: 0.7;
      }
      
      /* Input Area */
      .chat-input-container {
        padding: 20px;
        border-top: 1px solid var(--border);
        background: var(--background);
        border-radius: 0 0 16px 16px;
      }
      
      .typing-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 0;
        color: var(--text-secondary);
        font-size: 13px;
      }
      
      .typing-dots {
        display: flex;
        gap: 4px;
      }
      
      .typing-dots span {
        width: 6px;
        height: 6px;
        background: var(--text-secondary);
        border-radius: 50%;
        animation: typingBounce 1.4s infinite ease-in-out;
      }
      
      .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
      .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
      
      @keyframes typingBounce {
        0%, 80%, 100% {
          transform: scale(0.8);
          opacity: 0.5;
        }
        40% {
          transform: scale(1);
          opacity: 1;
        }
      }
      
      .chat-input-form {
        margin-top: 8px;
      }
      
      .input-wrapper {
        display: flex;
        gap: 8px;
        align-items: flex-end;
      }
      
      .chat-input {
        flex: 1;
        padding: 12px 16px;
        border: 2px solid var(--border);
        border-radius: 12px;
        background: var(--background);
        color: var(--text-primary);
        font-size: 14px;
        outline: none;
        transition: all 0.2s ease;
        resize: none;
        min-height: 44px;
        max-height: 120px;
        font-family: inherit;
      }
      
      .chat-input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
      }
      
      .chat-input::placeholder {
        color: var(--text-secondary);
      }
      
      .send-button {
        width: 44px;
        height: 44px;
        border: none;
        background: var(--primary-color);
        color: white;
        border-radius: 12px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        flex-shrink: 0;
      }
      
      .send-button:hover:not(:disabled) {
        background: var(--primary-hover);
        transform: scale(1.05);
      }
      
      .send-button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none;
      }
      
      .send-icon {
        width: 18px;
        height: 18px;
      }
      
      .rate-limit-warning {
        margin-top: 8px;
        padding: 8px 12px;
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        color: #dc2626;
      }
      
      /* Mobile Responsive */
      @media (max-width: 480px) {
        .chat-window {
          width: calc(100vw - 20px);
          height: calc(100vh - 120px);
          bottom: 10px;
          left: 10px;
          right: 10px;
        }
        
        .chat-window.bottom-right,
        .chat-window.bottom-left {
          left: 10px;
          right: 10px;
        }
        
        .fab-container.bottom-right {
          right: 20px;
        }
        
        .fab-container.bottom-left {
          left: 20px;
        }
      }
      
      /* Dark mode specific adjustments */
      .whatsupdoc-widget[data-theme="dark"] .message-content pre,
      .whatsupdoc-widget[data-theme="dark"] .message-content code {
        background: rgba(255, 255, 255, 0.1);
      }
      
      .whatsupdoc-widget[data-theme="dark"] .rate-limit-warning {
        background: #fef2f2;
        border-color: #fecaca;
        color: #dc2626;
      }
    `;
  }
  
  setupEventListeners() {
    const fabButton = this.shadowRoot.getElementById('fab-button');
    const closeButton = this.shadowRoot.getElementById('close-button');
    const chatForm = this.shadowRoot.getElementById('chat-form');
    const chatInput = this.shadowRoot.getElementById('chat-input');
    
    // FAB button click
    fabButton?.addEventListener('click', () => this.toggleChat());
    
    // Close button click
    closeButton?.addEventListener('click', () => this.closeChat());
    
    // Form submission
    chatForm?.addEventListener('submit', (e) => this.handleSubmit(e));
    
    // Enter key handling
    chatInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleSubmit(e);
      }
    });
    
    // Click outside to close (optional)
    document.addEventListener('click', (e) => {
      if (this.isOpen && !this.contains(e.target)) {
        // Optional: close on outside click
        // this.closeChat();
      }
    });
  }
  
  toggleChat() {
    if (this.isOpen) {
      this.closeChat();
    } else {
      this.openChat();
    }
  }
  
  openChat() {
    const chatWindow = this.shadowRoot.getElementById('chat-window');
    const fabButton = this.shadowRoot.getElementById('fab-button');
    const chatInput = this.shadowRoot.getElementById('chat-input');
    
    chatWindow.style.display = 'flex';
    fabButton.classList.add('open');
    this.isOpen = true;
    
    // Focus input after animation
    setTimeout(() => {
      chatInput?.focus();
    }, 300);
    
    // Hide badge
    this.hideBadge();
  }
  
  closeChat() {
    const chatWindow = this.shadowRoot.getElementById('chat-window');
    const fabButton = this.shadowRoot.getElementById('fab-button');
    
    chatWindow.style.display = 'none';
    fabButton.classList.remove('open');
    this.isOpen = false;
  }
  
  async handleSubmit(e) {
    e.preventDefault();
    
    if (this.isLoading) return;
    
    const chatInput = this.shadowRoot.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message
    this.addMessage(message, 'user');
    
    // Clear input
    chatInput.value = '';
    
    // Show loading state
    this.setLoading(true);
    
    try {
      // Send message to API
      const response = await this.sendMessage(message);
      
      // Add bot response
      this.addMessage(response.answer, 'bot', {
        sources: response.sources,
        confidence: response.confidence,
        responseTime: response.response_time_ms
      });
      
    } catch (error) {
      console.error('Chat error:', error);
      
      // Add error message
      this.addMessage(
        'Sorry, I encountered an error processing your request. Please try again.',
        'bot',
        { isError: true }
      );
      
      // Handle rate limiting
      if (error.status === 429) {
        this.showRateLimit();
      }
    } finally {
      this.setLoading(false);
    }
  }
  
  async sendMessage(message) {
    // Validate API URL before making request
    if (!this.config.apiUrl) {
      throw new Error('No API URL configured. Please set data-api-url attribute.');
    }
    
    if (this.config.apiUrl.includes('storage.googleapis.com')) {
      throw new Error('Invalid API URL: Cannot use storage.googleapis.com as an API endpoint. Please check your data-api-url configuration.');
    }
    
    const apiEndpoint = `${this.config.apiUrl}/api/chat`;
    
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Widget-Origin': window.location.origin,
        'X-Widget-URL': window.location.href,
        'X-Widget-Version': '1.0.0'
      },
      body: JSON.stringify({
        query: message,
        conversation_id: this.conversationId,
        max_results: 5, // TODO still hardcoded
        distance_threshold: 0.8 // TODO still hardcoded
      })
    });
    
    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}`);
      error.status = response.status;
      
      // Enhanced error messages for common issues
      if (response.status === 404) {
        error.message = `API endpoint not found (404). Check if ${apiEndpoint} is correct.`;
      } else if (response.status === 403) {
        error.message = `Access forbidden (403). Check API permissions for ${this.config.apiUrl}`;
      } else if (response.status === 400) {
        error.message = `Bad request (400). The API rejected the request to ${apiEndpoint}`;
      }
      
      throw error;
    }
    
    return await response.json();
  }
  
  addMessage(content, type, metadata = {}) {
    const messagesContainer = this.shadowRoot.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}-message`;
    
    const timestamp = new Date().toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
    
    let sourcesHTML = '';
    if (metadata.sources && metadata.sources.length > 0) {
      sourcesHTML = `
        <div class="message-sources">
          <strong>Sources:</strong>
          ${metadata.sources.map(source => 
            `<a href="#" class="source-link">${source}</a>`
          ).join('')}
        </div>
      `;
    }
    
    messageElement.innerHTML = `
      <div class="message-avatar">
        ${type === 'user' ? 'U' : 'AI'}
      </div>
      <div class="message-content">
        <p>${this.formatMessage(content)}</p>
        ${sourcesHTML}
        <div class="message-timestamp">${timestamp}</div>
      </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    
    // Auto scroll to bottom
    this.scrollToBottom();
    
    // Save to conversation history
    this.messages.push({
      content,
      type,
      timestamp: Date.now(),
      metadata
    });
    
    this.saveConversationHistory();
  }
  
  formatMessage(content) {
    // Basic markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }
  
  setLoading(loading) {
    this.isLoading = loading;
    
    const typingIndicator = this.shadowRoot.getElementById('typing-indicator');
    const sendButton = this.shadowRoot.getElementById('send-button');
    const chatStatus = this.shadowRoot.getElementById('chat-status');
    
    if (loading) {
      typingIndicator.style.display = 'flex';
      sendButton.disabled = true;
      chatStatus.textContent = 'Thinking...';
    } else {
      typingIndicator.style.display = 'none';
      sendButton.disabled = false;
      chatStatus.textContent = 'Ready';
    }
  }
  
  showRateLimit() {
    const warning = this.shadowRoot.getElementById('rate-limit-warning');
    warning.style.display = 'block';
    
    setTimeout(() => {
      warning.style.display = 'none';
    }, 5000);
  }
  
  scrollToBottom() {
    const messagesContainer = this.shadowRoot.getElementById('chat-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
  
  showBadge(count = 1) {
    const badge = this.shadowRoot.getElementById('fab-badge');
    badge.textContent = count;
    badge.style.display = 'block';
  }
  
  hideBadge() {
    const badge = this.shadowRoot.getElementById('fab-badge');
    badge.style.display = 'none';
  }
  
  saveConversationHistory() {
    try {
      localStorage.setItem(
        `whatsupdoc-conversation-${this.conversationId}`, 
        JSON.stringify({
          messages: this.messages,
          timestamp: Date.now()
        })
      );
    } catch (error) {
      console.warn('Could not save conversation history:', error);
    }
  }
  
  loadConversationHistory() {
    try {
      const saved = localStorage.getItem(`whatsupdoc-conversation-${this.conversationId}`);
      if (saved) {
        const data = JSON.parse(saved);
        
        // Only load if less than 24 hours old
        if (Date.now() - data.timestamp < 24 * 60 * 60 * 1000) {
          this.messages = data.messages || [];
          
          // Restore messages to UI
          data.messages?.forEach(msg => {
            if (msg.type !== 'system') {
              this.addMessageToUI(msg.content, msg.type, msg.metadata);
            }
          });
        }
      }
    } catch (error) {
      console.warn('Could not load conversation history:', error);
    }
  }
  
  addMessageToUI(content, type, metadata = {}) {
    // Similar to addMessage but without saving to history
    const messagesContainer = this.shadowRoot.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}-message`;
    
    // Include sources if available in metadata
    let sourcesHTML = '';
    if (metadata.sources && metadata.sources.length > 0) {
      sourcesHTML = `
        <div class="message-sources">
          <strong>Sources:</strong>
          ${metadata.sources.map(source => 
            `<a href="#" class="source-link">${source}</a>`
          ).join('')}
        </div>
      `;
    }
    
    messageElement.innerHTML = `
      <div class="message-avatar">
        ${type === 'user' ? 'U' : 'AI'}
      </div>
      <div class="message-content">
        <p>${this.formatMessage(content)}</p>
        ${sourcesHTML}
      </div>
    `;
    
    messagesContainer.appendChild(messageElement);
  }
  
  cleanup() {
    // Cleanup when widget is removed
    this.saveConversationHistory();
  }
  
  // Utility functions
  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  
  adjustColor(hex, percent) {
    // Simple color adjustment utility
    const num = parseInt(hex.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = (num >> 8 & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    return '#' + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
      (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
      (B < 255 ? B < 1 ? 0 : B : 255))
      .toString(16).slice(1);
  }
}

// Register the custom element
if (!customElements.get('whatsupdoc-widget')) {
  customElements.define('whatsupdoc-widget', WhatsUpDocWidget);
}

// Auto-initialize function
function initializeWidget() {
  const widgetContainer = document.getElementById('whatsupdoc-widget');
  // Check for actual element children, not just text nodes
  const hasWidgetElement = widgetContainer && widgetContainer.querySelector('whatsupdoc-widget');
  
  if (widgetContainer && !hasWidgetElement) {
    const widget = document.createElement('whatsupdoc-widget');
    
    // Copy data attributes from container to widget element
    Array.from(widgetContainer.attributes).forEach(attr => {
      if (attr.name.startsWith('data-')) {
        widget.setAttribute(attr.name, attr.value);
      }
    });
    
    // Use a slight delay to ensure the custom element definition is ready
    setTimeout(() => {
      widgetContainer.appendChild(widget);
    }, 10);
  }
}


// Auto-initialize if a div with the ID exists
if (document.readyState === 'loading') {
  // DOM not yet loaded, wait for DOMContentLoaded
  document.addEventListener('DOMContentLoaded', initializeWidget);
} else {
  // DOM already loaded, initialize immediately
  initializeWidget();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = WhatsUpDocWidget;
}