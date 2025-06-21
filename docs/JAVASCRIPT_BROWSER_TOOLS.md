# JavaScript-Based Browser Tools Documentation

## Overview

This implementation brings Suna AI's approach to browser automation - using direct JavaScript execution within browser contexts instead of traditional selector-based automation. This provides enhanced flexibility, better performance, and more reliable automation for modern web applications.

## Key Features

### 1. Direct JavaScript Execution
- Execute arbitrary JavaScript code directly in the browser context
- Full access to DOM APIs, browser APIs, and page state
- Support for async/await patterns
- Better handling of dynamic content and SPAs

### 2. Security Features
- **JavaScriptSanitizer**: Prevents injection attacks by escaping user inputs
- Selector validation to prevent script injection
- Secure string escaping for JavaScript execution

### 3. JavaScript Templates Library
- Pre-built templates for common operations
- Optimized JavaScript patterns for performance
- Event dispatching for proper form handling
- Custom wait conditions and complex interactions

### 4. Enhanced Tools

#### ExecuteJavaScriptTool
Execute custom JavaScript directly in the browser:
```python
result = await tool._arun(
    js_code="document.querySelectorAll('.item').length"
)
```

#### JavaScriptTextInputTool
Type text with proper event dispatching:
```python
await tool._arun(
    selector="#username",
    text="user@example.com",
    delay=50,  # Optional typing delay
    clear_first=True
)
```

#### JavaScriptClickTool
Advanced clicking with modifiers and click types:
```python
await tool._arun(
    selector="#submit-button",
    click_type="double",  # left, right, middle, double
    modifiers=["Control", "Shift"]
)
```

#### WaitForConditionTool
Wait for custom JavaScript conditions:
```python
await tool._arun(
    condition="document.querySelector('.spinner').style.display === 'none'",
    timeout=10000
)
```

#### ExtractDataTool
Efficient bulk data extraction:
```python
data = await tool._arun(
    selectors={
        "title": "h1",
        "prices": ".price",
        "descriptions": ".description"
    }
)
```

#### JavaScriptStorageTool
Direct storage manipulation:
```python
# Get value
await tool._arun(action="get", key="auth_token")

# Set value
await tool._arun(action="set", key="preference", value="dark_mode")

# Clear storage
await tool._arun(action="clear", storage_type="sessionStorage")
```

## Integration with Existing Tools

### HybridBrowserToolsManager
Intelligently combines traditional and JavaScript-based tools:

```python
from agent.browser_tools_integration import HybridBrowserToolsManager

# Create hybrid manager
manager = HybridBrowserToolsManager(
    browser=browser,
    prefer_javascript=True  # Prefer JS tools when suitable
)

# Get recommended tools for specific use case
text_tools = manager.get_recommended_tools('text_input')
click_tools = manager.get_recommended_tools('click')
```

### SmartBrowserAutomation
High-level interface with automatic tool selection:

```python
from agent.browser_tools_integration import SmartBrowserAutomation

# Initialize smart automation
automation = SmartBrowserAutomation(browser)
await automation.set_page(page)

# Smart methods automatically choose optimal approach
await automation.smart_input("#email", "user@example.com")
await automation.smart_click("#submit")
await automation.smart_wait("document.readyState === 'complete'")

# Bulk data extraction
data = await automation.smart_extract({
    "title": "h1",
    "content": "#main-content",
    "links": "a.external-link"
})
```

## Usage Examples

### Example 1: Dynamic Form Handling
```python
# Traditional approach might fail on React forms
# JavaScript approach handles virtual DOM correctly

tool = ExecuteJavaScriptTool()
await tool._arun(js_code="""
    const input = document.querySelector('#dynamic-input');
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
    ).set;
    nativeInputValueSetter.call(input, 'New Value');
    
    // Trigger React's change detection
    input.dispatchEvent(new Event('input', { bubbles: true }));
""")
```

### Example 2: Complex Wait Conditions
```python
# Wait for multiple conditions
wait_tool = WaitForConditionTool()
await wait_tool._arun(
    condition="""
        document.querySelector('.loader').style.display === 'none' &&
        document.querySelectorAll('.product').length > 0 &&
        !document.body.classList.contains('loading')
    """,
    timeout=15000
)
```

### Example 3: Secure Data Extraction
```python
# Extract data with automatic sanitization
extract_tool = ExtractDataTool()
results = await extract_tool._arun(
    selectors={
        "product_names": ".product h3",
        "prices": ".product .price",
        "availability": ".product .stock-status",
        "ratings": ".product .rating span"
    }
)
# Returns structured JSON with all extracted data
```

### Example 4: Performance-Critical Operations
```python
# Batch operations in single JavaScript execution
exec_tool = ExecuteJavaScriptTool()
await exec_tool._arun(js_code="""
    // Perform multiple operations in one execution
    const results = [];
    
    // Click all "add to cart" buttons
    document.querySelectorAll('.add-to-cart').forEach(btn => {
        btn.click();
        results.push(btn.dataset.productId);
    });
    
    // Update cart counter
    const counter = document.querySelector('.cart-count');
    counter.textContent = results.length;
    
    return results;
""")
```

## Performance Benefits

1. **Reduced Round-trips**: Execute complex operations in a single evaluate() call
2. **Direct DOM Access**: No need for selector resolution on each operation
3. **Batch Operations**: Process multiple elements efficiently
4. **Native Speed**: JavaScript executes at native browser speed

## Security Considerations

1. **Input Sanitization**: All user inputs are escaped before JavaScript execution
2. **Selector Validation**: Prevents script injection through selectors
3. **Error Isolation**: JavaScript errors are caught and reported safely
4. **No Direct eval()**: Uses Playwright's secure evaluate() method

## Best Practices

1. **Use JavaScript for**:
   - Dynamic web applications (React, Vue, Angular)
   - Complex DOM manipulations
   - Bulk operations
   - Custom wait conditions
   - Performance-critical automation

2. **Use Traditional Tools for**:
   - Simple static pages
   - Standard form submissions
   - File uploads
   - Screenshots

3. **Error Handling**:
   ```python
   try:
       result = await js_tool._arun(js_code="complex.operation()")
       if "error" in result.lower():
           # Fall back to traditional approach
           result = await traditional_tool._arun(...)
   except JavaScriptExecutionError:
       # Handle execution errors
       logger.error("JavaScript execution failed")
   ```

4. **Testing**: Always test JavaScript tools on your target application as behavior may vary across different frameworks and implementations.

## Migration Guide

To migrate existing automation to JavaScript-based tools:

1. **Identify Performance Bottlenecks**: Look for slow selector-based operations
2. **Start with Hybrid Approach**: Use `HybridBrowserToolsManager` to gradually adopt JavaScript tools
3. **Test Thoroughly**: Ensure JavaScript execution works with your target applications
4. **Monitor Performance**: Compare execution times and reliability

## Troubleshooting

### Common Issues

1. **JavaScript Errors**: Check browser console for JavaScript errors
2. **Timing Issues**: Use wait conditions instead of fixed delays
3. **Framework Conflicts**: Some frameworks may require specific event handling

### Debug Mode

Enable detailed logging:
```python
import logging
logging.getLogger('browser_tools_js').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Script Injection**: Pre-load common utilities using `addInitScript()`
2. **Performance Metrics**: Built-in timing and performance tracking
3. **Framework-Specific Templates**: Optimized templates for React, Vue, Angular
4. **Visual Debugging**: Screenshot integration for debugging failures

## Conclusion

JavaScript-based browser tools provide a powerful alternative to traditional automation approaches. By executing code directly in the browser context, you gain flexibility, performance, and reliability - especially for modern web applications. The hybrid approach ensures you can leverage the best tool for each specific use case.