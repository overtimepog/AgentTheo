# AgentTheo Enhancement Implementation Guide

## Quick Start

This guide provides step-by-step instructions for implementing the AgentTheo enhancements outlined in the Browser Enhancement Plan.

## Prerequisites

1. **Development Environment**
   - Python 3.11+
   - Node.js 20+
   - Docker Desktop
   - Redis (for multi-agent communication)

2. **API Keys**
   - OpenRouter API key (existing)
   - GPT-4V or Claude Vision API key (new requirement)

## Phase 1: Multi-Agent Architecture

### Step 1: Install New Dependencies

```bash
# Create new requirements file for enhancements
cat >> requirements-enhanced.txt << EOF
# Multi-Agent & State Management
redis==4.5.5
aioredis==2.0.1
pydantic==2.5.0

# Vision & ML
openai==1.10.0
anthropic==0.8.0
opencv-python==4.8.1
pytesseract==0.3.10
Pillow==10.1.0

# Performance & Monitoring
prometheus-client==0.19.0
memory-profiler==0.61.0
psutil==5.9.6
EOF

# Install dependencies
pip install -r requirements-enhanced.txt
```

### Step 2: Create Agent Base Classes

Create `agent/multi_agent/base.py`:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel
from langgraph.types import Command
import asyncio
import redis.asyncio as aioredis

class AgentMessage(BaseModel):
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    correlation_id: str

class BaseAgent(ABC):
    def __init__(self, name: str, redis_url: str = "redis://localhost"):
        self.name = name
        self.redis = None
        self.redis_url = redis_url
        
    async def initialize(self):
        self.redis = await aioredis.from_url(self.redis_url)
        await self.setup()
    
    @abstractmethod
    async def setup(self):
        """Initialize agent-specific resources"""
        pass
    
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Optional[Command]:
        """Process incoming messages and return commands"""
        pass
    
    async def send_message(self, recipient: str, message_type: str, payload: Dict[str, Any]):
        """Send message to another agent"""
        msg = AgentMessage(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            correlation_id=str(asyncio.current_task())
        )
        await self.redis.publish(f"agent:{recipient}", msg.json())
```

### Step 3: Implement Specialized Agents

Create `agent/multi_agent/navigator.py`:

```python
from .base import BaseAgent, AgentMessage
from typing import Optional
from langgraph.types import Command

class NavigatorAgent(BaseAgent):
    async def setup(self):
        self.logger = get_logger(f"agent.{self.name}")
        
    async def process_message(self, message: AgentMessage) -> Optional[Command]:
        if message.message_type == "navigate":
            url = message.payload.get("url")
            # Implementation for navigation
            return Command(
                update={"status": "navigated", "url": url},
                goto="interaction_agent"
            )
```

### Step 4: Set Up Redis Communication

Update `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    
  agenttheo:
    # ... existing configuration ...
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379

volumes:
  redis_data:
```

## Phase 2: Vision Integration

### Step 1: Create Vision Agent

Create `agent/multi_agent/vision.py`:

```python
import base64
from typing import Dict, Any
from openai import OpenAI
from .base import BaseAgent

class VisionAgent(BaseAgent):
    def __init__(self, name: str, redis_url: str, api_key: str):
        super().__init__(name, redis_url)
        self.client = OpenAI(api_key=api_key)
    
    async def analyze_screenshot(self, image_bytes: bytes, query: str) -> Dict[str, Any]:
        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode()
        
        response = await self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]
            }]
        )
        
        return {"analysis": response.choices[0].message.content}
```

### Step 2: Implement Screenshot Pipeline

Create `agent/vision/screenshot_processor.py`:

```python
from PIL import Image
import numpy as np
from io import BytesIO

class ScreenshotProcessor:
    @staticmethod
    def preprocess(image_bytes: bytes, max_size: tuple = (1920, 1080)) -> bytes:
        """Preprocess screenshot for vision model input"""
        image = Image.open(BytesIO(image_bytes))
        
        # Resize if needed
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save to bytes
        output = BytesIO()
        image.save(output, format='PNG', optimize=True)
        return output.getvalue()
```

## Phase 3: Self-Healing Selectors

### Step 1: Implement Adaptive Selector

Create `agent/browser_tools_adaptive.py`:

```python
from typing import List, Optional, Dict
import json

class AdaptiveSelector:
    def __init__(self, storage_path: str = ".selector_cache.json"):
        self.storage_path = storage_path
        self.selector_history = self.load_history()
    
    def load_history(self) -> Dict[str, List[Dict]]:
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    async def find_element(self, page, strategies: List[Dict[str, str]]) -> Optional[Any]:
        """Try multiple strategies to find an element"""
        for strategy in strategies:
            try:
                if strategy['type'] == 'css':
                    element = await page.query_selector(strategy['selector'])
                elif strategy['type'] == 'xpath':
                    element = await page.xpath(strategy['selector'])
                elif strategy['type'] == 'text':
                    element = await page.get_by_text(strategy['selector'])
                elif strategy['type'] == 'role':
                    element = await page.get_by_role(strategy['role'], name=strategy.get('name'))
                
                if element:
                    self.record_success(strategies[0]['selector'], strategy)
                    return element
            except:
                continue
        
        # If all fail, try vision-based detection
        return await self.vision_fallback(page, strategies[0].get('description'))
    
    def record_success(self, original_selector: str, successful_strategy: Dict):
        """Record successful selector for future use"""
        if original_selector not in self.selector_history:
            self.selector_history[original_selector] = []
        
        self.selector_history[original_selector].append({
            'strategy': successful_strategy,
            'timestamp': datetime.now().isoformat(),
            'success_count': 1
        })
        
        self.save_history()
```

## Testing Strategy

### Unit Tests

Create `tests/test_multi_agent.py`:

```python
import pytest
from agent.multi_agent.base import BaseAgent, AgentMessage

@pytest.mark.asyncio
async def test_agent_communication():
    # Test agent initialization
    agent = TestAgent("test_agent")
    await agent.initialize()
    
    # Test message sending
    await agent.send_message("target", "test", {"data": "value"})
    
    # Verify message received
    # ... implementation ...
```

### Integration Tests

Create `tests/test_vision_integration.py`:

```python
@pytest.mark.asyncio
async def test_vision_fallback():
    # Create test page with dynamic content
    page = await browser.new_page()
    await page.goto("http://example.com")
    
    # Test vision-based element detection
    vision_agent = VisionAgent("vision", "redis://localhost")
    element = await vision_agent.detect_element(page, "Click the submit button")
    
    assert element is not None
```

## Monitoring and Debugging

### Add Prometheus Metrics

Create `agent/monitoring.py`:

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
task_counter = Counter('browser_tasks_total', 'Total browser tasks', ['status'])
task_duration = Histogram('browser_task_duration_seconds', 'Task duration')
active_browsers = Gauge('active_browsers', 'Number of active browser instances')

# Use in code
@task_duration.time()
async def execute_task(task):
    try:
        result = await process_task(task)
        task_counter.labels(status='success').inc()
        return result
    except Exception as e:
        task_counter.labels(status='failure').inc()
        raise
```

## Configuration

Update `.env` file:

```bash
# Existing configuration
OPENROUTER_API_KEY=your_key

# New configuration
REDIS_URL=redis://localhost:6379
VISION_MODEL=gpt-4-vision-preview
VISION_API_KEY=your_openai_key
ENABLE_MULTI_AGENT=true
MAX_CONCURRENT_BROWSERS=5
ENABLE_SELF_HEALING=true
```

## Migration Guide

### Backward Compatibility

Ensure existing code continues to work:

```python
# In main_langgraph.py
if os.getenv("ENABLE_MULTI_AGENT", "false").lower() == "true":
    from agent.multi_agent import create_multi_agent_system
    agent = await create_multi_agent_system()
else:
    # Use existing single agent
    agent = await create_browser_agent()
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   docker-compose up -d redis
   # Check logs: docker-compose logs redis
   ```

2. **Vision API Rate Limits**
   - Implement exponential backoff
   - Cache vision results for similar queries

3. **Memory Leaks**
   - Monitor with `memory_profiler`
   - Ensure proper browser cleanup

## Next Steps

1. Complete Phase 1 implementation
2. Run integration tests
3. Deploy to staging environment
4. Gather performance metrics
5. Iterate based on results

---

For questions or issues, refer to the [Enhancement Plan](BROWSER_ENHANCEMENT_PLAN.md) or create an issue in the repository.