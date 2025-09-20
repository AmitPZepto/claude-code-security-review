# Azure OpenAI Usage Example

This example shows how to use the Claude Code Security Review action with Azure OpenAI.

## Prerequisites

1. **Azure OpenAI Resource**: You need an Azure OpenAI resource with a deployed model
2. **API Key**: Get your API key from the Azure portal
3. **Endpoint URL**: Your Azure OpenAI endpoint URL
4. **Model Name**: The name of your deployed model (e.g., `gpt-4o`, `gpt-4o-mini`)

## GitHub Secrets Setup

Add these secrets to your repository:

```bash
# Required secrets
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

## Workflow Configuration

```yaml
name: Security Review with Azure OpenAI

on:
  pull_request:
    paths:
      - '.github/workflows/**'
      - '**/*.yml'
      - '**/*.yaml'

jobs:
  security-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: AmitPZepto/claude-code-security-review@helloai
        with:
          comment-pr: true
          ai-provider: 'azure_openai'
          ai-model: 'gpt-4o'  # Your deployed model name
          azure-openai-api-key: ${{ secrets.AZURE_OPENAI_API_KEY }}
          azure-openai-endpoint: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          azure-openai-api-version: '2025-01-01-preview'  # Optional
          run-every-commit: true
          upload-results: true
          claudecode-timeout: 20
```

## Environment Variables

The action will set these environment variables:

- `AI_PROVIDER=azure_openai`
- `AI_MODEL=your-model-name`
- `AZURE_OPENAI_API_KEY=your-api-key`
- `AZURE_OPENAI_ENDPOINT=your-endpoint`
- `AZURE_OPENAI_API_VERSION=2025-01-01-preview`

## Supported Models

Azure OpenAI supports various models. Common ones include:

- `gpt-4o` - Most capable model
- `gpt-4o-mini` - Faster and more cost-effective
- `gpt-4-turbo` - Good balance of capability and speed
- `gpt-3.5-turbo` - Fastest and most cost-effective

## Configuration Options

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `ai-provider` | Set to `azure_openai` | Yes | `anthropic` |
| `ai-model` | Your deployed model name | Yes | `gpt-4o` |
| `azure-openai-api-key` | Your Azure OpenAI API key | Yes | - |
| `azure-openai-endpoint` | Your Azure OpenAI endpoint URL | Yes | - |
| `azure-openai-api-version` | API version to use | No | `2025-01-01-preview` |

## Example with Different Models

```yaml
# Using GPT-4o Mini for faster analysis
- uses: AmitPZepto/claude-code-security-review@helloai
  with:
    ai-provider: 'azure_openai'
    ai-model: 'gpt-4o-mini'
    azure-openai-api-key: ${{ secrets.AZURE_OPENAI_API_KEY }}
    azure-openai-endpoint: ${{ secrets.AZURE_OPENAI_ENDPOINT }}

# Using GPT-4 Turbo for comprehensive analysis
- uses: AmitPZepto/claude-code-security-review@helloai
  with:
    ai-provider: 'azure_openai'
    ai-model: 'gpt-4-turbo'
    azure-openai-api-key: ${{ secrets.AZURE_OPENAI_API_KEY }}
    azure-openai-endpoint: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
```

## Troubleshooting

### Common Issues

1. **Invalid Endpoint**: Make sure your endpoint URL includes the full path
   - ✅ Correct: `https://your-resource.openai.azure.com/`
   - ❌ Incorrect: `https://your-resource.openai.azure.com`

2. **Model Not Found**: Ensure your model is deployed in Azure OpenAI Studio
   - Check the model name matches exactly
   - Verify the model is deployed and active

3. **API Key Issues**: Verify your API key has the correct permissions
   - Must have access to the specific model
   - Check if the key is expired or revoked

### Debug Information

The action will log debug information including:
- Provider: `azure_openai`
- Model: Your deployed model name
- Endpoint: Your Azure OpenAI endpoint
- API Version: The version being used

## Cost Considerations

Azure OpenAI pricing varies by model and region. Consider:

- **GPT-4o Mini**: Most cost-effective for regular use
- **GPT-4o**: Best quality but higher cost
- **GPT-4 Turbo**: Good balance for complex analysis

Monitor your usage in the Azure portal to track costs.
