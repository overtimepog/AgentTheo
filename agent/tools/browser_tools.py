"""
Browser automation tools using JavaScript execution for better performance and reliability
Combines standard toolkit with custom JavaScript-based tools for modern web apps
"""

from typing import Optional, Any, Type, List, Dict, Tuple
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_community.tools.playwright import (
    ClickTool as BaseClickTool,
    NavigateTool as BaseNavigateTool,
    NavigateBackTool,
    ExtractTextTool,
    ExtractHyperlinksTool,
    GetElementsTool,
    CurrentWebPageTool,
)
from pydantic import BaseModel, Field
from playwright.async_api import Page, Browser, BrowserContext, async_playwright
import json
import base64
import os
from datetime import datetime
from ..utils.logger import get_logger
from ..stealth import apply_stealth, StealthConfig

logger = get_logger('browser_tools')


def escape_js_string(value: str) -> str:
    """Escape a string for safe JavaScript execution"""
    if not isinstance(value, str):
        return str(value)
    
    # Escape special characters to prevent injection
    escaped = value.replace('\\', '\\\\')
    escaped = escaped.replace('"', '\\"')
    escaped = escaped.replace("'", "\\'")
    escaped = escaped.replace('\n', '\\n')
    escaped = escaped.replace('\r', '\\r')
    escaped = escaped.replace('\t', '\\t')
    escaped = escaped.replace('\b', '\\b')
    escaped = escaped.replace('\f', '\\f')
    return escaped


# Base class for custom browser tools
class BrowserTool(BaseTool):
    """Base class for browser automation tools with JavaScript execution"""
    
    page: Optional[Page] = None
    context: Optional[BrowserContext] = None
    browser: Optional[Browser] = None
    
    def set_page(self, page: Page):
        """Set the page instance for the tool"""
        self.page = page
        
    def set_context(self, context: BrowserContext):
        """Set the browser context for the tool"""
        self.context = context
        
    def set_browser(self, browser: Browser):
        """Set the browser instance for the tool"""
        self.browser = browser
        
    async def get_page(self) -> Optional[Page]:
        """Get or create a page instance"""
        if self.page:
            return self.page
            
        if self.context:
            pages = self.context.pages
            if pages:
                self.page = pages[0]
                return self.page
            else:
                self.page = await self.context.new_page()
                return self.page
                
        if self.browser:
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                pages = self.context.pages
                if pages:
                    self.page = pages[0]
                    return self.page
                else:
                    self.page = await self.context.new_page()
                    return self.page
            else:
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
                return self.page
                
        return None
    
    async def execute_js(self, js_code: str, *args) -> Any:
        """Execute JavaScript in the browser context"""
        page = await self.get_page()
        if not page:
            raise Exception("No page context available")
        
        try:
            return await page.evaluate(js_code, *args)
        except Exception as e:
            logger.error(f"JavaScript execution error: {str(e)}")
            raise
    
    async def _arun(
        self,
        *args,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs
    ) -> str:
        """Async implementation required by BaseTool"""
        raise NotImplementedError("Async implementation required")
        
    def _run(
        self,
        *args,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs
    ) -> str:
        """Sync implementation - not used in async context"""
        raise NotImplementedError("Use async implementation")


# Input Models
class TextInputSchema(BaseModel):
    """Schema for text input tool"""
    selector: str = Field(description="CSS selector for the input element")
    text: str = Field(description="Text to type into the element")
    delay: Optional[int] = Field(default=0, description="Delay between keystrokes in ms")
    clear_first: Optional[bool] = Field(default=True, description="Clear existing text first")


class ClickSchema(BaseModel):
    """Schema for click tool"""
    selector: str = Field(description="CSS selector for element to click")
    click_type: Optional[str] = Field(default="left", description="Click type: left, right, middle, double")
    wait_for_navigation: Optional[bool] = Field(default=False, description="Wait for page navigation after click")


class WaitForElementSchema(BaseModel):
    """Schema for wait for element tool"""
    selector: str = Field(description="CSS selector to wait for")
    state: Optional[str] = Field(default="visible", description="State to wait for: visible, attached, hidden, detached")
    timeout: Optional[int] = Field(default=30000, description="Timeout in milliseconds")


class ScrollSchema(BaseModel):
    """Schema for scroll tool"""
    direction: Optional[str] = Field(default="down", description="Scroll direction: up, down, left, right")
    amount: Optional[int] = Field(default=300, description="Amount to scroll in pixels")
    to_element: Optional[str] = Field(default=None, description="CSS selector to scroll to")


class ExtractDataSchema(BaseModel):
    """Schema for data extraction tool"""
    selectors: Dict[str, str] = Field(description="Dictionary mapping data keys to CSS selectors")


class ExecuteJavaScriptSchema(BaseModel):
    """Schema for JavaScript execution tool"""
    code: str = Field(description="JavaScript code to execute in the browser context")
    args: Optional[List[Any]] = Field(default=None, description="Arguments to pass to the JavaScript code")


class PressKeySchema(BaseModel):
    """Schema for key press tool"""
    selector: str = Field(description="CSS selector for the element to press key on")
    key: str = Field(description="Key to press (e.g., 'Enter', 'Tab', 'Escape')")


# Enhanced Click Tool with JavaScript
class ClickTool(BrowserTool):
    """Click elements using JavaScript for better compatibility"""
    
    name: str = "click_element"
    description: str = "Click on an element using JavaScript for better compatibility with dynamic content"
    args_schema: Type[BaseModel] = ClickSchema
    
    async def _arun(
        self,
        selector: str,
        click_type: str = "left",
        wait_for_navigation: bool = False,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Click element using JavaScript"""
        try:
            # First wait for element to be clickable
            js_wait = f"""
            new Promise((resolve, reject) => {{
                const timeout = 5000;
                const startTime = Date.now();
                
                const checkElement = () => {{
                    const element = document.querySelector("{escape_js_string(selector)}");
                    if (element) {{
                        const rect = element.getBoundingClientRect();
                        const isVisible = rect.width > 0 && rect.height > 0 && 
                                         window.getComputedStyle(element).display !== 'none' &&
                                         window.getComputedStyle(element).visibility !== 'hidden';
                        
                        if (isVisible) {{
                            resolve(element);
                        }} else if (Date.now() - startTime > timeout) {{
                            reject(new Error('Element not visible within timeout'));
                        }} else {{
                            setTimeout(checkElement, 100);
                        }}
                    }} else if (Date.now() - startTime > timeout) {{
                        reject(new Error('Element not found within timeout'));
                    }} else {{
                        setTimeout(checkElement, 100);
                    }}
                }};
                
                checkElement();
            }})
            """
            
            await self.execute_js(js_wait)
            
            # Execute click with proper event simulation
            js_click = f"""
            (() => {{
                const element = document.querySelector("{escape_js_string(selector)}");
                if (!element) {{
                    throw new Error('Element not found');
                }}
                
                // Scroll element into view
                element.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                
                // Get element coordinates
                const rect = element.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                
                // Create mouse event options
                const eventOptions = {{
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: x,
                    clientY: y
                }};
                
                // Dispatch mouse events based on click type
                if ("{click_type}" === "double") {{
                    element.dispatchEvent(new MouseEvent('mousedown', eventOptions));
                    element.dispatchEvent(new MouseEvent('mouseup', eventOptions));
                    element.dispatchEvent(new MouseEvent('click', eventOptions));
                    element.dispatchEvent(new MouseEvent('mousedown', eventOptions));
                    element.dispatchEvent(new MouseEvent('mouseup', eventOptions));
                    element.dispatchEvent(new MouseEvent('click', eventOptions));
                    element.dispatchEvent(new MouseEvent('dblclick', eventOptions));
                }} else {{
                    const button = "{click_type}" === "right" ? 2 : "{click_type}" === "middle" ? 1 : 0;
                    eventOptions.button = button;
                    element.dispatchEvent(new MouseEvent('mousedown', eventOptions));
                    element.dispatchEvent(new MouseEvent('mouseup', eventOptions));
                    element.dispatchEvent(new MouseEvent('click', eventOptions));
                    
                    // Also trigger the native click for maximum compatibility
                    if ("{click_type}" === "left") {{
                        element.click();
                    }}
                }}
                
                return 'Clicked successfully';
            }})()
            """
            
            result = await self.execute_js(js_click)
            
            # Wait for navigation if requested
            if wait_for_navigation:
                page = await self.get_page()
                await page.wait_for_load_state('networkidle', timeout=5000)
            
            logger.info(f"Clicked element '{selector}' with {click_type} click")
            return f"Successfully clicked element '{selector}'"
            
        except Exception as e:
            logger.error(f"Error clicking element: {str(e)}")
            return f"Error clicking element '{selector}': {str(e)}"


# Text Input Tool with JavaScript
class TextInputTool(BrowserTool):
    """Type text using JavaScript for better compatibility with React/Vue/Angular"""
    
    name: str = "input_text"
    description: str = "Type text into an input field using JavaScript for better framework compatibility"
    args_schema: Type[BaseModel] = TextInputSchema
    
    async def _arun(
        self,
        selector: str,
        text: str,
        delay: int = 0,
        clear_first: bool = True,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Type text using JavaScript"""
        try:
            # JavaScript for text input with proper event dispatching
            js_code = f"""
            new Promise((resolve, reject) => {{
                const selector = "{escape_js_string(selector)}";
                const text = "{escape_js_string(text)}";
                const clearFirst = {json.dumps(clear_first)};
                const delay = {delay};
                
                // Wait for element
                const findElement = () => {{
                    return new Promise((findResolve, findReject) => {{
                        const timeout = 5000;
                        const startTime = Date.now();
                        
                        const check = () => {{
                            const el = document.querySelector(selector);
                            if (el) {{
                                findResolve(el);
                            }} else if (Date.now() - startTime > timeout) {{
                                findReject(new Error('Element not found within timeout'));
                            }} else {{
                                setTimeout(check, 100);
                            }}
                        }};
                        check();
                    }});
                }};
                
                findElement().then(element => {{
                    // Focus the element
                    element.focus();
                    
                    // Clear existing content if requested
                    if (clearFirst) {{
                        // Select all text
                        if (element.select) {{
                            element.select();
                        }}
                        
                        // Clear value in a way that works with React/Vue/Angular
                        element.value = '';
                        
                        // Dispatch events to notify frameworks
                        element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                    
                    // Type text function for delay
                    const typeWithDelay = (text, delay) => {{
                        return new Promise(typeResolve => {{
                            let index = 0;
                            const typeNext = () => {{
                                if (index >= text.length) {{
                                    typeResolve();
                                    return;
                                }}
                                
                                const char = text[index];
                                const currentValue = element.value || '';
                                element.value = currentValue + char;
                                
                                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                element.dispatchEvent(new KeyboardEvent('keydown', {{ key: char, bubbles: true }}));
                                element.dispatchEvent(new KeyboardEvent('keypress', {{ key: char, bubbles: true }}));
                                element.dispatchEvent(new KeyboardEvent('keyup', {{ key: char, bubbles: true }}));
                                
                                index++;
                                setTimeout(typeNext, delay);
                            }};
                            typeNext();
                        }});
                    }};
                    
                    // Type text with optional delay
                    if (delay > 0) {{
                        typeWithDelay(text, delay).then(() => {{
                            element.blur();
                            resolve('Text input successful');
                        }});
                    }} else {{
                        // Set value directly for React/Vue/Angular
                        element.value = text;
                        
                        // Dispatch all necessary events
                        element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        // Blur to trigger validation
                        element.blur();
                        resolve('Text input successful');
                    }}
                }}).catch(error => {{
                    reject(error);
                }});
            }})
            """
            
            await self.execute_js(js_code)
            logger.info(f"Typed text into element '{selector}'")
            return f"Successfully typed text into element '{selector}'"
            
        except Exception as e:
            logger.error(f"Error typing text: {str(e)}")
            return f"Error typing text into '{selector}': {str(e)}"


# Wait for Element Tool
class WaitForElementTool(BrowserTool):
    """Wait for elements with custom conditions using JavaScript"""
    
    name: str = "wait_for_element"
    description: str = "Wait for an element to appear or reach a specific state"
    args_schema: Type[BaseModel] = WaitForElementSchema
    
    async def _arun(
        self,
        selector: str,
        state: str = "visible",
        timeout: int = 30000,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Wait for element using JavaScript"""
        try:
            js_code = f"""
            new Promise((resolve, reject) => {{
                const selector = "{escape_js_string(selector)}";
                const state = "{state}";
                const timeout = {timeout};
                const startTime = Date.now();
                
                const checkElement = () => {{
                    const element = document.querySelector(selector);
                    
                    let conditionMet = false;
                    
                    switch(state) {{
                        case "attached":
                            conditionMet = element !== null;
                            break;
                        case "detached":
                            conditionMet = element === null;
                            break;
                        case "visible":
                            if (element) {{
                                const rect = element.getBoundingClientRect();
                                const style = window.getComputedStyle(element);
                                conditionMet = rect.width > 0 && rect.height > 0 && 
                                             style.display !== 'none' && 
                                             style.visibility !== 'hidden' &&
                                             style.opacity !== '0';
                            }}
                            break;
                        case "hidden":
                            if (element) {{
                                const rect = element.getBoundingClientRect();
                                const style = window.getComputedStyle(element);
                                conditionMet = rect.width === 0 || rect.height === 0 || 
                                             style.display === 'none' || 
                                             style.visibility === 'hidden' ||
                                             style.opacity === '0';
                            }} else {{
                                conditionMet = true;
                            }}
                            break;
                    }}
                    
                    if (conditionMet) {{
                        resolve(element);
                    }} else if (Date.now() - startTime > timeout) {{
                        reject(new Error(`Element did not reach state '${{state}}' within ${{timeout}}ms`));
                    }} else {{
                        setTimeout(checkElement, 100);
                    }}
                }};
                
                checkElement();
            }})
            """
            
            await self.execute_js(js_code)
            logger.info(f"Element '{selector}' reached state '{state}'")
            return f"Element '{selector}' is now {state}"
            
        except Exception as e:
            logger.error(f"Error waiting for element: {str(e)}")
            return f"Error waiting for element '{selector}': {str(e)}"


# Scroll Tool
class ScrollTool(BrowserTool):
    """Scroll the page using JavaScript"""
    
    name: str = "scroll_page"
    description: str = "Scroll the page in a direction, by amount, or to an element"
    args_schema: Type[BaseModel] = ScrollSchema
    
    async def _arun(
        self,
        direction: str = "down",
        amount: int = 300,
        to_element: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Scroll the page using JavaScript"""
        try:
            if to_element:
                js_code = f"""
                (() => {{
                    const element = document.querySelector("{escape_js_string(to_element)}");
                    if (!element) {{
                        throw new Error('Element not found');
                    }}
                    element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    return 'Scrolled to element';
                }})()
                """
            else:
                scroll_x = 0
                scroll_y = 0
                
                if direction == "down":
                    scroll_y = amount
                elif direction == "up":
                    scroll_y = -amount
                elif direction == "right":
                    scroll_x = amount
                elif direction == "left":
                    scroll_x = -amount
                
                js_code = f"""
                (() => {{
                    window.scrollBy({{
                        left: {scroll_x},
                        top: {scroll_y},
                        behavior: 'smooth'
                    }});
                    return 'Scrolled {direction} by {amount}px';
                }})()
                """
            
            result = await self.execute_js(js_code)
            logger.info(result)
            return f"Successfully {result.lower()}"
            
        except Exception as e:
            logger.error(f"Error scrolling: {str(e)}")
            return f"Error scrolling: {str(e)}"


# DOM Mapper Tool
class DOMMapperTool(BrowserTool):
    """Advanced DOM analysis and mapping tool for comprehensive page understanding"""
    
    name: str = "analyze_dom"
    description: str = "Analyze the DOM structure and provide comprehensive element analysis including visibility, interactability, and intelligent selector generation"
    
    async def _arun(
        self,
        selector: Optional[str] = None,
        max_depth: int = 3,
        include_invisible: bool = False,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Analyze DOM structure and elements"""
        try:
            js_code = f"""
            (() => {{
                const maxDepth = {max_depth};
                const includeInvisible = {json.dumps(include_invisible)};
                const targetSelector = {json.dumps(selector) if selector else 'null'};
                
                // Helper to check element visibility
                function isElementVisible(element) {{
                    if (!element) return false;
                    
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);
                    
                    return rect.width > 0 && 
                           rect.height > 0 && 
                           style.display !== 'none' && 
                           style.visibility !== 'hidden' &&
                           style.opacity !== '0' &&
                           rect.top < window.innerHeight &&
                           rect.bottom > 0 &&
                           rect.left < window.innerWidth &&
                           rect.right > 0;
                }}
                
                // Helper to check if element is interactable
                function isInteractable(element) {{
                    if (!isElementVisible(element)) return false;
                    
                    const tagName = element.tagName.toLowerCase();
                    const isDisabled = element.disabled || element.getAttribute('aria-disabled') === 'true';
                    const isReadonly = element.readOnly || element.getAttribute('aria-readonly') === 'true';
                    
                    const interactableTags = ['a', 'button', 'input', 'select', 'textarea', 'label'];
                    const hasClickHandler = element.onclick || element.getAttribute('onclick');
                    const hasRole = element.getAttribute('role');
                    const isContentEditable = element.contentEditable === 'true';
                    
                    return !isDisabled && !isReadonly && (
                        interactableTags.includes(tagName) ||
                        hasClickHandler ||
                        hasRole ||
                        isContentEditable ||
                        element.tabIndex >= 0
                    );
                }}
                
                // Generate intelligent selectors
                function generateSelectors(element) {{
                    const selectors = [];
                    
                    // ID selector
                    if (element.id) {{
                        selectors.push(`#${{element.id}}`);
                    }}
                    
                    // Class selector
                    if (element.className && typeof element.className === 'string') {{
                        const classes = element.className.trim().split(/\\s+/);
                        if (classes.length > 0 && classes[0]) {{
                            selectors.push(`.${{classes.join('.')}}`);
                        }}
                    }}
                    
                    // Data attributes
                    for (const attr of element.attributes) {{
                        if (attr.name.startsWith('data-')) {{
                            selectors.push(`[${{attr.name}}="${{attr.value}}"]`);
                        }}
                    }}
                    
                    // ARIA attributes
                    const ariaLabel = element.getAttribute('aria-label');
                    if (ariaLabel) {{
                        selectors.push(`[aria-label="${{ariaLabel}}"]`);
                    }}
                    
                    // Text content selector
                    const text = element.textContent?.trim();
                    if (text && text.length < 50 && !text.includes('\\n')) {{
                        selectors.push(`text="${{text}}"`);
                    }}
                    
                    // Tag with attributes
                    const tag = element.tagName.toLowerCase();
                    const type = element.getAttribute('type');
                    const name = element.getAttribute('name');
                    const placeholder = element.getAttribute('placeholder');
                    
                    if (type) selectors.push(`${{tag}}[type="${{type}}"]`);
                    if (name) selectors.push(`${{tag}}[name="${{name}}"]`);
                    if (placeholder) selectors.push(`${{tag}}[placeholder="${{placeholder}}"]`);
                    
                    // Role selector
                    const role = element.getAttribute('role');
                    if (role) {{
                        selectors.push(`[role="${{role}}"]`);
                    }}
                    
                    return selectors;
                }}
                
                // Analyze element
                function analyzeElement(element, depth = 0) {{
                    if (!element || depth > maxDepth) return null;
                    
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);
                    const visible = isElementVisible(element);
                    
                    if (!includeInvisible && !visible) return null;
                    
                    const analysis = {{
                        tagName: element.tagName.toLowerCase(),
                        visible: visible,
                        interactable: isInteractable(element),
                        selectors: generateSelectors(element),
                        attributes: {{}},
                        position: {{
                            top: rect.top,
                            left: rect.left,
                            width: rect.width,
                            height: rect.height,
                            centerX: rect.left + rect.width / 2,
                            centerY: rect.top + rect.height / 2
                        }},
                        style: {{
                            display: style.display,
                            visibility: style.visibility,
                            opacity: style.opacity,
                            zIndex: style.zIndex,
                            position: style.position
                        }},
                        text: element.textContent?.trim().substring(0, 100),
                        value: element.value || null,
                        children: []
                    }};
                    
                    // Collect important attributes
                    const importantAttrs = ['id', 'class', 'name', 'type', 'href', 'src', 
                                          'alt', 'title', 'placeholder', 'role', 'aria-label'];
                    for (const attr of importantAttrs) {{
                        const value = element.getAttribute(attr);
                        if (value) analysis.attributes[attr] = value;
                    }}
                    
                    // Analyze children if not at max depth
                    if (depth < maxDepth) {{
                        const children = Array.from(element.children);
                        for (const child of children) {{
                            const childAnalysis = analyzeElement(child, depth + 1);
                            if (childAnalysis) {{
                                analysis.children.push(childAnalysis);
                            }}
                        }}
                    }}
                    
                    return analysis;
                }}
                
                // Main analysis
                let results;
                
                if (targetSelector) {{
                    // Analyze specific elements
                    const elements = document.querySelectorAll(targetSelector);
                    results = {{
                        selector: targetSelector,
                        count: elements.length,
                        elements: Array.from(elements).map(el => analyzeElement(el, 0)).filter(Boolean)
                    }};
                }} else {{
                    // Analyze page structure
                    const body = document.body;
                    const interactableElements = [];
                    const formElements = [];
                    const linkElements = [];
                    
                    // Find all interactable elements
                    const allElements = document.querySelectorAll('*');
                    for (const el of allElements) {{
                        if (isInteractable(el)) {{
                            const analysis = analyzeElement(el, maxDepth);
                            if (analysis) {{
                                interactableElements.push(analysis);
                                
                                if (['input', 'select', 'textarea'].includes(analysis.tagName)) {{
                                    formElements.push(analysis);
                                }}
                                if (analysis.tagName === 'a' || analysis.tagName === 'button') {{
                                    linkElements.push(analysis);
                                }}
                            }}
                        }}
                    }}
                    
                    results = {{
                        pageInfo: {{
                            title: document.title,
                            url: window.location.href,
                            viewport: {{
                                width: window.innerWidth,
                                height: window.innerHeight
                            }},
                            documentSize: {{
                                width: document.documentElement.scrollWidth,
                                height: document.documentElement.scrollHeight
                            }}
                        }},
                        summary: {{
                            totalInteractable: interactableElements.length,
                            forms: formElements.length,
                            links: linkElements.length,
                            buttons: interactableElements.filter(el => el.tagName === 'button').length
                        }},
                        interactableElements: interactableElements.slice(0, 50), // Limit to prevent huge output
                        forms: formElements,
                        navigation: linkElements.slice(0, 20)
                    }};
                }}
                
                return results;
            }})()
            """
            
            results = await self.execute_js(js_code)
            logger.info(f"DOM analysis completed: {results.get('summary', {})}")
            return json.dumps(results, indent=2)
            
        except Exception as e:
            logger.error(f"Error analyzing DOM: {str(e)}")
            return f"Error analyzing DOM: {str(e)}"


# DOM Event Monitor Tool
class DOMEventMonitorTool(BrowserTool):
    """Monitor and capture DOM events for understanding page behavior"""
    
    name: str = "monitor_dom_events"
    description: str = "Monitor DOM events on the page to understand interactions and dynamic behavior"
    
    async def _arun(
        self,
        duration_ms: int = 3000,
        event_types: Optional[List[str]] = None,
        selector: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Monitor DOM events"""
        try:
            if event_types is None:
                event_types = ['click', 'input', 'change', 'focus', 'blur', 'submit', 'load', 'error']
            
            js_code = f"""
            new Promise((resolve) => {{
                    const duration = {duration_ms};
                    const eventTypes = {json.dumps(event_types)};
                    const targetSelector = {json.dumps(selector) if selector else 'null'};
                    const events = [];
                    const listeners = [];
                    
                    // Event handler
                    function captureEvent(event) {{
                        const target = event.target;
                        const eventData = {{
                            type: event.type,
                            timestamp: Date.now(),
                            target: {{
                                tagName: target.tagName?.toLowerCase(),
                                id: target.id || null,
                                className: target.className || null,
                                text: target.textContent?.trim().substring(0, 50),
                                value: target.value || null,
                                selector: generateSelector(target)
                            }},
                            bubbles: event.bubbles,
                            cancelable: event.cancelable,
                            defaultPrevented: event.defaultPrevented
                        }};
                        
                        // Add event-specific data
                        if (event.type === 'click' || event.type.includes('mouse')) {{
                            eventData.position = {{
                                clientX: event.clientX,
                                clientY: event.clientY,
                                pageX: event.pageX,
                                pageY: event.pageY
                            }};
                        }}
                        
                        if (event.type === 'input' || event.type === 'change') {{
                            eventData.value = target.value;
                        }}
                        
                        events.push(eventData);
                    }}
                    
                    // Generate selector for element
                    function generateSelector(element) {{
                        if (element.id) return `#${{element.id}}`;
                        if (element.className) return `.${{element.className.split(' ')[0]}}`;
                        return element.tagName.toLowerCase();
                    }}
                    
                    // Set up listeners
                    const root = targetSelector ? document.querySelector(targetSelector) : document;
                    if (root) {{
                        for (const eventType of eventTypes) {{
                            const listener = (e) => captureEvent(e);
                            root.addEventListener(eventType, listener, true); // Use capture
                            listeners.push({{ type: eventType, listener }});
                        }}
                    }}
                    
                    // Set up mutation observer
                    const mutations = [];
                    const observer = new MutationObserver((mutationsList) => {{
                        for (const mutation of mutationsList) {{
                            mutations.push({{
                                type: mutation.type,
                                target: generateSelector(mutation.target),
                                timestamp: Date.now(),
                                addedNodes: mutation.addedNodes.length,
                                removedNodes: mutation.removedNodes.length,
                                attributeName: mutation.attributeName,
                                oldValue: mutation.oldValue
                            }});
                        }}
                    }});
                    
                    observer.observe(root || document.body, {{
                        childList: true,
                        attributes: true,
                        subtree: true,
                        attributeOldValue: true
                    }});
                    
                    // Clean up after duration
                    setTimeout(() => {{
                        // Remove listeners
                        for (const {{ type, listener }} of listeners) {{
                            (root || document).removeEventListener(type, listener, true);
                        }}
                        
                        // Disconnect observer
                        observer.disconnect();
                        
                        // Return results
                        resolve({{
                            duration: duration,
                            eventCount: events.length,
                            mutationCount: mutations.length,
                            events: events,
                            mutations: mutations.slice(0, 50), // Limit mutations
                            summary: {{
                                byType: events.reduce((acc, e) => {{
                                    acc[e.type] = (acc[e.type] || 0) + 1;
                                    return acc;
                                }}, {{}}),
                                topTargets: [...new Set(events.map(e => e.target.selector))].slice(0, 10)
                            }}
                        }});
                    }}, duration);
            }})
            """
            
            result = await self.execute_js(js_code)
            logger.info(f"Monitored {result['eventCount']} events over {duration_ms}ms")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error monitoring events: {str(e)}")
            return f"Error monitoring events: {str(e)}"


# Data Extraction Tool
class ExtractDataTool(BrowserTool):
    """Extract multiple data points efficiently using JavaScript"""
    
    name: str = "extract_data"
    description: str = "Extract multiple data points from the page using CSS selectors"
    args_schema: Type[BaseModel] = ExtractDataSchema
    
    async def _arun(
        self,
        selectors: Dict[str, str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Extract data using JavaScript"""
        try:
            # Escape selectors for JavaScript
            escaped_selectors = {k: escape_js_string(v) for k, v in selectors.items()}
            
            js_code = f"""
            (() => {{
                const selectors = {json.dumps(escaped_selectors)};
                const results = {{}};
                
                for (const [key, selector] of Object.entries(selectors)) {{
                    try {{
                        const elements = document.querySelectorAll(selector);
                        if (elements.length === 0) {{
                            results[key] = null;
                        }} else if (elements.length === 1) {{
                            const el = elements[0];
                            results[key] = {{
                                text: el.textContent.trim(),
                                value: el.value || null,
                                href: el.href || null,
                                src: el.src || null
                            }};
                        }} else {{
                            results[key] = Array.from(elements).map(el => ({{
                                text: el.textContent.trim(),
                                value: el.value || null,
                                href: el.href || null,
                                src: el.src || null
                            }}));
                        }}
                    }} catch (error) {{
                        results[key] = {{ error: error.message }};
                    }}
                }}
                
                return results;
            }})()
            """
            
            results = await self.execute_js(js_code)
            logger.info(f"Extracted data from {len(selectors)} selectors")
            return json.dumps(results, indent=2)
            
        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            return f"Error extracting data: {str(e)}"


# Press Key Tool
class PressKeyTool(BrowserTool):
    """Press keyboard keys on elements for form submission and navigation"""
    
    name: str = "press_key"
    description: str = "Press a keyboard key on an element (e.g., Enter to submit forms, Tab to navigate)"
    args_schema: Type[BaseModel] = PressKeySchema
    
    async def _arun(
        self,
        selector: str,
        key: str = "Enter",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Press a key on the specified element"""
        try:
            js_code = f"""
            (() => {{
                const element = document.querySelector("{escape_js_string(selector)}");
                if (!element) {{
                    throw new Error('Element not found');
                }}
                
                // Focus the element first
                element.focus();
                
                // Create keyboard event based on key
                const keyCode = {{
                    'Enter': 13,
                    'Tab': 9,
                    'Escape': 27,
                    'Space': 32,
                    'ArrowUp': 38,
                    'ArrowDown': 40,
                    'ArrowLeft': 37,
                    'ArrowRight': 39
                }}["{key}"] || "{key}".charCodeAt(0);
                
                // Dispatch keyboard events
                const eventOptions = {{
                    key: "{key}",
                    keyCode: keyCode,
                    which: keyCode,
                    bubbles: true,
                    cancelable: true
                }};
                
                element.dispatchEvent(new KeyboardEvent('keydown', eventOptions));
                element.dispatchEvent(new KeyboardEvent('keypress', eventOptions));
                element.dispatchEvent(new KeyboardEvent('keyup', eventOptions));
                
                // For Enter key, also try submitting the form if it exists
                if ("{key}" === "Enter" && element.form) {{
                    element.form.submit();
                }}
                
                return `Pressed ${{"{key}"}} key on element`;
            }})()
            """
            
            result = await self.execute_js(js_code)
            logger.info(f"Pressed {key} key on element '{selector}'")
            return f"Successfully pressed {key} key on element '{selector}'"
            
        except Exception as e:
            logger.error(f"Error pressing key: {str(e)}")
            return f"Error pressing {key} key on '{selector}': {str(e)}"


# JavaScript Execution Tool
class ExecuteJavaScriptTool(BrowserTool):
    """Execute custom JavaScript code in the browser context"""
    
    name: str = "execute_javascript"
    description: str = "Execute custom JavaScript code in the browser for advanced operations"
    args_schema: Type[BaseModel] = ExecuteJavaScriptSchema
    
    async def _arun(
        self,
        code: str,
        args: Optional[List[Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute custom JavaScript"""
        try:
            result = await self.execute_js(code, *(args or []))
            logger.info("JavaScript executed successfully")
            return json.dumps({"success": True, "result": result})
        except Exception as e:
            logger.error(f"JavaScript execution error: {str(e)}")
            return json.dumps({"success": False, "error": str(e)})


# Screenshot Tool
class ScreenshotTool(BrowserTool):
    """Capture screenshots of the page or elements"""
    
    name: str = "take_screenshot"
    description: str = "Capture a screenshot of the page or a specific element"
    
    async def _arun(
        self,
        selector: Optional[str] = None,
        full_page: bool = False,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Take a screenshot"""
        page = await self.get_page()
        if not page:
            return "Error: No page context available"
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join("/app/logs", filename)
            
            if selector:
                # Wait for element and screenshot it
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    await element.screenshot(path=filepath)
                    logger.info(f"Captured screenshot of element '{selector}': {filename}")
                    return f"Screenshot saved: {filename}"
                else:
                    return f"Error: Element '{selector}' not found"
            else:
                # Screenshot page
                await page.screenshot(path=filepath, full_page=full_page)
                logger.info(f"Captured {'full page' if full_page else 'viewport'} screenshot: {filename}")
                return f"Screenshot saved: {filename}"
                
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return f"Error capturing screenshot: {str(e)}"


# Manager class for browser tools
class BrowserToolsManager:
    """Manager for browser tools that maintains page/context state"""
    
    def __init__(self, browser=None):
        self.browser = browser
        self.tools = [
            # Custom JavaScript-based tools
            ClickTool(),
            TextInputTool(),
            WaitForElementTool(),
            ScrollTool(),
            DOMMapperTool(),
            DOMEventMonitorTool(),
            ExtractDataTool(),
            PressKeyTool(),
            ExecuteJavaScriptTool(),
            ScreenshotTool(),
        ]
        
        if browser:
            for tool in self.tools:
                tool.set_browser(browser)
    
    def get_tools(self):
        """Get all browser tools"""
        return self.tools
        
    def update_page_context(self, page=None, context=None):
        """Update page and context for all tools"""
        for tool in self.tools:
            if page:
                tool.set_page(page)
            if context:
                tool.set_context(context)


# Main functions to get browser and tools
async def get_browser_toolkit() -> Tuple[Browser, Any]:
    """Create browser instance and toolkit"""
    browser_type = os.environ.get('BROWSER', 'chromium')
    # Always run in desktop mode (non-headless)
    headless = False
    
    logger.info(f"Creating browser instance: {browser_type}, desktop mode (headless={headless})")
    
    # Create browser directly with Playwright to avoid event loop issues
    playwright = await async_playwright().start()
    
    # Browser launch arguments for desktop mode with stealth
    browser_args = [
        '--start-maximized',
        '--disable-dev-shm-usage',  # Use /tmp instead of /dev/shm
        '--no-sandbox',  # Required in Docker
        '--disable-setuid-sandbox',
        '--disable-gpu',  # Disable GPU in Docker
        '--disable-software-rasterizer',
        '--disable-blink-features=AutomationControlled',  # Stealth: Remove automation flag
        '--disable-features=IsolateOrigins,site-per-process',  # Stealth: Better compatibility
        '--enable-features=NetworkService,NetworkServiceInProcess',  # Stealth: Normal browser behavior
        '--disable-web-security',  # Allow cross-origin requests
        '--allow-running-insecure-content',  # Allow mixed content
        '--disable-features=CrossSiteDocumentBlockingIfIsolating',
        '--disable-site-isolation-trials',
        '--disable-features=AudioServiceOutOfProcess',
        '--disable-features=CalculateNativeWinOcclusion',
        '--disable-features=OptimizationHints',
        '--disable-features=RendererCodeIntegrity',
        '--disable-features=Translate',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--disable-features=ScriptStreaming',
        '--disable-hang-monitor',
        '--disable-ipc-flooding-protection',
        '--disable-prompt-on-repost',
        '--metrics-recording-only',
        '--disable-blink-features=AutomationControlled',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    # Launch browser based on type
    if browser_type == 'firefox':
        browser = await playwright.firefox.launch(
            headless=headless,
            args=browser_args if browser_type == 'chromium' else None
        )
    elif browser_type == 'webkit':
        browser = await playwright.webkit.launch(
            headless=headless
        )
    else:  # default to chromium
        browser = await playwright.chromium.launch(
            headless=headless,
            args=browser_args
        )
    
    # Get the default context and page
    contexts = browser.contexts
    if contexts:
        context = contexts[0]
        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = await context.new_page()
    else:
        # Create context with stealth-optimized settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation', 'notifications'],
            color_scheme='light',
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            }
        )
        page = await context.new_page()
    
    # Apply stealth to the browser
    logger.info("Applying stealth configuration to browser...")
    stealth_config = StealthConfig(
        enable_all=True,
        locale='en-US',
        fix_hairline=True,
        mask_tcp_rtt=True,
        mask_network_info=True
    )
    await apply_stealth(browser, stealth_config)
    
    # Create standard toolkit with page
    from langchain_community.agent_toolkits.playwright.toolkit import PlayWrightBrowserToolkit
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    
    # Update the sync browser reference to use the page
    if hasattr(toolkit, 'sync_browser') and toolkit.sync_browser:
        toolkit.sync_browser.current_page = page
    
    logger.info(f"Browser created with stealth: {browser_type}, headless={headless}")
    
    # Get standard tools
    standard_tools = toolkit.get_tools()
    logger.info("Browser toolkit created with tools:")
    for tool in standard_tools:
        logger.info(f"  - {tool.name}: {tool.description}")
    
    return browser, toolkit


def get_custom_browser_tools(browser=None):
    """Get custom browser automation tools"""
    manager = BrowserToolsManager(browser)
    return manager.get_tools()