# DOM Analysis Tools for Browser Automation

## Overview

The browser automation framework now includes advanced DOM analysis and event monitoring tools that help the AI understand web pages before attempting interactions. This significantly improves reliability and success rates, especially on complex or dynamic websites.

## New Tools

### 1. DOM Mapper Tool (`analyze_dom`)

The DOM Mapper provides comprehensive analysis of page structure and elements.

#### Features:
- **Intelligent Selector Generation**: Generates multiple selector strategies for each element
- **Visibility Detection**: Determines if elements are actually visible to users
- **Interactability Analysis**: Identifies which elements can be interacted with
- **Hierarchical Structure**: Analyzes DOM tree with configurable depth
- **Page Metrics**: Provides viewport dimensions, document size, and element counts

#### Usage:
```python
# Analyze entire page
result = await dom_mapper._arun()

# Analyze specific elements
result = await dom_mapper._arun(selector="form", max_depth=2)

# Include invisible elements
result = await dom_mapper._arun(include_invisible=True)
```

#### Output Structure:
```json
{
  "pageInfo": {
    "title": "Page Title",
    "url": "https://example.com",
    "viewport": { "width": 1920, "height": 1080 },
    "documentSize": { "width": 1920, "height": 2000 }
  },
  "summary": {
    "totalInteractable": 45,
    "forms": 2,
    "links": 20,
    "buttons": 5
  },
  "interactableElements": [
    {
      "tagName": "input",
      "visible": true,
      "interactable": true,
      "selectors": [
        "#search-input",
        ".search-box",
        "[name='q']",
        "input[type='text']"
      ],
      "attributes": {
        "id": "search-input",
        "name": "q",
        "type": "text"
      },
      "position": {
        "top": 100,
        "left": 200,
        "width": 300,
        "height": 40
      }
    }
  ]
}
```

### 2. DOM Event Monitor Tool (`monitor_dom_events`)

Monitors and captures DOM events to understand page behavior and timing.

#### Features:
- **Event Capture**: Records specified event types with full details
- **Mutation Observation**: Tracks DOM changes and updates
- **Timing Analysis**: Helps understand when elements become available
- **Event Flow**: Captures bubbling and event propagation

#### Usage:
```python
# Monitor all events for 3 seconds
result = await event_monitor._arun(duration_ms=3000)

# Monitor specific events
result = await event_monitor._arun(
    duration_ms=5000,
    event_types=['click', 'input', 'submit']
)

# Monitor events on specific element
result = await event_monitor._arun(
    selector="#login-form",
    duration_ms=2000
)
```

#### Output Structure:
```json
{
  "duration": 3000,
  "eventCount": 15,
  "mutationCount": 8,
  "events": [
    {
      "type": "focus",
      "timestamp": 1234567890,
      "target": {
        "tagName": "input",
        "id": "email",
        "selector": "#email"
      }
    }
  ],
  "summary": {
    "byType": {
      "focus": 3,
      "input": 5,
      "click": 2
    },
    "topTargets": ["#email", "#password", "button"]
  }
}
```

## Selector Generation Strategy

The DOM Mapper generates intelligent selectors in order of preference:

1. **ID Selectors**: `#unique-id` (most specific)
2. **Class Selectors**: `.specific-class`
3. **Data Attributes**: `[data-testid="element"]`
4. **ARIA Attributes**: `[aria-label="Search"]`
5. **Text Content**: `text="Submit"` (for short, unique text)
6. **Attribute Combinations**: `input[type="email"][name="user_email"]`
7. **Role Selectors**: `[role="button"]`

## Best Practices

### 1. Always Analyze Before Interacting
```python
# Good - Analyze first
dom_analysis = await analyze_dom()
search_input = find_element_in_analysis(dom_analysis, "search input")
await input_text(search_input['selectors'][0], "query")

# Bad - Using generic selector
await input_text("input", "query")  # May target wrong input
```

### 2. Use Multiple Selectors as Fallbacks
```python
# Try selectors in order of specificity
for selector in element['selectors']:
    try:
        await click_element(selector)
        break
    except:
        continue
```

### 3. Monitor Dynamic Pages
```python
# For SPAs or dynamic content
await navigate_browser("https://app.example.com")
await monitor_dom_events(duration_ms=2000)  # Understand page behavior
await analyze_dom()  # Then analyze structure
```

### 4. Re-analyze After Failures
```python
try:
    await click_element(selector)
except:
    # Page may have changed
    new_analysis = await analyze_dom()
    # Find element again with fresh selectors
```

## Integration with Agent

The browser agent has been updated to automatically use these tools:

1. **Updated System Prompt**: Agent now knows to analyze DOM before interactions
2. **Workflow Enhancement**: Navigate → Analyze → Interact → Verify
3. **Error Recovery**: Re-analyzes DOM when interactions fail

## Performance Considerations

- **DOM Analysis**: Full page analysis typically takes 100-500ms
- **Event Monitoring**: Minimal overhead, captures events in real-time
- **Memory Usage**: Results are limited to prevent excessive memory use
  - Interactable elements: Limited to 50 in full analysis
  - Event capture: Limited to prevent memory overflow
  - Mutation tracking: Limited to 50 mutations

## Common Use Cases

### 1. Form Filling
```python
# Analyze form structure
analysis = await analyze_dom(selector="form")
# Find specific inputs by attributes
email_input = find_by_attribute(analysis, "type", "email")
password_input = find_by_attribute(analysis, "type", "password")
```

### 2. Navigation Menus
```python
# Find all navigation links
analysis = await analyze_dom(selector="nav")
links = [el for el in analysis['elements'] if el['tagName'] == 'a']
```

### 3. Dynamic Content
```python
# Wait and monitor for content to load
await monitor_dom_events(duration_ms=3000)
# Then analyze the loaded content
analysis = await analyze_dom()
```

## Troubleshooting

### Element Not Found
- Check visibility with `include_invisible=True`
- Increase `max_depth` for nested elements
- Monitor events to ensure element is loaded

### Selector Not Working
- Use DOM analysis to get fresh selectors
- Check if element is in iframe (requires special handling)
- Verify element is actually interactable

### Dynamic Page Issues
- Use event monitoring to understand timing
- Add appropriate waits based on event data
- Re-analyze DOM after dynamic updates