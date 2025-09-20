# Multi-Model Support Usage Examples

This GitHub Action now supports multiple AI providers for security analysis. Here are examples of how to use different models:

## Using Anthropic Claude (Default)

```yaml
name: Security Review with Claude

on:
  pull_request:

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
          fetch-depth: 2
      
      - uses: your-org/claude-code-security-review@main
        with:
          ai-provider: 'anthropic'
          ai-model: 'claude-opus-4-1-20250805'  # Optional, defaults to latest
          claude-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          comment-pr: true
```

## Using OpenAI GPT

```yaml
name: Security Review with OpenAI

on:
  pull_request:

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
          fetch-depth: 2
      
      - uses: your-org/claude-code-security-review@main
        with:
          ai-provider: 'openai'
          ai-model: 'gpt-4o'  # Optional, defaults to gpt-4o
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          comment-pr: true
```

## Using Different Models

### Claude Models
- `claude-opus-4-1-20250805` (default)
- `claude-sonnet-4-20250514`
- `claude-haiku-3-5-20241022`

### OpenAI Models
- `gpt-4o` (default)
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

## Environment Variables

You can also configure the provider and model using environment variables:

```yaml
env:
  AI_PROVIDER: 'openai'
  AI_MODEL: 'gpt-4o'
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Backward Compatibility

The action remains backward compatible with existing configurations:

```yaml
# This still works (uses Claude by default)
- uses: your-org/claude-code-security-review@main
  with:
    claude-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    claude-model: 'claude-opus-4-1-20250805'
    comment-pr: true
```

## Adding New Providers

To add support for a new AI provider (e.g., Google Gemini):

1. Create a new client class in `claudecode/ai_models/` that implements `AIModelClient`
2. Register it in the `ModelFactory` in `model_factory.py`
3. Add the provider to the `ModelProvider` enum in `base_client.py`
4. Update the action.yml inputs if needed

Example:
```python
# claudecode/ai_models/gemini_client.py
class GeminiClient(AIModelClient):
    def validate_api_access(self) -> Tuple[bool, str]:
        # Implementation here
        pass
    
    def call_with_retry(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> Tuple[bool, str, str]:
        # Implementation here
        pass
    
    # ... other required methods
```
