// AgentTheo Web UI JavaScript

class AgentTheoUI {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.isProcessing = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 3000;
        
        // DOM elements
        this.elements = {
            messageInput: document.getElementById('messageInput'),
            sendButton: document.getElementById('sendButton'),
            chatMessages: document.getElementById('chatMessages'),
            statusIndicator: document.getElementById('statusIndicator'),
            agentStatus: document.getElementById('agentStatus'),
            vncFrame: document.getElementById('vncFrame'),
            vncLoading: document.getElementById('vncLoading'),
            clearBtn: document.getElementById('clearBtn'),
            stopBtn: document.getElementById('stopBtn'),
            fullscreenBtn: document.getElementById('fullscreenBtn'),
            refreshBtn: document.getElementById('refreshBtn')
        };
        
        // Initialize modules
        this.markdownRenderer = new MarkdownRenderer();
        this.streamHandler = new StreamHandler({
            onMessage: this.handleStreamMessage.bind(this),
            onError: this.handleStreamError.bind(this),
            onComplete: this.handleStreamComplete.bind(this),
            onStart: this.handleStreamStart.bind(this)
        });
        this.resizablePanels = null;
        
        // Message management
        this.currentStreamMessageId = null;
        
        this.init();
    }
    
    init() {
        // Connect to WebSocket
        this.connect();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup VNC frame
        this.setupVNC();
        
        // Initialize resizable panels
        this.resizablePanels = new ResizablePanels({
            container: document.querySelector('.container'),
            leftPanel: document.querySelector('.vnc-panel'),
            rightPanel: document.querySelector('.chat-panel'),
            minLeftWidth: 400,
            minRightWidth: 400
        });
    }
    
    setupEventListeners() {
        // Send button
        this.elements.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key handling
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.elements.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
        });
        
        // Clear button
        this.elements.clearBtn.addEventListener('click', () => this.clearChat());
        
        // Stop button
        this.elements.stopBtn.addEventListener('click', () => this.stopCurrentTask());
        
        // Fullscreen button
        this.elements.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        
        // Refresh VNC button
        this.elements.refreshBtn.addEventListener('click', () => this.refreshVNC());
    }
    
    connect() {
        const wsUrl = `ws://${window.location.hostname}:8000/ws`;
        this.addMessage('Connecting to AgentTheo...', 'system');
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
                this.elements.messageInput.disabled = false;
                this.elements.sendButton.disabled = false;
                this.elements.messageInput.focus();
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('Failed to parse message:', e);
                }
            };
            
            this.ws.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.elements.messageInput.disabled = true;
                this.elements.sendButton.disabled = true;
                
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.addMessage(`Connection lost. Reconnecting in ${this.reconnectDelay/1000} seconds...`, 'system');
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.connect();
                    }, this.reconnectDelay);
                } else {
                    this.addMessage('Failed to connect after multiple attempts. Please refresh the page.', 'error');
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.addMessage('Connection error occurred', 'error');
            };
        } catch (e) {
            console.error('Failed to create WebSocket:', e);
            this.addMessage('Failed to establish connection', 'error');
        }
    }
    
    handleMessage(data) {
        const { message, type } = data;
        
        // Filter out echo messages and redundant processing messages
        if (type === 'system' && message.startsWith('Received:')) {
            // Don't display the echo
            return;
        }
        
        if (type === 'system' && message.startsWith('Processing:')) {
            // Update status instead of adding a message
            this.updateAgentStatus('Processing command...');
            this.isProcessing = true;
            this.elements.stopBtn.style.display = 'inline-block';
            return;
        }
        
        // Handle different message types
        switch (type) {
            case 'system':
                if (message.includes('ready')) {
                    this.updateAgentStatus('Ready');
                }
                this.addMessage(message, 'system');
                break;
                
            case 'agent':
                if (message.includes('completed') || message.includes('Result:')) {
                    this.isProcessing = false;
                    this.elements.stopBtn.style.display = 'none';
                    this.updateAgentStatus('Ready');
                }
                this.addMessage(message, 'agent');
                break;
                
            case 'error':
                this.isProcessing = false;
                this.elements.stopBtn.style.display = 'none';
                this.updateAgentStatus('Error occurred');
                this.addMessage(message, 'error');
                break;
                
            default:
                this.addMessage(message, type);
        }
    }
    
    sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message || !this.isConnected || this.isProcessing) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Check if streaming is enabled (we'll add a setting for this)
        const useStreaming = true; // Default to streaming
        
        if (useStreaming) {
            // Start streaming response
            const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            this.streamHandler.startStream(message, messageId);
        } else {
            // Send via WebSocket (traditional method)
            this.ws.send(JSON.stringify({
                command: message,
                timestamp: new Date().toISOString()
            }));
        }
        
        // Clear input
        this.elements.messageInput.value = '';
        this.autoResizeTextarea();
        
        // Update status
        this.updateAgentStatus('Sending command...');
    }
    
    addMessage(text, type, messageId = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        if (messageId) {
            messageDiv.id = messageId;
            messageDiv.setAttribute('data-message-id', messageId);
        }
        
        // Add timestamp for non-system messages
        if (type !== 'system') {
            const timestamp = new Date().toLocaleTimeString();
            const timeSpan = document.createElement('span');
            timeSpan.className = 'message-time';
            timeSpan.textContent = timestamp;
            messageDiv.appendChild(timeSpan);
        }
        
        // Add message content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Render markdown for agent messages
        if (type === 'agent' && this.markdownRenderer) {
            // Format agent response first
            const formatted = this.markdownRenderer.formatAgentResponse(text);
            contentDiv.innerHTML = this.markdownRenderer.render(formatted);
            
            // Setup copy handlers for code blocks
            this.markdownRenderer.setupCopyHandlers(contentDiv);
        } else {
            // Plain text for other message types
            contentDiv.textContent = text;
        }
        
        messageDiv.appendChild(contentDiv);
        
        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageDiv;
    }
    
    clearChat() {
        this.elements.chatMessages.innerHTML = '';
        this.addMessage('Chat cleared', 'system');
    }
    
    stopCurrentTask() {
        if (this.isProcessing && this.isConnected) {
            this.ws.send(JSON.stringify({
                command: '__STOP__',
                timestamp: new Date().toISOString()
            }));
            this.addMessage('Stopping current task...', 'system');
        }
    }
    
    updateConnectionStatus(connected) {
        this.elements.statusIndicator.className = `status-indicator ${connected ? 'connected' : 'disconnected'}`;
        if (!connected) {
            this.updateAgentStatus('Disconnected');
        }
    }
    
    updateAgentStatus(status) {
        const statusText = this.elements.agentStatus.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = status;
        }
    }
    
    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }
    
    autoResizeTextarea() {
        const textarea = this.elements.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
    
    setupVNC() {
        this.elements.vncFrame.onload = () => {
            this.elements.vncLoading.style.display = 'none';
            this.elements.vncFrame.style.display = 'block';
        };
        
        this.elements.vncFrame.onerror = () => {
            this.elements.vncLoading.innerHTML = `
                <div class="error-message">
                    <p>Failed to load VNC viewer</p>
                    <button onclick="agentTheoUI.refreshVNC()">Retry</button>
                </div>
            `;
        };
    }
    
    refreshVNC() {
        this.elements.vncLoading.style.display = 'flex';
        this.elements.vncFrame.style.display = 'none';
        this.elements.vncFrame.src = this.elements.vncFrame.src;
    }
    
    toggleFullscreen() {
        const vncPanel = document.querySelector('.vnc-panel');
        if (!document.fullscreenElement) {
            vncPanel.requestFullscreen().catch(err => {
                console.error('Error attempting to enable fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }
    
    // Stream handler callbacks
    handleStreamStart(messageId) {
        // Create a new streaming message
        const messageDiv = this.streamHandler.createStreamMessage('', messageId);
        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        this.currentStreamMessageId = messageId;
        this.isProcessing = true;
        this.elements.stopBtn.style.display = 'inline-block';
        this.updateAgentStatus('Processing...');
    }
    
    handleStreamMessage(data) {
        if (data.type === 'append' && data.messageId) {
            // Update the streaming message
            const messageEl = document.getElementById(data.messageId);
            if (messageEl) {
                const contentEl = messageEl.querySelector('.message-content');
                if (contentEl) {
                    // Append new content
                    const currentHtml = contentEl.innerHTML;
                    const newContent = this.markdownRenderer.renderInline(data.content);
                    contentEl.innerHTML = currentHtml + newContent;
                    
                    this.scrollToBottom();
                }
            }
        } else if (data.type === 'status') {
            // Update status without affecting the message
            this.updateAgentStatus(data.content);
        }
    }
    
    handleStreamError(error) {
        console.error('Stream error:', error);
        
        if (error.messageId) {
            this.streamHandler.finalizeStreamMessage(error.messageId);
        }
        
        this.addMessage(error.message || 'Stream error occurred', 'error');
        this.isProcessing = false;
        this.elements.stopBtn.style.display = 'none';
        this.updateAgentStatus('Error occurred');
    }
    
    handleStreamComplete(data) {
        if (data.messageId) {
            // Finalize the message
            this.streamHandler.finalizeStreamMessage(data.messageId);
            
            // Re-render the complete message with full markdown
            const messageEl = document.getElementById(data.messageId);
            if (messageEl && data.finalContent) {
                const contentEl = messageEl.querySelector('.message-content');
                if (contentEl) {
                    const formatted = this.markdownRenderer.formatAgentResponse(data.finalContent);
                    contentEl.innerHTML = this.markdownRenderer.render(formatted);
                    this.markdownRenderer.setupCopyHandlers(contentEl);
                }
            }
        }
        
        this.currentStreamMessageId = null;
        this.isProcessing = false;
        this.elements.stopBtn.style.display = 'none';
        this.updateAgentStatus('Ready');
        this.scrollToBottom();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.agentTheoUI = new AgentTheoUI();
});

// Add message timestamp styling
const style = document.createElement('style');
style.textContent = `
    .message-time {
        display: block;
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin-bottom: 0.25rem;
    }
    
    .error-message {
        text-align: center;
    }
    
    .error-message button {
        margin-top: 1rem;
        padding: 0.5rem 1rem;
        background-color: var(--accent-blue);
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    
    .error-message button:hover {
        background-color: var(--accent-blue-hover);
    }
`;
document.head.appendChild(style);