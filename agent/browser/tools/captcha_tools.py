"""
Enhanced browser tools with CAPTCHA detection
"""

import json
from typing import Optional, Any
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_community.tools.playwright import NavigateTool as BaseNavigateTool
from pydantic import BaseModel, Field
from playwright.async_api import Page
from agent.browser.stealth.captcha_handler import CaptchaDetector
from ...utils.logger import get_logger

logger = get_logger('enhanced_browser_tools')


class NavigateToolInput(BaseModel):
    """Input for NavigateTool with CAPTCHA awareness"""
    url: str = Field(..., description="The URL to navigate to")


class NavigateToolWithCaptchaDetection(BaseNavigateTool):
    """Enhanced navigation tool that detects CAPTCHAs"""
    
    name: str = "navigate_browser"
    description: str = """Navigate to a URL and detect if CAPTCHA is present.
    
    Args:
        url: The URL to navigate to
        
    Returns:
        Result of navigation including CAPTCHA detection
    """
    args_schema: type[BaseModel] = NavigateToolInput
    
    def _run(
        self,
        url: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the sync version"""
        raise NotImplementedError("Use async version")
    
    async def _arun(
        self,
        url: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Navigate to URL and check for CAPTCHA"""
        if self.sync_browser is None:
            raise ValueError(f"Synchronous browser not provided to {self.name}")
        
        page = self.sync_browser
        
        try:
            # Navigate to the URL
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=5000)
            
            # Check for CAPTCHA
            captcha_result = await CaptchaDetector.check_for_captcha(page)
            
            if captcha_result["detected"]:
                logger.warning(f"CAPTCHA detected on {url}: {captcha_result}")
                return (
                    f"⚠️ CAPTCHA DETECTED!\n"
                    f"Type: {captcha_result['type']}\n"
                    f"Message: {captcha_result['message']}\n"
                    f"Current URL: {page.url}\n"
                    f"Action Required: Please solve the CAPTCHA manually in the browser window."
                )
            
            # Normal navigation result
            return f"Navigated to {page.url}"
            
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            
            # Check if error might be CAPTCHA-related
            error_msg = str(e).lower()
            if any(word in error_msg for word in ['captcha', 'cloudflare', 'forbidden', 'blocked']):
                # Double-check for CAPTCHA
                try:
                    captcha_result = await CaptchaDetector.check_for_captcha(page)
                    if captcha_result["detected"]:
                        return (
                            f"⚠️ Navigation blocked by CAPTCHA!\n"
                            f"Type: {captcha_result['type']}\n"
                            f"Error: {str(e)}"
                        )
                except:
                    pass
            
            return f"Error navigating to {url}: {str(e)}"


class AnalyzeDOMWithCaptchaCheck(BaseModel):
    """Enhanced DOM analysis that includes CAPTCHA detection"""
    
    name: str = "analyze_dom"
    description: str = """Analyze the current page DOM and check for CAPTCHAs.
    
    Returns:
        Analysis including DOM structure and CAPTCHA status
    """
    
    async def run(self, page: Page) -> str:
        """Analyze DOM and check for CAPTCHA"""
        try:
            # First check for CAPTCHA
            captcha_result = await CaptchaDetector.check_for_captcha(page)
            
            if captcha_result["detected"]:
                return (
                    f"⚠️ CAPTCHA DETECTED - Cannot analyze DOM properly!\n"
                    f"Type: {captcha_result['type']}\n"
                    f"Message: {captcha_result['message']}\n"
                    f"Please solve the CAPTCHA first."
                )
            
            # Normal DOM analysis
            dom_info = await page.evaluate("""() => {
                const getElementInfo = (element, depth = 0, maxDepth = 3) => {
                    if (depth > maxDepth) return null;
                    
                    const info = {
                        tag: element.tagName,
                        id: element.id || null,
                        classes: element.className ? element.className.split(' ').filter(c => c) : [],
                        text: element.textContent ? element.textContent.substring(0, 50) : null,
                        attributes: {}
                    };
                    
                    // Get important attributes
                    ['href', 'src', 'type', 'name', 'value', 'placeholder'].forEach(attr => {
                        if (element.hasAttribute(attr)) {
                            info.attributes[attr] = element.getAttribute(attr);
                        }
                    });
                    
                    return info;
                };
                
                // Get key elements
                const forms = Array.from(document.querySelectorAll('form')).map(f => getElementInfo(f));
                const buttons = Array.from(document.querySelectorAll('button, input[type="submit"]')).map(b => getElementInfo(b));
                const links = Array.from(document.querySelectorAll('a')).slice(0, 10).map(a => getElementInfo(a));
                const inputs = Array.from(document.querySelectorAll('input, textarea')).map(i => getElementInfo(i));
                
                return {
                    title: document.title,
                    url: window.location.href,
                    forms: forms,
                    buttons: buttons,
                    links: links,
                    inputs: inputs
                };
            }""")
            
            return f"DOM Analysis:\n{json.dumps(dom_info, indent=2)}"
            
        except Exception as e:
            logger.error(f"DOM analysis error: {e}")
            return f"Error analyzing DOM: {str(e)}"