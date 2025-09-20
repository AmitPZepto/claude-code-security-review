"""Factory for creating AI model clients."""

import os
from typing import Optional
from .base_client import AIModelClient, ModelConfig, ModelProvider
from .claude_client import ClaudeClient
from .openai_client import OpenAIClient
from .azure_openai_client import AzureOpenAIClient
from ..logger import get_logger

logger = get_logger(__name__)


class ModelFactory:
    """Factory for creating AI model clients."""
    
    _providers = {
        ModelProvider.ANTHROPIC: ClaudeClient,
        ModelProvider.OPENAI: OpenAIClient,
        ModelProvider.AZURE_OPENAI: AzureOpenAIClient,
    }
    
    @classmethod
    def create_client(cls, 
                     provider: str, 
                     model_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> AIModelClient:
        """Create an AI model client.
        
        Args:
            provider: Provider name (anthropic, openai, etc.)
            model_name: Optional model name override
            api_key: Optional API key override
            
        Returns:
            Configured AI model client
            
        Raises:
            ValueError: If provider is not supported or configuration is invalid
        """
        try:
            provider_enum = ModelProvider(provider.lower())
        except ValueError:
            supported = [p.value for p in ModelProvider]
            raise ValueError(f"Unsupported provider '{provider}'. Supported providers: {supported}")
        
        # Create configuration
        if api_key:
            config = ModelConfig(
                provider=provider_enum,
                model_name=model_name or cls._get_default_model(provider_enum),
                api_key=api_key
            )
        else:
            config = ModelConfig.from_environment(provider, model_name)
        
        # Get client class
        client_class = cls._providers.get(provider_enum)
        if not client_class:
            raise ValueError(f"No client implementation for provider: {provider}")
        
        # Create and return client
        client = client_class(config)
        logger.info(f"Created {provider} client with model: {config.model_name}")
        return client
    
    @classmethod
    def _get_default_model(cls, provider: ModelProvider) -> str:
        """Get default model name for provider."""
        defaults = {
            ModelProvider.ANTHROPIC: 'claude-opus-4-1-20250805',
            ModelProvider.OPENAI: 'gpt-4o',
            ModelProvider.AZURE_OPENAI: 'gpt-4o',
        }
        return defaults[provider]
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported providers."""
        return [provider.value for provider in ModelProvider]
    
    @classmethod
    def register_provider(cls, provider: ModelProvider, client_class: type):
        """Register a new provider (for extensibility).
        
        Args:
            provider: Provider enum
            client_class: Client class implementing AIModelClient
        """
        cls._providers[provider] = client_class
        logger.info(f"Registered provider: {provider.value}")


def get_model_client(provider: Optional[str] = None, 
                    model_name: Optional[str] = None,
                    api_key: Optional[str] = None) -> AIModelClient:
    """Convenience function to get an AI model client.
    
    Args:
        provider: Provider name (defaults to environment variable or 'anthropic')
        model_name: Optional model name override
        api_key: Optional API key override
        
    Returns:
        Configured AI model client
    """
    # Get provider from environment or parameter
    if not provider:
        provider = os.environ.get('AI_PROVIDER', 'anthropic')
    
    return ModelFactory.create_client(provider, model_name, api_key)
