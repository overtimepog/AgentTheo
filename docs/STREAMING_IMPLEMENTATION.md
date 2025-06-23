# AgentTheo Streaming Implementation Guide

## Overview

AgentTheo implements real-time streaming capabilities to provide live feedback of agent actions through a web interface. This document details the streaming architecture, implementation status, and usage guidelines.

## Architecture

### Components

1. **StreamingBrowserAgent** (`agent/core/streaming_agent.py`)
   - Extends BrowserAgent with LangGraph streaming support
   - Implements `astream()` method for asynchronous event generation
   - Supports multiple streaming modes: messages, updates, custom

2. **FastAPI SSE Endpoint** (`webui/server.py`)
   - `/stream` endpoint for Server-Sent Events
   - Handles real-time streaming from agent to web clients
   - Supports connection management and error handling

3. **Streaming Callbacks** (`agent/core/streaming_callbacks.py`)
   - StreamingCallbackHandler: Captures LLM token generation
   - ProgressCallbackHandler: Tracks multi-step task progress

4. **Event Schema** (`webui/streaming_schema.py`)
   - Standardized event types: TokenEvent, ProgressEvent, ToolEvent, etc.
   - SSE formatting utilities

## Current Implementation Status

### ✅ Completed
- LangGraph astream API integration
- Streaming callback handlers
- SSE endpoint implementation
- Event schema definitions
- Basic WebSocket support

### ⏳ In Progress
- Full StreamingBrowserAgent-SSE integration
- Progress tracking for multi-step tasks
- Connection management improvements

### 📋 Planned
- WebSocket fallback mode
- Concurrent session management
- Stream interruption/resumption
- Performance optimizations

## Usage

### Starting the Service

```bash
# Start AgentTheo with streaming support
./run.sh start

# Access the web UI
# http://localhost:8000
```

### SSE Endpoint

The streaming endpoint is available at `/stream` with the following parameters:

```
GET /stream?command=<command>&messageId=<id>&stream_mode=<mode>
```

Parameters:
- `command`: The task/command to execute
- `messageId`: Unique identifier for tracking
- `stream_mode`: One of "messages", "updates", "custom"

### Event Types

1. **Token Events**
   ```json
   {
     "type": "token",
     "data": {
       "token": "Hello ",
       "metadata": {"count": 1}
     }
   }
   ```

2. **Progress Events**
   ```json
   {
     "type": "progress",
     "data": {
       "step": 1,
       "total": 5,
       "message": "Navigating to website..."
     }
   }
   ```

3. **Tool Events**
   ```json
   {
     "type": "tool_start",
     "data": {
       "tool_name": "navigate_to",
       "tool_input": "https://example.com"
     }
   }
   ```

## Integration Examples

### JavaScript Client

```javascript
const eventSource = new EventSource(`/stream?command=${encodeURIComponent(command)}&messageId=${messageId}`);

eventSource.addEventListener('token', (event) => {
  const data = JSON.parse(event.data);
  console.log('Token:', data.token);
});

eventSource.addEventListener('progress', (event) => {
  const data = JSON.parse(event.data);
  updateProgressBar(data.step, data.total);
});

eventSource.addEventListener('error', (event) => {
  console.error('Stream error:', event);
  eventSource.close();
});
```

### Python Client

```python
import aiohttp
import json

async def stream_command(command: str):
    async with aiohttp.ClientSession() as session:
        url = f"http://localhost:8000/stream?command={command}&messageId=test"
        async with session.get(url) as response:
            async for line in response.content:
                if line.startswith(b'data: '):
                    data = json.loads(line[6:].decode())
                    print(f"Event: {data}")
```

## Testing

Run the streaming tests:

```bash
# Inside the container
python -m pytest tests/test_streaming.py -v

# Specific test
python -m pytest tests/test_streaming.py::TestStreamingSupport::test_sse_endpoint_basic -v
```

## Troubleshooting

### Common Issues

1. **No streaming output**
   - Verify StreamingBrowserAgent is initialized with `initialize_with_streaming()`
   - Check that the LLM supports streaming (OpenRouter models should)
   - Ensure SSE connection isn't being buffered by proxy

2. **Connection drops**
   - Implement reconnection logic in client
   - Check for timeout settings in nginx/reverse proxy
   - Monitor server logs for errors

3. **High latency**
   - Optimize chunk size in streaming callbacks
   - Use `X-Accel-Buffering: no` header
   - Consider WebSocket mode for lower latency

### Debug Mode

Enable debug logging:

```python
# In config/.env
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.getLogger('streaming_agent').setLevel(logging.DEBUG)
```

## Performance Considerations

1. **Memory Usage**
   - Streaming uses generators to avoid memory accumulation
   - Each connection maintains minimal state
   - Automatic cleanup on disconnection

2. **Latency Targets**
   - First token: < 100ms from LLM response
   - Progress updates: Real-time as they occur
   - Tool events: Immediate notification

3. **Concurrency**
   - Current: Single agent instance, multiple streaming connections
   - Planned: Multiple agent instances with session management

## Future Enhancements

1. **Advanced Streaming Modes**
   - Binary streaming for screenshots
   - Compressed event streams
   - Batch event mode for high-frequency updates

2. **Client Libraries**
   - React hooks for streaming
   - Python async client
   - CLI streaming viewer

3. **Monitoring**
   - Stream health metrics
   - Connection analytics
   - Performance dashboards

## Contributing

When working on streaming features:

1. Follow the event schema strictly
2. Add tests for new event types
3. Document streaming behavior
4. Consider backward compatibility
5. Test with various network conditions

## References

- [LangGraph Streaming Docs](https://langchain-ai.github.io/langgraph/)
- [FastAPI SSE Guide](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Server-Sent Events Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)