// Resizable Panels Module for AgentTheo Web UI

class ResizablePanels {
    constructor(options = {}) {
        this.container = options.container || document.querySelector('.container');
        this.leftPanel = options.leftPanel || document.querySelector('.vnc-panel');
        this.rightPanel = options.rightPanel || document.querySelector('.chat-panel');
        this.minLeftWidth = options.minLeftWidth || 300;
        this.minRightWidth = options.minRightWidth || 300;
        this.storageKey = options.storageKey || 'agenttheo-panel-sizes';
        
        this.isResizing = false;
        this.startX = 0;
        this.startLeftWidth = 0;
        this.currentPointerId = null;
        this.iframeOverlay = null;
        
        this.init();
    }
    
    init() {
        // Create resizer element
        this.resizer = document.createElement('div');
        this.resizer.className = 'panel-resizer';
        this.resizer.innerHTML = '<div class="resizer-handle"></div>';
        
        // Insert resizer between panels
        this.leftPanel.after(this.resizer);
        
        // Load saved sizes
        this.loadSavedSizes();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Apply initial styles
        this.applyStyles();
    }    
    setupEventListeners() {
        // Use pointer events for better iframe handling
        this.resizer.addEventListener('pointerdown', this.onPointerDown.bind(this));
        
        // Attach move and up events to document for better tracking
        document.addEventListener('pointermove', this.onPointerMove.bind(this));
        document.addEventListener('pointerup', this.onPointerUp.bind(this));
        document.addEventListener('pointercancel', this.onPointerUp.bind(this));
        
        // Touch events for mobile compatibility
        this.resizer.addEventListener('touchstart', this.onTouchStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.onTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.onTouchEnd.bind(this));
        
        // Double click to reset
        this.resizer.addEventListener('dblclick', this.resetSizes.bind(this));
        
        // Window resize
        window.addEventListener('resize', this.onWindowResize.bind(this));
        
        // Prevent context menu on resizer
        this.resizer.addEventListener('contextmenu', (e) => e.preventDefault());
    }
    
    onPointerDown(e) {
        e.preventDefault();
        
        // Don't use pointer capture since we're using document-level events
        this.currentPointerId = e.pointerId;
        
        this.startResize(e.clientX);
    }
    
    onPointerMove(e) {
        if (!this.isResizing) return;
        e.preventDefault();
        this.performResize(e.clientX);
    }    
    onPointerUp(e) {
        if (!this.isResizing) return;
        
        this.currentPointerId = null;
        this.endResize();
    }
    
    onTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        this.startResize(touch.clientX);
    }
    
    onTouchMove(e) {
        if (!this.isResizing) return;
        e.preventDefault();
        const touch = e.touches[0];
        this.performResize(touch.clientX);
    }
    
    onTouchEnd(e) {
        this.endResize();
    }
    
    startResize(clientX) {
        this.isResizing = true;
        this.startX = clientX;
        this.startLeftWidth = this.leftPanel.offsetWidth;
        
        // Add resizing class for visual feedback
        document.body.classList.add('resizing');
        this.container.classList.add('resizing');
        
        // Prevent text selection
        document.body.style.userSelect = 'none';
        
        // Create iframe overlay to prevent iframe from capturing events
        this.createIframeOverlay();
        
        // Show resize indicator
        this.showResizeIndicator();
    }    
    performResize(clientX) {
        const containerWidth = this.container.offsetWidth;
        const deltaX = clientX - this.startX;
        const newLeftWidth = this.startLeftWidth + deltaX;
        const newRightWidth = containerWidth - newLeftWidth - this.resizer.offsetWidth;
        
        // Check constraints
        if (newLeftWidth < this.minLeftWidth || newRightWidth < this.minRightWidth) {
            return;
        }
        
        // Calculate percentages for flexible layout
        const leftPercent = (newLeftWidth / containerWidth) * 100;
        const rightPercent = (newRightWidth / containerWidth) * 100;
        
        // Apply new sizes
        this.leftPanel.style.flex = `0 0 ${leftPercent}%`;
        this.rightPanel.style.flex = `0 0 ${rightPercent}%`;
        
        // Update resize indicator position
        if (this.resizeIndicator) {
            this.resizeIndicator.style.left = `${newLeftWidth}px`;
        }
    }
    
    endResize() {
        if (!this.isResizing) return;
        
        this.isResizing = false;
        document.body.classList.remove('resizing');
        this.container.classList.remove('resizing');
        document.body.style.userSelect = '';
        
        // Remove iframe overlay
        this.removeIframeOverlay();
        
        // Hide resize indicator
        this.hideResizeIndicator();
        
        // Save sizes
        this.saveSizes();
    }    
    showResizeIndicator() {
        if (!this.resizeIndicator) {
            this.resizeIndicator = document.createElement('div');
            this.resizeIndicator.className = 'resize-indicator';
            this.container.appendChild(this.resizeIndicator);
        }
        
        this.resizeIndicator.style.display = 'block';
        this.resizeIndicator.style.left = `${this.leftPanel.offsetWidth}px`;
    }
    
    hideResizeIndicator() {
        if (this.resizeIndicator) {
            this.resizeIndicator.style.display = 'none';
        }
    }
    
    createIframeOverlay() {
        // Create a single overlay that covers the entire viewport
        if (!this.iframeOverlay) {
            this.iframeOverlay = document.createElement('div');
            this.iframeOverlay.className = 'iframe-resize-overlay';
            this.iframeOverlay.style.position = 'fixed';
            this.iframeOverlay.style.top = '0';
            this.iframeOverlay.style.left = '0';
            this.iframeOverlay.style.width = '100%';
            this.iframeOverlay.style.height = '100%';
            this.iframeOverlay.style.zIndex = '9999';
            // Transparent overlay
            this.iframeOverlay.style.background = 'transparent';
            this.iframeOverlay.style.cursor = 'col-resize';
            this.iframeOverlay.style.pointerEvents = 'all';
        }
        
        document.body.appendChild(this.iframeOverlay);
    }
    
    removeIframeOverlay() {
        if (this.iframeOverlay && this.iframeOverlay.parentNode) {
            this.iframeOverlay.parentNode.removeChild(this.iframeOverlay);
        }
    }
    
    resetSizes() {
        // Reset to 50/50
        this.leftPanel.style.flex = '0 0 50%';
        this.rightPanel.style.flex = '0 0 50%';
        this.saveSizes();
        
        // Visual feedback
        this.resizer.classList.add('reset-animation');
        setTimeout(() => {
            this.resizer.classList.remove('reset-animation');
        }, 300);
    }
    
    saveSizes() {
        const containerWidth = this.container.offsetWidth;
        const leftWidth = this.leftPanel.offsetWidth;
        const rightWidth = this.rightPanel.offsetWidth;
        
        const sizes = {
            leftPercent: (leftWidth / containerWidth) * 100,
            rightPercent: (rightWidth / containerWidth) * 100,
            timestamp: Date.now()
        };
        
        localStorage.setItem(this.storageKey, JSON.stringify(sizes));
    }    
    loadSavedSizes() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            if (saved) {
                const sizes = JSON.parse(saved);
                this.leftPanel.style.flex = `0 0 ${sizes.leftPercent}%`;
                this.rightPanel.style.flex = `0 0 ${sizes.rightPercent}%`;
            }
        } catch (e) {
            console.error('Failed to load saved panel sizes:', e);
        }
    }
    
    onWindowResize() {
        // Maintain proportions on window resize
        const containerWidth = this.container.offsetWidth;
        const leftWidth = this.leftPanel.offsetWidth;
        const rightWidth = this.rightPanel.offsetWidth;
        
        // Check if panels are too small after resize
        if (leftWidth < this.minLeftWidth || rightWidth < this.minRightWidth) {
            this.resetSizes();
        }
    }    
    applyStyles() {
        // Add necessary styles dynamically
        if (!document.getElementById('resizable-panels-styles')) {
            const style = document.createElement('style');
            style.id = 'resizable-panels-styles';
            style.textContent = `
                .panel-resizer {
                    width: 4px;
                    background: var(--border-color);
                    cursor: col-resize;
                    position: relative;
                    transition: background-color 0.2s;
                    flex-shrink: 0;
                    touch-action: none; /* Prevent default touch behavior */
                }
                
                .panel-resizer:hover {
                    background: var(--accent-blue);
                }
                
                .resizer-handle {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 4px;
                    height: 40px;
                    background: var(--border-color);
                    border-radius: 2px;
                }
                
                .panel-resizer:hover .resizer-handle {
                    background: var(--accent-blue);
                }
                
                .container.resizing .panel-resizer {
                    background: var(--accent-blue);
                }
                
                .resize-indicator {
                    position: absolute;
                    top: 0;
                    bottom: 0;
                    width: 2px;
                    background: var(--accent-blue);
                    display: none;
                    z-index: 1000;
                    box-shadow: 0 0 10px rgba(37, 99, 235, 0.5);
                }                
                body.resizing {
                    cursor: col-resize !important;
                }
                
                body.resizing * {
                    cursor: col-resize !important;
                    user-select: none !important;
                }
                
                .panel-resizer.reset-animation {
                    animation: pulse-resizer 0.3s ease-out;
                }
                
                @keyframes pulse-resizer {
                    0% { transform: scaleX(1); }
                    50% { transform: scaleX(3); background: var(--accent-green); }
                    100% { transform: scaleX(1); }
                }
                
                /* Ensure panels don't shrink below minimum */
                .vnc-panel {
                    min-width: 300px;
                }
                
                .chat-panel {
                    min-width: 300px;
                }
                
                /* Iframe overlay during resize */
                .iframe-resize-overlay {
                    position: fixed;
                    pointer-events: all;
                    z-index: 9999;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    // Public methods
    setLayout(preset) {
        switch (preset) {
            case 'equal':
                this.leftPanel.style.flex = '0 0 50%';
                this.rightPanel.style.flex = '0 0 50%';
                break;
            case 'wide-vnc':
                this.leftPanel.style.flex = '0 0 70%';
                this.rightPanel.style.flex = '0 0 30%';
                break;
            case 'wide-chat':
                this.leftPanel.style.flex = '0 0 30%';
                this.rightPanel.style.flex = '0 0 70%';
                break;
        }
        this.saveSizes();
    }    
    destroy() {
        // Remove event listeners
        this.resizer.removeEventListener('pointerdown', this.onPointerDown.bind(this));
        document.removeEventListener('pointermove', this.onPointerMove.bind(this));
        document.removeEventListener('pointerup', this.onPointerUp.bind(this));
        document.removeEventListener('pointercancel', this.onPointerUp.bind(this));
        
        // Remove elements
        this.resizer.remove();
        if (this.resizeIndicator) {
            this.resizeIndicator.remove();
        }
        if (this.iframeOverlay) {
            this.removeIframeOverlay();
        }
        
        // Remove styles
        const styles = document.getElementById('resizable-panels-styles');
        if (styles) {
            styles.remove();
        }
    }
}

// Export for use in main app
window.ResizablePanels = ResizablePanels;