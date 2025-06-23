// Stream Handler Module for AgentTheo Web UI

class StreamHandler {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || window.location.origin;
        this.onMessage = options.onMessage || (() => {});
        this.onError = options.onError || (() => {});
        this.onComplete = options.onComplete || (() => {});
        this.onStart = options.onStart || (() => {});
        
        this.eventSource = null;
        this.currentMessageId = null;
        this.buffer = '';
        this.typingSpeed = options.typingSpeed || 30; // ms per character
        this.typingTimer = null;
        this.isTyping = false;
    }
    
    startStream(command, messageId) {
        // Close any existing stream
        this.stopStream();
        
        this.currentMessageId = messageId;
        this.buffer = '';
        this.isTyping = false;
        
        // Create SSE connection
        const url = `${this.baseUrl}/stream`;
        const params = new URLSearchParams({ command: command, messageId: messageId });
        
        this.eventSource = new EventSource(`${url}?${params}`);
        
        // Handle connection open
        this.eventSource.onopen = () => {
            console.log('SSE connection opened');
            this.onStart(messageId);
        };
        
        // Handle messages
        this.eventSource.onmessage = (event) => {
            this.handleStreamData(event.data);
        };
        
        // Handle specific event types
        this.eventSource.addEventListener('token', (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleToken(data.content);
            } catch (e) {
                console.error('Error parsing token data:', e);
            }
        });
        
        this.eventSource.addEventListener('complete', (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleComplete(data);
            } catch (e) {
                console.error('Error parsing complete data:', e);
            }
        });
        
        this.eventSource.addEventListener('error', (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleError(data.message || data.content);
            } catch (e) {
                console.error('Error parsing error data:', e);
            }
        });
        
        this.eventSource.addEventListener('status', (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleStatus(data.message || data.content);
            } catch (e) {
                console.error('Error parsing status data:', e);
            }
        });
        
        // Handle connection errors
        this.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            this.onError('Connection lost. Retrying...');
            this.stopStream();
        };
    }
    
    handleStreamData(data) {
        try {
            const parsed = JSON.parse(data);
            
            switch (parsed.type) {
                case 'token':
                    this.handleToken(parsed.content);
                    break;
                case 'chunk':
                    this.handleChunk(parsed.content);
                    break;
                case 'status':
                    this.handleStatus(parsed.content || parsed.message);
                    break;
                case 'complete':
                    this.handleComplete(parsed);
                    break;
                case 'error':
                    this.handleError(parsed.content || parsed.message);
                    break;
                default:
                    console.warn('Unknown stream data type:', parsed.type, parsed);
            }
        } catch (e) {
            // Handle plain text data
            console.error('Failed to parse stream data:', e, data);
            this.handleToken(data);
        }
    }
    
    handleToken(token) {
        // Ensure token is a string
        if (typeof token === 'object' && token.content) {
            token = token.content;
        } else if (typeof token !== 'string') {
            console.warn('Invalid token type:', typeof token, token);
            return;
        }
        
        // Add token to buffer
        this.buffer += token;
        
        // Start or continue typing animation
        if (!this.isTyping) {
            this.startTyping();
        }
    }
    
    handleChunk(chunk) {
        // Handle larger chunks of text (like code blocks)
        this.buffer += chunk;
        
        // For chunks, we might want to display faster
        if (!this.isTyping) {
            this.displayChunk(chunk);
        }
    }
    
    handleStatus(status) {
        // Update status indicator below chat instead of inline
        const statusIndicator = document.getElementById('agentStatusIndicator');
        if (!statusIndicator) return;
        
        const statusText = statusIndicator.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = status;
        }
        
        // Show the status indicator
        statusIndicator.classList.add('active');
        
        // Don't send status to chat messages
        // this.onMessage({
        //     type: 'status',
        //     content: status,
        //     messageId: this.currentMessageId
        // });
    }
    
    handleComplete(data) {
        // Ensure all buffered content is displayed
        if (this.buffer) {
            this.flushBuffer();
        }
        
        // Stop typing animation
        this.stopTyping();
        
        // Hide status indicator
        const statusIndicator = document.getElementById('agentStatusIndicator');
        if (statusIndicator) {
            statusIndicator.classList.remove('active');
        }
        
        // Close the stream
        this.stopStream();
        
        // Notify completion
        this.onComplete({
            messageId: this.currentMessageId,
            finalContent: data.content || this.buffer,
            metadata: data.metadata || {}
        });
    }
    
    handleError(error) {
        this.stopTyping();
        this.stopStream();
        
        // Hide status indicator
        const statusIndicator = document.getElementById('agentStatusIndicator');
        if (statusIndicator) {
            statusIndicator.classList.remove('active');
        }
        
        this.onError({
            message: error,
            messageId: this.currentMessageId
        });
    }
    
    startTyping() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        this.typeNextCharacter();
    }
    
    typeNextCharacter() {
        if (!this.buffer || !this.isTyping) {
            this.isTyping = false;
            return;
        }
        
        // Get next character or word for smoother animation
        let charsToType = 1;
        
        // Type whole words for better performance
        if (this.buffer.length > 10) {
            const nextSpace = this.buffer.indexOf(' ');
            if (nextSpace > 0 && nextSpace < 20) {
                charsToType = nextSpace + 1;
            } else {
                charsToType = Math.min(5, this.buffer.length);
            }
        }
        
        const chars = this.buffer.substring(0, charsToType);
        this.buffer = this.buffer.substring(charsToType);
        
        // Send the characters to display
        this.onMessage({
            type: 'append',
            content: chars,
            messageId: this.currentMessageId
        });
        
        // Schedule next character
        if (this.buffer) {
            this.typingTimer = setTimeout(() => {
                this.typeNextCharacter();
            }, this.typingSpeed);
        } else {
            this.isTyping = false;
        }
    }
    
    displayChunk(chunk) {
        // Display a chunk immediately (for code blocks, etc.)
        this.onMessage({
            type: 'append',
            content: chunk,
            messageId: this.currentMessageId
        });
    }
    
    flushBuffer() {
        if (this.buffer) {
            this.onMessage({
                type: 'append',
                content: this.buffer,
                messageId: this.currentMessageId
            });
            this.buffer = '';
        }
        this.stopTyping();
    }
    
    stopTyping() {
        this.isTyping = false;
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
            this.typingTimer = null;
        }
    }
    
    stopStream() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.stopTyping();
    }
    
    // Utility method to format streaming messages
    createStreamMessage(content = '', messageId = null) {
        const id = messageId || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message agent streaming';
        messageDiv.id = id;
        messageDiv.setAttribute('data-message-id', id);
        
        // Add timestamp
        const timestamp = document.createElement('span');
        timestamp.className = 'message-time';
        timestamp.textContent = new Date().toLocaleTimeString();
        messageDiv.appendChild(timestamp);
        
        // Add content container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = content;
        messageDiv.appendChild(contentDiv);
        
        // Add typing indicator
        const typingIndicator = document.createElement('span');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        messageDiv.appendChild(typingIndicator);
        
        return messageDiv;
    }
    
    // Update existing message with new content
    updateStreamMessage(messageId, content, append = false) {
        const messageEl = document.getElementById(messageId);
        if (!messageEl) return;
        
        const contentEl = messageEl.querySelector('.message-content');
        if (!contentEl) return;
        
        if (append) {
            contentEl.innerHTML += content;
        } else {
            contentEl.innerHTML = content;
        }
    }
    
    // Remove typing indicator when complete
    finalizeStreamMessage(messageId) {
        const messageEl = document.getElementById(messageId);
        if (!messageEl) return;
        
        messageEl.classList.remove('streaming');
        const typingIndicator = messageEl.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
}

// Add typing indicator CSS
if (!document.getElementById('stream-handler-styles')) {
    const style = document.createElement('style');
    style.id = 'stream-handler-styles';
    style.textContent = `
        .message.streaming {
            position: relative;
        }
        
        .typing-indicator {
            display: inline-flex;
            align-items: center;
            margin-left: 0.5rem;
        }
        
        .typing-indicator span {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: var(--text-secondary);
            margin: 0 1px;
            animation: typing-bounce 1.4s infinite ease-in-out;
        }
        
        .typing-indicator span:nth-child(1) {
            animation-delay: -0.32s;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: -0.16s;
        }
        
        @keyframes typing-bounce {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }
        
        .message-content {
            display: inline;
        }
        
        .message.streaming .message-content::after {
            content: '▊';
            animation: cursor-blink 1s infinite;
            color: var(--accent-blue);
            font-weight: normal;
        }
        
        @keyframes cursor-blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}

// Export for use in main app
window.StreamHandler = StreamHandler;