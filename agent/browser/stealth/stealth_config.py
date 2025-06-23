"""
Main stealth configuration and application
"""

import random
from typing import Optional, Dict, Any, List
from playwright.async_api import Page, BrowserContext, Browser
from ...utils.logger import get_logger
from .evasions import EVASIONS

logger = get_logger('stealth')


class StealthConfig:
    """Configuration for stealth mode"""
    
    def __init__(
        self,
        enable_all: bool = True,
        evasions: Optional[List[str]] = None,
        vendor: Optional[str] = None,
        renderer: Optional[str] = None,
        fix_hairline: bool = True,
        run_on_insecure_origins: bool = False,
        user_agent: Optional[str] = None,
        locale: Optional[str] = None,
        mask_tcp_rtt: bool = True,
        mask_network_info: bool = True
    ):
        self.enable_all = enable_all
        self.evasions = evasions or []
        self.vendor = vendor
        self.renderer = renderer
        self.fix_hairline = fix_hairline
        self.run_on_insecure_origins = run_on_insecure_origins
        self.user_agent = user_agent
        self.locale = locale
        self.mask_tcp_rtt = mask_tcp_rtt
        self.mask_network_info = mask_network_info
        
        # Set defaults if not provided
        if not self.vendor:
            self.vendor = random.choice(['Google Inc.', 'Intel Inc.'])
        if not self.renderer:
            renderers = [
                'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)',
                'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)',
                'ANGLE (AMD, AMD Radeon RX 6600 Direct3D11 vs_5_0 ps_5_0)'
            ]
            self.renderer = random.choice(renderers)
            
        logger.info(f"StealthConfig initialized: enable_all={enable_all}, evasions={len(evasions or [])}")


async def apply_stealth(
    target: Any,  # Can be Page, BrowserContext, or Browser
    config: Optional[StealthConfig] = None
) -> None:
    """Apply stealth techniques to browser, context, or page"""
    
    if config is None:
        config = StealthConfig()
    
    logger.info(f"Applying stealth to {type(target).__name__}")
    
    # Determine what type of target we have
    pages = []
    contexts = []
    
    if isinstance(target, Page):
        pages = [target]
        contexts = [target.context] if hasattr(target, 'context') else []
    elif isinstance(target, BrowserContext):
        contexts = [target]
        pages = target.pages
    elif isinstance(target, Browser):
        contexts = target.contexts
        for context in contexts:
            pages.extend(context.pages)
    
    # Apply context-level patches
    for context in contexts:
        await _apply_context_patches(context, config)
    
    # Apply page-level patches
    for page in pages:
        await _apply_page_patches(page, config)
        
    # Set up listeners for new pages
    for context in contexts:
        context.on('page', lambda page: _on_new_page(page, config))
    
    logger.info("Stealth patches applied successfully")


async def _apply_context_patches(context: BrowserContext, config: StealthConfig) -> None:
    """Apply context-level stealth patches"""
    
    # Set viewport to common sizes
    viewports = [
        {'width': 1920, 'height': 1080},
        {'width': 1366, 'height': 768},
        {'width': 1536, 'height': 864},
        {'width': 1440, 'height': 900}
    ]
    viewport = random.choice(viewports)
    # Viewport is set on page level, not context level
    
    # Set realistic geolocation if needed
    if config.mask_network_info:
        # Common locations
        locations = [
            {'latitude': 37.7749, 'longitude': -122.4194},  # San Francisco
            {'latitude': 40.7128, 'longitude': -74.0060},   # New York
            {'latitude': 51.5074, 'longitude': -0.1278},    # London
            {'latitude': 48.8566, 'longitude': 2.3522},     # Paris
        ]
        location = random.choice(locations)
        await context.set_geolocation(location)
        await context.grant_permissions(['geolocation'])
    
    # Set locale
    if config.locale:
        await context.set_extra_http_headers({
            'Accept-Language': config.locale
        })
    
    logger.debug(f"Applied context patches: viewport={viewport}")


async def _apply_page_patches(page: Page, config: StealthConfig) -> None:
    """Apply page-level stealth patches"""
    
    # Set viewport size
    viewports = [
        {'width': 1920, 'height': 1080},
        {'width': 1366, 'height': 768},
        {'width': 1536, 'height': 864},
        {'width': 1440, 'height': 900}
    ]
    viewport = random.choice(viewports)
    await page.set_viewport_size(viewport)
    
    # Determine which evasions to apply
    evasions_to_apply = []
    
    if config.enable_all:
        evasions_to_apply = list(EVASIONS.keys())
    else:
        evasions_to_apply = config.evasions
    
    # Apply each evasion
    for evasion_name in evasions_to_apply:
        if evasion_name in EVASIONS:
            try:
                evasion_func = EVASIONS[evasion_name]
                await evasion_func(page, config)
                logger.debug(f"Applied evasion: {evasion_name}")
            except Exception as e:
                logger.error(f"Failed to apply evasion {evasion_name}: {e}")
    
    # Apply additional patches
    await _apply_additional_patches(page, config)
    
    logger.debug(f"Applied {len(evasions_to_apply)} evasions to page")


async def _apply_additional_patches(page: Page, config: StealthConfig) -> None:
    """Apply additional stealth patches"""
    
    # Remove automation-related properties
    await page.add_init_script("""
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Fix permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Fix chrome runtime
        if (!window.chrome) {
            window.chrome = {};
        }
        
        if (!window.chrome.runtime) {
            window.chrome.runtime = {};
        }
        
        // Fix hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 4 + Math.floor(Math.random() * 4)
        });
        
        // Fix platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });
    """)


async def _on_new_page(page: Page, config: StealthConfig) -> None:
    """Handle new pages created in the context"""
    try:
        await _apply_page_patches(page, config)
        logger.debug("Applied stealth to new page")
    except Exception as e:
        logger.error(f"Failed to apply stealth to new page: {e}")