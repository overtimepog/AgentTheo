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
        // Mouse events
        this.resizer.addEventListener('mousedown', this.onMouseDown.bind(this));
        document.addEventListener('mousemove', this.onMouseMove.bind(this));
        document.addEventListener('mouseup', this.onMouseUp.bind(this));
        
        // Touch events for mobile
        this.resizer.addEventListener('touchstart', this.onTouchStart.bind(this));
        document.addEventListener('touchmove', this.onTouchMove.bind(this));
        document.addEventListener('touchend', this.onTouchEnd.bind(this));
        
        // Double click to reset
        this.resizer.addEventListener('dblclick', this.resetSizes.bind(this));
        
        // Window resize
        window.addEventListener('resize', this.onWindowResize.bind(this));
    }
    
    onMouseDown(e) {
        this.startResize(e.clientX);
    }
    
    onTouchStart(e) {
        const touch = e.touches[0];
        this.startResize(touch.clientX);
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
        
        // Show resize overlay
        this.showResizeOverlay();
    }
    
    onMouseMove(e) {
        if (!this.isResizing) return;
        this.performResize(e.clientX);
    }
    
    onTouchMove(e) {
        if (!this.isResizing) return;
        const touch = e.touches[0];
        this.performResize(touch.clientX);
        e.preventDefault(); // Prevent scrolling
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
        
        // Update overlay position
        if (this.resizeOverlay) {
            this.resizeOverlay.style.left = `${newLeftWidth}px`;
        }
    }
    
    onMouseUp() {
        this.endResize();
    }
    
    onTouchEnd() {
        this.endResize();
    }
    
    endResize() {
        if (!this.isResizing) return;
        
        this.isResizing = false;
        document.body.classList.remove('resizing');
        this.container.classList.remove('resizing');
        document.body.style.userSelect = '';
        
        // Hide resize overlay
        this.hideResizeOverlay();
        
        // Save sizes
        this.saveSizes();
    }
    
    showResizeOverlay() {
        if (!this.resizeOverlay) {
            this.resizeOverlay = document.createElement('div');
            this.resizeOverlay.className = 'resize-overlay';
            this.container.appendChild(this.resizeOverlay);
        }
        
        this.resizeOverlay.style.display = 'block';
        this.resizeOverlay.style.left = `${this.leftPanel.offsetWidth}px`;
    }
    
    hideResizeOverlay() {
        if (this.resizeOverlay) {
            this.resizeOverlay.style.display = 'none';
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
                
                .resize-overlay {
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
        // Remove event listeners and elements
        this.resizer.remove();
        if (this.resizeOverlay) {
            this.resizeOverlay.remove();
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