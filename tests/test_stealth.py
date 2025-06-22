#!/usr/bin/env python3
"""
Test stealth implementation
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools.browser_tools import get_browser_toolkit
from agent.stealth import apply_stealth, StealthConfig


async def test_stealth_detection():
    """Test stealth against common detection methods"""
    print("Testing stealth implementation...")
    
    browser, toolkit = await get_browser_toolkit()
    
    # Get the first page
    contexts = browser.contexts
    if contexts:
        context = contexts[0]
        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = await context.new_page()
    else:
        context = await browser.new_context()
        page = await context.new_page()
    
    try:
        # Test 1: Bot detection test
        print("\n1. Testing bot.sannysoft.com...")
        await page.goto('https://bot.sannysoft.com/')
        await page.wait_for_timeout(2000)
        
        # Check for webdriver detection
        webdriver_result = await page.evaluate('navigator.webdriver')
        print(f"   - navigator.webdriver: {webdriver_result} (should be undefined)")
        
        # Test 2: Check Chrome object
        print("\n2. Testing Chrome object...")
        chrome_exists = await page.evaluate('typeof window.chrome !== "undefined"')
        chrome_runtime = await page.evaluate('typeof window.chrome.runtime !== "undefined"')
        print(f"   - window.chrome exists: {chrome_exists}")
        print(f"   - window.chrome.runtime exists: {chrome_runtime}")
        
        # Test 3: Check plugins
        print("\n3. Testing plugins...")
        plugins_length = await page.evaluate('navigator.plugins.length')
        print(f"   - navigator.plugins.length: {plugins_length} (should be > 0)")
        
        # Test 4: Check languages
        print("\n4. Testing languages...")
        languages = await page.evaluate('navigator.languages')
        print(f"   - navigator.languages: {languages}")
        
        # Test 5: Check WebGL
        print("\n5. Testing WebGL...")
        try:
            webgl_vendor = await page.evaluate("""
                () => {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (!gl) return 'WebGL not supported';
                    
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    if (!debugInfo) return 'Debug info not available';
                    
                    return gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                }
            """)
            print(f"   - WebGL vendor: {webgl_vendor}")
        except Exception as e:
            print(f"   - WebGL test error: {e}")
        
        # Test 6: Check permissions
        print("\n6. Testing permissions...")
        notification_permission = await page.evaluate("""
            () => navigator.permissions.query({name: 'notifications'})
                .then(result => result.state)
        """)
        print(f"   - Notification permission: {notification_permission}")
        
        # Test 7: Take screenshot of detection page
        print("\n7. Taking screenshot of detection results...")
        await page.screenshot(path='tests/stealth_test_results.png')
        print("   - Screenshot saved to tests/stealth_test_results.png")
        
        # Test 8: Test against intoli
        print("\n8. Testing intoli.com/blog/not-possible-to-block-chrome-headless...")
        await page.goto('https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html')
        await page.wait_for_timeout(2000)
        
        # Check if detected
        detected = await page.evaluate("""
            () => {
                const element = document.querySelector('.result');
                return element ? element.textContent.includes('Chrome headless detected') : 'unknown';
            }
        """)
        print(f"   - Detection result: {detected}")
        
        # Test 9: Check user agent
        print("\n9. Testing user agent...")
        user_agent = await page.evaluate('navigator.userAgent')
        print(f"   - User agent: {user_agent}")
        
        # Test 10: Check screen dimensions
        print("\n10. Testing screen dimensions...")
        screen_info = await page.evaluate("""
            () => ({
                width: window.screen.width,
                height: window.screen.height,
                availWidth: window.screen.availWidth,
                availHeight: window.screen.availHeight,
                colorDepth: window.screen.colorDepth,
                pixelDepth: window.screen.pixelDepth
            })
        """)
        print(f"   - Screen info: {screen_info}")
        
        print("\n✓ Stealth tests completed!")
        
    except Exception as e:
        print(f"\n✗ Error during stealth testing: {e}")
        raise
    finally:
        await browser.close()


async def test_google_search():
    """Test stealth with actual Google search"""
    print("\n\nTesting Google search with stealth...")
    
    browser, toolkit = await get_browser_toolkit()
    
    # Get page
    contexts = browser.contexts
    if contexts:
        context = contexts[0]
        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = await context.new_page()
    else:
        context = await browser.new_context()
        page = await context.new_page()
    
    try:
        print("1. Navigating to Google...")
        await page.goto('https://www.google.com')
        await page.wait_for_timeout(2000)
        
        # Check if we hit a CAPTCHA
        captcha_present = await page.evaluate("""
            () => {
                const captchaIndicators = [
                    'recaptcha',
                    'captcha',
                    'challenge',
                    'verify you are human',
                    'unusual traffic'
                ];
                const pageText = document.body.innerText.toLowerCase();
                return captchaIndicators.some(indicator => pageText.includes(indicator));
            }
        """)
        
        if captcha_present:
            print("   ✗ CAPTCHA detected on Google!")
            await page.screenshot(path='tests/google_captcha.png')
            print("   - Screenshot saved to tests/google_captcha.png")
        else:
            print("   ✓ No CAPTCHA detected!")
            
            # Try a search
            print("2. Performing search...")
            search_box = await page.query_selector('input[name="q"]')
            if search_box:
                await search_box.type("playwright automation", delay=100)
                await page.keyboard.press('Enter')
                await page.wait_for_timeout(3000)
                
                # Check results
                results = await page.query_selector_all('h3')
                print(f"   - Found {len(results)} search results")
                
                await page.screenshot(path='tests/google_search_results.png')
                print("   - Screenshot saved to tests/google_search_results.png")
            else:
                print("   ✗ Could not find search box")
                
        print("\n✓ Google search test completed!")
        
    except Exception as e:
        print(f"\n✗ Error during Google search test: {e}")
        await page.screenshot(path='tests/google_error.png')
        print("   - Error screenshot saved to tests/google_error.png")
        raise
    finally:
        await browser.close()


async def main():
    """Run all stealth tests"""
    print("Running Browser Stealth tests...\n")
    
    # Create tests directory if it doesn't exist
    os.makedirs('tests', exist_ok=True)
    
    await test_stealth_detection()
    await test_google_search()
    
    print("\n\nAll stealth tests completed!")
    print("Check the screenshots in the tests/ directory for visual results.")


if __name__ == "__main__":
    # Set test environment
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['BROWSER'] = 'chromium'
    
    asyncio.run(main())