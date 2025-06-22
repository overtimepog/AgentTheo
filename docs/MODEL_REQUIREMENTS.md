# Model Requirements for Browser Automation

## Function Calling Support

The BrowserBase agent requires an LLM model that supports **function calling** (also known as tool use) to properly execute browser automation tasks.

## Recommended Models

### OpenAI Models (via OpenRouter)
- `openai/gpt-4o` - Most capable, higher cost
- `openai/gpt-4o-mini` - Good balance of capability and cost
- `openai/gpt-4-turbo` - Previous generation, still very capable
- `openai/gpt-3.5-turbo` - Fastest, most economical

### Anthropic Models (via OpenRouter)
- `anthropic/claude-3-opus` - Most capable Claude model
- `anthropic/claude-3-sonnet` - Balanced performance
- `anthropic/claude-3-haiku` - Fast and economical

### Specialized Function-Calling Models
- `arcee-ai/arcee-caller` - Optimized specifically for tool orchestration
- `zhipuai/glm-4` - Supports function calling and agents

## Models to Avoid

The following models do NOT support function calling and will only describe actions instead of executing them:
- `deepseek/deepseek-chat`
- `x-ai/grok-3-mini`
- Most open-source models without explicit function-calling support

## Configuration

Update your `config/.env` file:

```bash
# Replace with a function-calling capable model
LLM_MODEL=openai/gpt-4o-mini
```

## Testing

Run the test script to verify your model works properly:

```bash
python test_browser_agent.py
```

A successful test will show the agent navigating to a website and extracting information.