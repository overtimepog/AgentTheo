"""
Collection of evasion techniques for browser stealth
Each evasion targets specific detection methods
"""

from typing import Dict, Callable, Any
from playwright.async_api import Page
from ..utils.logger import get_logger

logger = get_logger('stealth.evasions')


async def webdriver_evasion(page: Page, config: Any) -> None:
    """Remove webdriver property and related indicators"""
    await page.add_init_script("""
        // Remove webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Remove webdriver in other contexts
        if (navigator.webdriver === true) {
            delete Object.getPrototypeOf(navigator).webdriver;
        }
        
        // Remove automation controlled flag
        delete navigator.__proto__.webdriver;
    """)


async def chrome_runtime_evasion(page: Page, config: Any) -> None:
    """Fix chrome runtime to appear like a real Chrome browser"""
    await page.add_init_script("""
        // Create convincing chrome object
        if (!window.chrome) {
            window.chrome = {};
        }
        
        // Add chrome.runtime with common properties
        window.chrome.runtime = {
            id: undefined,
            onMessage: {
                addListener: function() {}
            },
            onConnect: {
                addListener: function() {}
            },
            onInstalled: {
                addListener: function() {}
            },
            getManifest: function() {
                return undefined;
            },
            getURL: function() {
                return undefined;
            }
        };
        
        // Add chrome.app
        window.chrome.app = {
            InstallState: {
                DISABLED: 'disabled',
                INSTALLED: 'installed',
                NOT_INSTALLED: 'not_installed'
            },
            RunningState: {
                CANNOT_RUN: 'cannot_run',
                READY_TO_RUN: 'ready_to_run',
                RUNNING: 'running'
            },
            getDetails: () => null,
            getIsInstalled: () => false,
            installState: () => 'not_installed'
        };
        
        // Add chrome.csi
        window.chrome.csi = function() {
            return {
                startE: Date.now(),
                onloadT: Date.now() + Math.random() * 100,
                pageT: Date.now() + Math.random() * 1000,
                tran: 15
            };
        };
        
        // Add chrome.loadTimes
        window.chrome.loadTimes = function() {
            return {
                requestTime: Date.now() / 1000,
                startLoadTime: Date.now() / 1000 + Math.random(),
                commitLoadTime: Date.now() / 1000 + Math.random() * 2,
                finishDocumentLoadTime: Date.now() / 1000 + Math.random() * 3,
                finishLoadTime: Date.now() / 1000 + Math.random() * 4,
                firstPaintTime: Date.now() / 1000 + Math.random() * 2,
                firstPaintAfterLoadTime: 0,
                navigationType: 'Other',
                wasFetchedViaSpdy: false,
                wasNpnNegotiated: true,
                npnNegotiatedProtocol: 'http/1.1',
                wasAlternateProtocolAvailable: false,
                connectionInfo: 'http/1.1'
            };
        };
    """)


async def webgl_vendor_evasion(page: Page, config: Any) -> None:
    """Spoof WebGL vendor and renderer strings"""
    vendor = config.vendor
    renderer = config.renderer
    
    await page.add_init_script(f"""
        // Override WebGL vendor and renderer
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) {{
                return '{vendor}';
            }}
            if (parameter === 37446) {{
                return '{renderer}';
            }}
            return getParameter.apply(this, arguments);
        }};
        
        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) {{
                return '{vendor}';
            }}
            if (parameter === 37446) {{
                return '{renderer}';
            }}
            return getParameter2.apply(this, arguments);
        }};
        
        // Fix WEBGL_debug_renderer_info
        const debugInfo = {{
            UNMASKED_VENDOR_WEBGL: 37445,
            UNMASKED_RENDERER_WEBGL: 37446
        }};
        
        Object.defineProperty(debugInfo, 'UNMASKED_VENDOR_WEBGL', {{
            get: function() {{ return 37445; }}
        }});
        
        Object.defineProperty(debugInfo, 'UNMASKED_RENDERER_WEBGL', {{
            get: function() {{ return 37446; }}
        }});
    """)


async def plugins_evasion(page: Page, config: Any) -> None:
    """Add realistic browser plugins"""
    await page.add_init_script("""
        // Create realistic plugins array
        const pluginsData = [
            {
                name: 'Chrome PDF Plugin',
                filename: 'internal-pdf-viewer',
                description: 'Portable Document Format'
            },
            {
                name: 'Chrome PDF Viewer',
                filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                description: ''
            },
            {
                name: 'Native Client',
                filename: 'internal-nacl-plugin',
                description: ''
            }
        ];
        
        // Create plugin objects
        const plugins = [];
        pluginsData.forEach(data => {
            const plugin = {
                name: data.name,
                filename: data.filename,
                description: data.description,
                length: 1,
                item: function(index) {
                    return this[0];
                },
                namedItem: function(name) {
                    return this[0];
                },
                0: {
                    type: 'application/x-google-chrome-pdf',
                    suffixes: 'pdf',
                    description: data.description,
                    enabledPlugin: true
                }
            };
            plugins.push(plugin);
        });
        
        // Override navigator.plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => plugins
        });
        
        // Override navigator.mimeTypes
        const mimeTypes = [
            {
                type: 'application/pdf',
                suffixes: 'pdf',
                description: '',
                enabledPlugin: plugins[0]
            },
            {
                type: 'application/x-google-chrome-pdf',
                suffixes: 'pdf',
                description: 'Portable Document Format',
                enabledPlugin: plugins[1]
            }
        ];
        
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => mimeTypes
        });
    """)


async def languages_evasion(page: Page, config: Any) -> None:
    """Set realistic language preferences"""
    locale = config.locale or 'en-US'
    
    await page.add_init_script(f"""
        // Override navigator.languages
        Object.defineProperty(navigator, 'languages', {{
            get: () => ['{locale}', '{locale.split('-')[0]}']
        }});
        
        // Override navigator.language
        Object.defineProperty(navigator, 'language', {{
            get: () => '{locale}'
        }});
    """)


async def permissions_evasion(page: Page, config: Any) -> None:
    """Fix permissions API to appear normal"""
    await page.add_init_script("""
        // Override permissions.query
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => {
            // Handle common permission queries
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            if (parameters.name === 'push') {
                return Promise.resolve({ state: 'prompt' });
            }
            if (parameters.name === 'midi') {
                return Promise.resolve({ state: 'granted' });
            }
            return originalQuery(parameters);
        };
    """)


async def media_codecs_evasion(page: Page, config: Any) -> None:
    """Fix media codec support to appear normal"""
    await page.add_init_script("""
        // Override media codecs support
        const videoElement = document.createElement('video');
        const audioElement = document.createElement('audio');
        
        // Common video codecs
        const videoCodecs = {
            'ogg': 'video/ogg; codecs="theora"',
            'h264': 'video/mp4; codecs="avc1.42E01E"',
            'webm': 'video/webm; codecs="vp8, vorbis"',
            'vp9': 'video/webm; codecs="vp9"',
            'hls': 'application/x-mpegURL; codecs="avc1.42E01E"'
        };
        
        // Common audio codecs
        const audioCodecs = {
            'ogg': 'audio/ogg; codecs="vorbis"',
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav; codecs="1"',
            'mp4': 'audio/mp4; codecs="mp4a.40.2"',
            'webm': 'audio/webm; codecs="vorbis"'
        };
        
        // Override canPlayType for video
        const originalVideoCanPlayType = videoElement.canPlayType;
        videoElement.canPlayType = function(type) {
            if (type in videoCodecs) {
                return 'probably';
            }
            return originalVideoCanPlayType.call(this, type);
        };
        
        // Override canPlayType for audio
        const originalAudioCanPlayType = audioElement.canPlayType;
        audioElement.canPlayType = function(type) {
            if (type in audioCodecs) {
                return 'probably';
            }
            return originalAudioCanPlayType.call(this, type);
        };
    """)


async def iframe_contentwindow_evasion(page: Page, config: Any) -> None:
    """Fix iframe contentWindow to appear normal"""
    await page.add_init_script("""
        // Fix iframe contentWindow
        const originalContentWindow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
        
        Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
            get: function() {
                const window = originalContentWindow.get.call(this);
                if (window) {
                    // Ensure the iframe window has the same patches
                    if (!window.chrome) {
                        window.chrome = parent.chrome;
                    }
                    
                    Object.defineProperty(window.navigator, 'webdriver', {
                        get: () => undefined
                    });
                }
                return window;
            }
        });
    """)


async def hairline_fix_evasion(page: Page, config: Any) -> None:
    """Fix hairline rendering issues in headless mode"""
    if config.fix_hairline:
        await page.add_init_script("""
            // Fix getComputedStyle to prevent hairline detection
            const originalGetComputedStyle = window.getComputedStyle;
            window.getComputedStyle = function(element, pseudoElement) {
                const style = originalGetComputedStyle.call(this, element, pseudoElement);
                
                // Fix common detection points
                if (element && element.tagName && element.tagName.toLowerCase() === 'iframe') {
                    const descriptor = Object.getOwnPropertyDescriptor(style, 'width');
                    if (descriptor && descriptor.get) {
                        // Return integer values to prevent subpixel detection
                        const originalGet = descriptor.get;
                        descriptor.get = function() {
                            const value = originalGet.call(this);
                            if (value && value.includes('.')) {
                                return Math.round(parseFloat(value)) + 'px';
                            }
                            return value;
                        };
                        Object.defineProperty(style, 'width', descriptor);
                    }
                }
                
                return style;
            };
        """)


async def user_agent_evasion(page: Page, config: Any) -> None:
    """Set a realistic user agent"""
    if config.user_agent:
        await page.add_init_script(f"""
            // Override user agent
            Object.defineProperty(navigator, 'userAgent', {{
                get: () => '{config.user_agent}'
            }});
        """)


async def network_info_evasion(page: Page, config: Any) -> None:
    """Mask network information to appear normal"""
    if config.mask_network_info:
        await page.add_init_script("""
            // Override network information API
            if ('connection' in navigator) {
                Object.defineProperty(navigator.connection, 'rtt', {
                    get: () => 50 + Math.floor(Math.random() * 100)
                });
                
                Object.defineProperty(navigator.connection, 'downlink', {
                    get: () => 10 + Math.floor(Math.random() * 20)
                });
                
                Object.defineProperty(navigator.connection, 'effectiveType', {
                    get: () => '4g'
                });
                
                Object.defineProperty(navigator.connection, 'saveData', {
                    get: () => false
                });
            }
        """)


async def battery_api_evasion(page: Page, config: Any) -> None:
    """Mock battery API to appear normal"""
    await page.add_init_script("""
        // Mock battery API
        if ('getBattery' in navigator) {
            navigator.getBattery = async () => {
                return {
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 0.7 + Math.random() * 0.3,
                    addEventListener: () => {},
                    removeEventListener: () => {}
                };
            };
        }
    """)


async def device_memory_evasion(page: Page, config: Any) -> None:
    """Set realistic device memory"""
    await page.add_init_script("""
        // Override device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
    """)


async def hardware_concurrency_evasion(page: Page, config: Any) -> None:
    """Set realistic hardware concurrency"""
    await page.add_init_script("""
        // Override hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 4 + Math.floor(Math.random() * 4)
        });
    """)


# Collection of all evasions
EVASIONS: Dict[str, Callable] = {
    'webdriver': webdriver_evasion,
    'chrome_runtime': chrome_runtime_evasion,
    'webgl_vendor': webgl_vendor_evasion,
    'plugins': plugins_evasion,
    'languages': languages_evasion,
    'permissions': permissions_evasion,
    'media_codecs': media_codecs_evasion,
    'iframe_contentwindow': iframe_contentwindow_evasion,
    'hairline_fix': hairline_fix_evasion,
    'user_agent': user_agent_evasion,
    'network_info': network_info_evasion,
    'battery_api': battery_api_evasion,
    'device_memory': device_memory_evasion,
    'hardware_concurrency': hardware_concurrency_evasion,
}