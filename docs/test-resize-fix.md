# Resize Bug Fix Test Plan

## Issue
When dragging the resizer between panels, if the mouse moves over the VNC iframe, the resize operation stops working because the iframe captures the mouse events.

## Solution Implemented
1. Moved pointer event listeners from resizer element to document for better global tracking
2. Added iframe overlay creation during resize start
3. The overlay prevents iframes from capturing mouse events
4. Overlay is removed when resize ends

## Changes Made
1. Added `iframeOverlay` property to track overlay element
2. Modified `setupEventListeners()` to attach move/up events to document
3. Added `createIframeOverlay()` method to create transparent overlays
4. Added `removeIframeOverlay()` method to clean up overlays
5. Called overlay methods in `startResize()` and `endResize()`
6. Updated destroy method to clean up document listeners

## Testing Steps
1. Open http://localhost:8000 in browser
2. Click and hold the resizer between panels
3. Drag mouse over the VNC iframe area
4. Verify resize continues working
5. Release mouse to complete resize
6. Test multiple resize operations

## Expected Behavior
- Resize should continue smoothly even when mouse is over iframe
- Visual feedback (cursor, colors) should remain consistent
- Panel sizes should update in real-time
- No jittering or stuck states