# Browser Stealth Implementation

This document describes the stealth techniques implemented to avoid CAPTCHA detection and bypass anti-bot measures.

## Overview

The stealth implementation is designed to make the Playwright browser automation appear as a regular user-controlled browser, preventing detection by services like Google, Cloudflare, and other anti-bot systems.

## Features

### 1. Core Evasions
- **WebDriver Property Removal**: Removes `navigator.webdriver` property
- **Chrome Runtime Emulation**: Creates convincing `window.chrome` object with runtime, app, csi, and loadTimes
- **WebGL Spoofing**: Randomizes WebGL vendor and renderer strings
- **Plugin Emulation**: Adds realistic browser plugins (PDF viewer, Native Client)
- **Language Configuration**: Sets realistic language preferences
- **Permissions API**: Fixes permissions.query responses
- **Media Codecs**: Reports support for common media codecs
- **Hardware Properties**: Randomizes hardware concurrency, device memory
- **Network Information**: Masks connection details (RTT, downlink, effectiveType)
- **Battery API**: Provides realistic battery status

### 2. Browser Launch Arguments
```python
--disable-blink-features=AutomationControlled
--disable-features=IsolateOrigins,site-per-process
--enable-features=NetworkService,NetworkServiceInProcess
--disable-web-security
--allow-running-insecure-content
```

### 3. Context Configuration
- Realistic viewport sizes (1920x1080, 1366x768, etc.)
- Proper user agent string
- Locale and timezone settings
- HTTP headers (Accept-Language, Sec-Ch-Ua, etc.)

## Usage

### Basic Implementation
```python
from agent.stealth import apply_stealth, StealthConfig

# Create stealth config
config = StealthConfig(
    enable_all=True,  # Enable all evasions
    locale='en-US',
    fix_hairline=True,
    mask_network_info=True
)

# Apply to browser/context/page
await apply_stealth(browser, config)
```

### Custom Configuration
```python
config = StealthConfig(
    enable_all=False,
    evasions=['webdriver', 'chrome_runtime', 'plugins'],  # Select specific evasions
    vendor='Intel Inc.',  # Custom WebGL vendor
    renderer='Intel Iris Graphics',  # Custom WebGL renderer
    user_agent='Custom UA String'
)
```

## Testing

Run the stealth test suite:
```bash
python tests/test_stealth.py
```

This will:
1. Test against bot.sannysoft.com
2. Check all stealth properties
3. Test Google search for CAPTCHA
4. Generate screenshots of results

## Evasions List

| Evasion | Description | Impact |
|---------|-------------|---------|
| webdriver | Removes automation indicators | Critical |
| chrome_runtime | Emulates Chrome-specific objects | High |
| webgl_vendor | Spoofs graphics hardware | Medium |
| plugins | Adds expected browser plugins | Medium |
| languages | Sets language preferences | Low |
| permissions | Fixes permission queries | Medium |
| media_codecs | Reports codec support | Low |
| iframe_contentwindow | Fixes iframe properties | Medium |
| hairline_fix | Prevents subpixel detection | Low |
| user_agent | Custom user agent string | High |
| network_info | Masks connection details | Medium |
| battery_api | Provides battery status | Low |
| device_memory | Sets device memory | Low |
| hardware_concurrency | Sets CPU cores | Low |

## Best Practices

1. **Always Enable Core Evasions**: webdriver, chrome_runtime, and user_agent are essential
2. **Randomize Properties**: Use different viewports, user agents, and hardware specs
3. **Behavioral Patterns**: Add delays between actions, randomize mouse movements
4. **Session Management**: Maintain cookies and local storage between requests
5. **Proxy Rotation**: Use residential proxies for better anonymity

## Limitations

- Some advanced anti-bot services may still detect automation
- Performance overhead from JavaScript patches
- Regular updates needed as detection methods evolve
- WebRTC and Canvas fingerprinting not fully addressed

## Future Improvements

1. WebRTC leak prevention
2. Canvas fingerprint randomization
3. Audio context fingerprinting
4. Font enumeration protection
5. TLS/JA3 fingerprint randomization