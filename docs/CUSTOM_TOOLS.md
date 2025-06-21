# Custom Browser Automation Tools

This document describes the custom browser automation tools that extend the default Playwright toolkit in the Browser Agent.

## Overview

The Browser Agent includes 12 custom tools that provide advanced browser automation capabilities beyond the standard Playwright toolkit:

1. **Text Input Tool** - Type text into form fields with advanced options
2. **Form Submit Tool** - Submit forms via buttons or keyboard
3. **Screenshot Tool** - Capture full page, viewport, or element screenshots
4. **Wait For Element Tool** - Wait for elements to appear or change state
5. **File Upload Tool** - Upload files to file input elements
6. **Key Press Tool** - Press keyboard keys and combinations
7. **Scroll Tool** - Scroll pages by amount or to specific elements
8. **Drag and Drop Tool** - Drag elements and drop them on targets
9. **Hover Tool** - Hover over elements with optional duration
10. **Advanced Click Tool** - Right-click, double-click, and click with modifiers
11. **Iframe Tool** - Navigate into and out of iframe contexts
12. **Storage Tool** - Manipulate localStorage and sessionStorage

## Tool Details

### 1. Text Input Tool (`input_text`)

Types text into input fields, textareas, or contenteditable elements.

**Parameters:**
- `selector` (str): CSS selector for the input element
- `text` (str): Text to type
- `delay` (int, optional): Delay between keystrokes in ms (default: 0)
- `clear_first` (bool, optional): Clear existing text first (default: True)

**Example Usage:**
```
"Type 'Hello World' into the input field with selector '#search-box'"
```

### 2. Form Submit Tool (`submit_form`)

Submits forms by clicking submit buttons or pressing Enter.

**Parameters:**
- `form_selector` (str, optional): CSS selector for the form
- `submit_selector` (str, optional): CSS selector for submit button
- `press_enter` (bool, optional): Submit by pressing Enter (default: False)

**Example Usage:**
```
"Submit the form with selector '#login-form'"
"Press Enter to submit the current form"
```

### 3. Screenshot Tool (`take_screenshot`)

Captures screenshots of the page, full page, or specific elements.

**Parameters:**
- `full_page` (bool, optional): Capture full page (default: False)
- `selector` (str, optional): CSS selector for specific element
- `format` (str, optional): Image format - 'png' or 'jpeg' (default: 'png')
- `quality` (int, optional): JPEG quality 0-100 (default: None)

**Example Usage:**
```
"Take a full page screenshot"
"Take a screenshot of the element with selector '.main-content'"
```

### 4. Wait For Element Tool (`wait_for_element`)

Waits for elements to appear, become visible, or change state.

**Parameters:**
- `selector` (str): CSS selector to wait for
- `state` (str, optional): State to wait for - 'visible', 'attached', 'detached', 'hidden' (default: 'visible')
- `timeout` (int, optional): Timeout in milliseconds (default: 30000)

**Example Usage:**
```
"Wait for the element with selector '.loading' to be hidden"
"Wait for the button with selector '#submit' to be visible"
```

### 5. File Upload Tool (`upload_file`)

Uploads files to file input elements.

**Parameters:**
- `selector` (str): CSS selector for file input element
- `file_path` (str): Path to file to upload

**Example Usage:**
```
"Upload the file '/app/data/test.pdf' to the file input with selector '#file-upload'"
```

### 6. Key Press Tool (`press_key`)

Presses keyboard keys or key combinations.

**Parameters:**
- `key` (str): Key to press (e.g., 'Enter', 'Escape', 'Control+A')

**Example Usage:**
```
"Press the Escape key"
"Press Control+S to save"
```

### 7. Scroll Tool (`scroll_page`)

Scrolls the page in various ways.

**Parameters:**
- `direction` (str, optional): Scroll direction - 'up', 'down', 'left', 'right' (default: 'down')
- `amount` (int, optional): Amount to scroll in pixels (default: 300)
- `to_element` (str, optional): CSS selector to scroll to

**Example Usage:**
```
"Scroll down by 500 pixels"
"Scroll to the element with selector '#footer'"
```

### 8. Drag and Drop Tool (`drag_drop`)

Performs drag and drop operations between elements.

**Parameters:**
- `source_selector` (str): CSS selector for element to drag
- `target_selector` (str): CSS selector for drop target

**Example Usage:**
```
"Drag the element with selector '.draggable-item' to the element with selector '.drop-zone'"
```

### 9. Hover Tool (`hover_element`)

Hovers over elements, optionally for a specified duration.

**Parameters:**
- `selector` (str): CSS selector for element to hover over
- `duration` (int, optional): Duration to hover in milliseconds (default: 0)

**Example Usage:**
```
"Hover over the menu item with selector '.dropdown-trigger' for 2000 milliseconds"
```

### 10. Advanced Click Tool (`click_advanced`)

Performs advanced click operations including right-click and double-click.

**Parameters:**
- `selector` (str): CSS selector for element to click
- `click_type` (str, optional): Click type - 'left', 'right', 'middle', 'double' (default: 'left')
- `modifiers` (list, optional): Modifier keys - ['Control'], ['Shift'], ['Alt'], ['Meta']

**Example Usage:**
```
"Right-click on the element with selector '.context-menu-target'"
"Double-click on the file with selector '.file-icon'"
"Control-click on the link with selector 'a.multi-select'"
```

### 11. Iframe Tool (`navigate_iframe`)

Navigates into and out of iframe contexts.

**Parameters:**
- `iframe_selector` (str, optional): CSS selector for iframe to enter
- `exit_iframe` (bool, optional): Exit current iframe to parent context (default: False)

**Example Usage:**
```
"Enter the iframe with selector '#embedded-content'"
"Exit the current iframe back to the main page"
```

### 12. Storage Tool (`manage_storage`)

Manages browser storage (localStorage and sessionStorage).

**Parameters:**
- `action` (str): Action to perform - 'get', 'set', 'remove', 'clear'
- `storage_type` (str, optional): Storage type - 'localStorage' or 'sessionStorage' (default: 'localStorage')
- `key` (str, optional): Storage key (required for get, set, remove)
- `value` (str, optional): Storage value (required for set)

**Example Usage:**
```
"Set localStorage key 'user_preference' to value 'dark_mode'"
"Get the value of sessionStorage key 'session_id'"
"Clear all localStorage"
```

## Integration with LangChain

All custom tools are automatically integrated with the LangChain agent and can be invoked through natural language commands. The agent will intelligently select and use the appropriate tools based on the task description.

## Error Handling

Each tool includes comprehensive error handling and will return descriptive error messages if:
- Required elements are not found
- Timeouts occur
- Invalid parameters are provided
- Browser context is not available

## Best Practices

1. **Use specific CSS selectors** - More specific selectors reduce ambiguity
2. **Wait for elements** - Use the wait tool before interacting with dynamic content
3. **Handle navigation** - Allow time for page loads between actions
4. **Check results** - Tools return success/failure messages that can guide next actions
5. **Combine tools** - Complex workflows can chain multiple tools together

## Examples

### Example 1: Form Automation
```
"Go to the login page, type 'user@example.com' into the email field with selector '#email', 
type 'password123' into the password field with selector '#password', 
then click the submit button with selector '#login-button'"
```

### Example 2: Data Extraction with Screenshots
```
"Navigate to the dashboard, wait for the chart with selector '.sales-chart' to be visible,
scroll to that element, then take a screenshot of it"
```

### Example 3: Complex Interaction
```
"Go to the file manager, right-click on the file with selector '.file[data-name='report.pdf']',
wait for the context menu with selector '.context-menu' to appear,
then click on the 'Download' option"
```