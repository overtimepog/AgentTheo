"""
CAPTCHA Detection and Handling Module
"""

import logging
from typing import Optional, Dict, Any
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class CaptchaDetector:
    """Detects various types of CAPTCHAs and security checks"""
    
    # Common CAPTCHA indicators
    CAPTCHA_SELECTORS = [
        # Google reCAPTCHA
        'iframe[src*="recaptcha"]',
        'div.g-recaptcha',
        '#g-recaptcha',
        '.g-recaptcha',
        
        # hCaptcha
        'iframe[src*="hcaptcha"]',
        'div.h-captcha',
        '.h-captcha',
        
        # Cloudflare
        'div.cf-challenge',
        '#challenge-form',
        'form#challenge-form',
        
        # Generic CAPTCHA
        'img[src*="captcha"]',
        'div[class*="captcha"]',
        'input[name*="captcha"]',
        '#captcha',
        '.captcha'
    ]
    
    # Security check text patterns
    SECURITY_TEXT_PATTERNS = [
        'security check',
        'verify you are human',
        'confirm you are not a robot',
        'complete the captcha',
        'solve the puzzle',
        'cloudflare ray id',
        'access denied',
        'forbidden',
        'checking your browser'
    ]
    
    @classmethod
    async def check_for_captcha(cls, page: Page) -> Dict[str, Any]:
        """
        Check if the current page contains a CAPTCHA
        
        Returns:
            Dict containing:
            - detected: bool - Whether a CAPTCHA was detected
            - type: str - Type of CAPTCHA (if detected)
            - message: str - Description of what was found
        """
        result = {
            "detected": False,
            "type": None,
            "message": "",
            "selectors_found": []
        }
        
        try:
            # Check for CAPTCHA selectors
            for selector in cls.CAPTCHA_SELECTORS:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        result["detected"] = True
                        result["selectors_found"].append(selector)
                        
                        # Determine CAPTCHA type
                        if 'recaptcha' in selector:
                            result["type"] = "reCAPTCHA"
                        elif 'hcaptcha' in selector:
                            result["type"] = "hCaptcha"
                        elif 'cloudflare' in selector or 'cf-challenge' in selector:
                            result["type"] = "Cloudflare"
                        else:
                            result["type"] = "Generic"
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
            
            # Check page content for security text
            if not result["detected"]:
                try:
                    page_text = await page.content()
                    page_text_lower = page_text.lower()
                    
                    for pattern in cls.SECURITY_TEXT_PATTERNS:
                        if pattern in page_text_lower:
                            result["detected"] = True
                            result["type"] = "Security Check"
                            result["message"] = f"Found security pattern: '{pattern}'"
                            break
                except Exception as e:
                    logger.debug(f"Error checking page text: {e}")
            
            # Check page title
            if not result["detected"]:
                try:
                    title = await page.title()
                    title_lower = title.lower()
                    
                    if any(word in title_lower for word in ['captcha', 'security', 'blocked', 'forbidden']):
                        result["detected"] = True
                        result["type"] = "Security Page"
                        result["message"] = f"Suspicious page title: '{title}'"
                except Exception as e:
                    logger.debug(f"Error checking page title: {e}")
            
            # Set final message
            if result["detected"]:
                if not result["message"]:
                    result["message"] = f"{result['type']} detected on page"
                logger.warning(f"CAPTCHA detected: {result['message']}")
            
        except Exception as e:
            logger.error(f"Error during CAPTCHA detection: {e}")
            result["message"] = f"Error during detection: {str(e)}"
        
        return result
    
    @classmethod
    async def wait_for_manual_solve(cls, page: Page, timeout: int = 300000) -> bool:
        """
        Wait for user to manually solve CAPTCHA
        
        Args:
            page: The page containing the CAPTCHA
            timeout: Maximum time to wait in milliseconds (default: 5 minutes)
            
        Returns:
            bool: True if CAPTCHA appears to be solved, False if timeout
        """
        logger.info("Waiting for manual CAPTCHA solution...")
        
        try:
            # Wait for CAPTCHA elements to disappear
            for selector in cls.CAPTCHA_SELECTORS:
                try:
                    await page.wait_for_selector(
                        selector,
                        state="hidden",
                        timeout=timeout
                    )
                    logger.info(f"CAPTCHA element {selector} disappeared")
                    return True
                except:
                    continue
            
            # If no specific CAPTCHA element found, wait for navigation
            initial_url = page.url
            
            # Wait for URL change or new content
            await page.wait_for_function(
                f"() => window.location.href !== '{initial_url}'",
                timeout=timeout
            )
            
            logger.info("Page navigated after CAPTCHA")
            return True
            
        except Exception as e:
            logger.error(f"Timeout waiting for CAPTCHA solution: {e}")
            return False


class CaptchaHandler:
    """Handles CAPTCHA situations"""
    
    def __init__(self):
        self.detector = CaptchaDetector()
        self.captcha_encountered = False
        self.last_captcha_type = None
    
    async def handle_page(self, page: Page) -> Dict[str, Any]:
        """
        Check page for CAPTCHA and handle appropriately
        
        Returns:
            Dict with handling result
        """
        # Detect CAPTCHA
        detection_result = await CaptchaDetector.check_for_captcha(page)
        
        if not detection_result["detected"]:
            return {
                "success": True,
                "captcha_found": False,
                "message": "No CAPTCHA detected"
            }
        
        # CAPTCHA detected
        self.captcha_encountered = True
        self.last_captcha_type = detection_result["type"]
        
        logger.warning(f"CAPTCHA detected: {detection_result}")
        
        # For now, we'll notify the user and wait for manual solving
        # In the future, this could integrate with CAPTCHA solving services
        
        result = {
            "success": False,
            "captcha_found": True,
            "captcha_type": detection_result["type"],
            "message": f"CAPTCHA detected: {detection_result['message']}. Manual intervention required.",
            "action_required": "Please solve the CAPTCHA in the browser window"
        }
        
        # Optional: Wait for manual solution
        # solved = await CaptchaDetector.wait_for_manual_solve(page)
        # if solved:
        #     result["success"] = True
        #     result["message"] = "CAPTCHA appears to be solved"
        
        return result