# JavaScript-Based Browser Tools

## Overview

The browser tools in this project use direct JavaScript execution via `page.evaluate()` for better performance and reliability with modern web applications. This approach is inspired by successful open-source browser automation projects like Skyvern and Browser-Use.

## Key Features

### Direct JavaScript Execution
- All browser interactions use `page.evaluate()` instead of high-level Playwright APIs
- Full access to DOM APIs and browser context
- Better compatibility with React, Vue, Angular, and other modern frameworks
- More reliable handling of dynamic content

### Security
- `escape_js_string()` function prevents JavaScript injection attacks
- All user inputs are properly escaped before execution
- Safe parameter passing to JavaScript code

### Tools Available

#### 1. ClickTool (`click_element`)
Clicks elements using JavaScript with proper event simulation:
- Waits for element visibility
- Scrolls element into view
- Supports left, right, middle, and double clicks
- Dispatches proper mouse events for framework compatibility
- Optional navigation waiting

#### 2. TextInputTool (`input_text`)
Types text using JavaScript for framework compatibility:
- Uses native value setters for React/Vue/Angular
- Proper event dispatching (input, change, keydown, keyup)
- Optional typing delay for realistic interaction
- Clear existing text option

#### 3. WaitForElementTool (`wait_for_element`)
Waits for elements with custom conditions:
- States: visible, attached, hidden, detached
- Custom timeout configuration
- Proper visibility checking including computed styles

#### 4. ScrollTool (`scroll_page`)
Scrolls using JavaScript:
- Directional scrolling (up, down, left, right)
- Scroll to specific element
- Smooth scrolling behavior
- Custom scroll amounts

#### 5. ExtractDataTool (`extract_data`)
Efficiently extracts multiple data points:
- Batch extraction with single JavaScript execution
- Returns text, value, href, and src attributes
- Handles single and multiple elements
- Error handling per selector

#### 6. ExecuteJavaScriptTool (`execute_javascript`)
Executes custom JavaScript for advanced operations:
- Direct access to browser context
- Support for passing arguments
- Returns execution results or errors

#### 7. ScreenshotTool (`take_screenshot`)
Captures screenshots (uses Playwright API for efficiency):
- Full page or viewport screenshots
- Element-specific screenshots
- Timestamped filenames

## Usage Examples

### Basic Click
```python
click_tool = ClickTool()
await click_tool._arun(selector="button#submit", click_type="left")
```

### Text Input with React Compatibility
```python
input_tool = TextInputTool()
await input_tool._arun(
    selector="input#username",
    text="user@example.com",
    clear_first=True
)
```

### Wait for Dynamic Content
```python
wait_tool = WaitForElementTool()
await wait_tool._arun(
    selector=".loading-complete",
    state="visible",
    timeout=10000
)
```

### Extract Multiple Data Points
```python
extract_tool = ExtractDataTool()
data = await extract_tool._arun(
    selectors={
        "title": "h1",
        "price": ".product-price",
        "description": ".product-description"
    }
)
```

### Custom JavaScript Execution
```python
js_tool = ExecuteJavaScriptTool()
result = await js_tool._arun(
    code="""
    const buttons = document.querySelectorAll('.add-to-cart');
    buttons.forEach(btn => btn.click());
    return buttons.length;
    """
)
```

## Implementation Details

### Event Dispatching for Frameworks
The tools properly handle modern JavaScript frameworks by:
1. Using native property setters instead of just setting `.value`
2. Dispatching all necessary events (input, change, keydown, keyup)
3. Triggering both synthetic and native events
4. Proper focus/blur handling

### Visibility Checking
Elements are considered visible when:
- Width and height > 0
- `display` is not `none`
- `visibility` is not `hidden`
- `opacity` is not `0`
- Element is in the viewport

### Error Handling
- All JavaScript errors are caught and returned as error messages
- Timeouts are configurable
- Clear error messages for debugging

## Performance Benefits

1. **Reduced Round-trips**: Complex operations execute in single `evaluate()` call
2. **Batch Operations**: Extract multiple data points in one execution
3. **Native Browser Speed**: JavaScript runs at full browser speed
4. **Better Framework Support**: Direct DOM manipulation works with any framework

## Security Considerations

1. **Input Sanitization**: All inputs are escaped using `escape_js_string()`
2. **No String Interpolation**: User data is passed as parameters, not concatenated
3. **Safe Execution**: Uses Playwright's secure `page.evaluate()` method
4. **Error Isolation**: JavaScript errors don't crash the automation

## Comparison with High-Level APIs

| Feature | High-Level API | JavaScript Execution |
|---------|----------------|---------------------|
| Framework Compatibility | Limited | Excellent |
| Performance | Multiple round-trips | Single execution |
| Dynamic Content | May fail | Handles well |
| Custom Logic | Not possible | Fully supported |
| Security | Built-in | Requires care |

## Best Practices

1. **Use JavaScript tools for**:
   - Modern web applications (React, Vue, Angular)
   - Dynamic content that loads after page load
   - Batch operations on multiple elements
   - Custom interaction patterns

2. **Error Handling**:
   - Always check return values for errors
   - Use appropriate timeouts for dynamic content
   - Provide fallback strategies

3. **Testing**:
   - Test with your specific web application
   - Verify event handling works with your framework
   - Check performance improvements

## Future Enhancements

- Add more specialized tools for common patterns
- Implement retry logic for transient failures
- Add performance metrics collection
- Create framework-specific optimizations