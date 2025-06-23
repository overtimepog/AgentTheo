// Markdown Renderer Module for AgentTheo Web UI

class MarkdownRenderer {
    constructor(options = {}) {
        this.options = {
            breaks: true,
            linkify: true,
            typographer: true,
            highlight: options.highlight || this.highlightCode.bind(this),
            ...options
        };
        
        // Initialize marked with options
        this.marked = window.marked;
        if (!this.marked) {
            console.error('Marked.js not loaded. Please include marked.js library.');
            return;
        }
        
        // Configure marked
        this.marked.setOptions({
            breaks: this.options.breaks,
            gfm: true,
            headerIds: true,
            langPrefix: 'language-',
            highlight: this.options.highlight
        });
        
        // Initialize DOMPurify for security
        this.DOMPurify = window.DOMPurify;
        if (!this.DOMPurify) {
            console.warn('DOMPurify not loaded. HTML sanitization disabled.');
        }
        
        // Initialize highlight.js if available
        this.hljs = window.hljs;
        
        // Configure DOMPurify
        if (this.DOMPurify) {
            this.DOMPurify.setConfig({
                ALLOWED_TAGS: [
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'p', 'br', 'hr',
                    'ul', 'ol', 'li',
                    'a', 'em', 'strong', 'code', 'pre',
                    'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
                    'img', 'span', 'div'
                ],
                ALLOWED_ATTR: [
                    'href', 'title', 'class', 'id', 'src', 'alt',
                    'colspan', 'rowspan', 'data-language'
                ],
                ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i
            });
        }
    }
    
    render(markdown) {
        if (!this.marked) return markdown;
        
        try {
            // Parse markdown to HTML
            let html = this.marked.parse(markdown);
            
            // Sanitize HTML if DOMPurify is available
            if (this.DOMPurify) {
                html = this.DOMPurify.sanitize(html);
            }
            
            // Post-process for additional features
            html = this.postProcess(html);
            
            return html;
        } catch (error) {
            console.error('Markdown rendering error:', error);
            return this.escapeHtml(markdown);
        }
    }
    
    renderInline(markdown) {
        if (!this.marked) return markdown;
        
        try {
            let html = this.marked.parseInline(markdown);
            
            if (this.DOMPurify) {
                html = this.DOMPurify.sanitize(html);
            }
            
            return html;
        } catch (error) {
            console.error('Inline markdown rendering error:', error);
            return this.escapeHtml(markdown);
        }
    }
    
    highlightCode(code, language) {
        if (this.hljs && language && this.hljs.getLanguage(language)) {
            try {
                return this.hljs.highlight(code, { language }).value;
            } catch (error) {
                console.error('Syntax highlighting error:', error);
            }
        }
        
        // Fallback to escaped code
        return this.escapeHtml(code);
    }
    
    postProcess(html) {
        // Create a temporary container
        const container = document.createElement('div');
        container.innerHTML = html;
        
        // Add copy buttons to code blocks
        const codeBlocks = container.querySelectorAll('pre code');
        codeBlocks.forEach((block, index) => {
            const pre = block.parentElement;
            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper';
            
            // Get language from class
            const langClass = Array.from(block.classList).find(c => c.startsWith('language-'));
            const language = langClass ? langClass.replace('language-', '') : 'text';
            
            // Create header
            const header = document.createElement('div');
            header.className = 'code-block-header';
            
            const langLabel = document.createElement('span');
            langLabel.className = 'code-block-lang';
            langLabel.textContent = language;
            
            const copyBtn = document.createElement('button');
            copyBtn.className = 'code-block-copy';
            copyBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M10.707 3H14v10h-4V9.707L10.707 3zM9.293 3.707L9 4v9h4V4h-3.293l-.414-.293zM6 2h8a1 1 0 011 1v10a1 1 0 01-1 1H6a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M3 5H2a1 1 0 00-1 1v9a1 1 0 001 1h8a1 1 0 001-1v-1H6a2 2 0 01-2-2V6a2 2 0 012-2V3a2 2 0 00-2 2H3z"/></svg>';
            copyBtn.setAttribute('data-code-id', `code-${Date.now()}-${index}`);
            copyBtn.title = 'Copy code';
            
            header.appendChild(langLabel);
            header.appendChild(copyBtn);
            
            // Wrap pre element
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(header);
            wrapper.appendChild(pre);
            
            // Store code content for copying
            block.setAttribute('data-code-content', block.textContent);
        });
        
        // Make links open in new tab
        const links = container.querySelectorAll('a');
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('http')) {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
            }
        });
        
        // Add classes for better styling
        container.querySelectorAll('table').forEach(table => {
            table.classList.add('markdown-table');
        });
        
        container.querySelectorAll('blockquote').forEach(quote => {
            quote.classList.add('markdown-blockquote');
        });
        
        return container.innerHTML;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Format agent responses with better structure
    formatAgentResponse(response) {
        // Detect and format different types of content
        const lines = response.split('\n');
        const formatted = [];
        let inCodeBlock = false;
        let codeLines = [];
        let codeLanguage = '';
        
        for (const line of lines) {
            // Check for code block markers
            if (line.trim().startsWith('```')) {
                if (!inCodeBlock) {
                    inCodeBlock = true;
                    codeLanguage = line.trim().substring(3) || 'text';
                    codeLines = [];
                } else {
                    // End code block
                    formatted.push('```' + codeLanguage);
                    formatted.push(...codeLines);
                    formatted.push('```');
                    inCodeBlock = false;
                    codeLines = [];
                }
                continue;
            }
            
            if (inCodeBlock) {
                codeLines.push(line);
                continue;
            }
            
            // Format different types of lines
            let formattedLine = line;
            
            // Detect and format lists
            if (line.match(/^[\s]*[-*+]\s/)) {
                // Bullet list
                formattedLine = line;
            } else if (line.match(/^[\s]*\d+\.\s/)) {
                // Numbered list
                formattedLine = line;
            } else if (line.match(/^(#{1,6})\s/)) {
                // Headers
                formattedLine = line;
            } else if (line.includes('Error:') || line.includes('error:')) {
                // Error messages
                formattedLine = `**❌ ${line}**`;
            } else if (line.includes('Warning:') || line.includes('warning:')) {
                // Warning messages
                formattedLine = `**⚠️ ${line}**`;
            } else if (line.includes('Success:') || line.includes('success:')) {
                // Success messages
                formattedLine = `**✅ ${line}**`;
            } else if (line.includes('Note:') || line.includes('note:')) {
                // Note messages
                formattedLine = `**📝 ${line}**`;
            } else if (line.match(/^(Task|Step|Action):/i)) {
                // Task/Step indicators
                formattedLine = `### ${line}`;
            }
            
            formatted.push(formattedLine);
        }
        
        return formatted.join('\n');
    }
    
    // Utility method to create collapsible sections
    createCollapsible(title, content, isOpen = false) {
        const id = `collapse-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        return `
<details ${isOpen ? 'open' : ''} class="markdown-collapsible">
    <summary class="markdown-collapsible-title">${this.escapeHtml(title)}</summary>
    <div class="markdown-collapsible-content">
        ${this.render(content)}
    </div>
</details>
        `.trim();
    }
    
    // Add copy functionality
    setupCopyHandlers(container) {
        const copyButtons = container.querySelectorAll('.code-block-copy');
        
        copyButtons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const codeBlock = btn.closest('.code-block-wrapper').querySelector('code');
                const code = codeBlock.getAttribute('data-code-content') || codeBlock.textContent;
                
                try {
                    await navigator.clipboard.writeText(code);
                    
                    // Visual feedback
                    const originalHTML = btn.innerHTML;
                    btn.innerHTML = '✓';
                    btn.classList.add('copied');
                    
                    setTimeout(() => {
                        btn.innerHTML = originalHTML;
                        btn.classList.remove('copied');
                    }, 2000);
                } catch (error) {
                    console.error('Failed to copy code:', error);
                    
                    // Fallback
                    const textarea = document.createElement('textarea');
                    textarea.value = code;
                    textarea.style.position = 'absolute';
                    textarea.style.left = '-9999px';
                    document.body.appendChild(textarea);
                    textarea.select();
                    
                    try {
                        document.execCommand('copy');
                        btn.innerHTML = '✓';
                        setTimeout(() => {
                            btn.innerHTML = originalHTML;
                        }, 2000);
                    } catch (e) {
                        console.error('Fallback copy failed:', e);
                    }
                    
                    document.body.removeChild(textarea);
                }
            });
        });
    }
}

// Export for use in main app
window.MarkdownRenderer = MarkdownRenderer;