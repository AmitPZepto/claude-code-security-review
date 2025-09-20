"""Base AI model client interface and configuration."""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum


class ModelProvider(Enum):
    """Supported AI model providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    # Future providers can be added here
    # GOOGLE = "google"
    # COHERE = "cohere"


@dataclass
class ModelConfig:
    """Configuration for AI model clients."""
    provider: ModelProvider
    model_name: str
    api_key: str
    timeout_seconds: int = 180
    max_retries: int = 3
    max_tokens: int = 16384
    
    @classmethod
    def from_environment(cls, provider: str, model_name: Optional[str] = None) -> 'ModelConfig':
        """Create ModelConfig from environment variables.
        
        Args:
            provider: Provider name (anthropic, openai, etc.)
            model_name: Optional model name override
            
        Returns:
            ModelConfig instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        provider_enum = ModelProvider(provider.lower())
        
        # Map providers to their environment variable names
        api_key_vars = {
            ModelProvider.ANTHROPIC: 'ANTHROPIC_API_KEY',
            ModelProvider.OPENAI: 'OPENAI_API_KEY',
        }
        
        api_key = os.environ.get(api_key_vars[provider_enum])
        if not api_key:
            raise ValueError(f"API key not found. Please set {api_key_vars[provider_enum]} environment variable")
        
        # Default model names for each provider
        default_models = {
            ModelProvider.ANTHROPIC: 'claude-opus-4-1-20250805',
            ModelProvider.OPENAI: 'gpt-4o',
        }
        
        return cls(
            provider=provider_enum,
            model_name=model_name or default_models[provider_enum],
            api_key=api_key,
            timeout_seconds=int(os.environ.get('AI_TIMEOUT_SECONDS', '180')),
            max_retries=int(os.environ.get('AI_MAX_RETRIES', '3')),
            max_tokens=int(os.environ.get('AI_MAX_TOKENS', '16384'))
        )


class AIModelClient(ABC):
    """Abstract base class for AI model clients."""
    
    def __init__(self, config: ModelConfig):
        """Initialize AI model client.
        
        Args:
            config: Model configuration
        """
        self.config = config
    
    @abstractmethod
    def validate_api_access(self) -> Tuple[bool, str]:
        """Validate that API access is working.
        
        Returns:
            Tuple of (success, error_message)
        """
        pass
    
    @abstractmethod
    def call_with_retry(self, 
                       prompt: str,
                       system_prompt: Optional[str] = None,
                       max_tokens: Optional[int] = None) -> Tuple[bool, str, str]:
        """Make AI API call with retry logic.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (success, response_text, error_message)
        """
        pass
    
    @abstractmethod
    def analyze_single_finding(self, 
                              finding: Dict[str, Any], 
                              pr_context: Optional[Dict[str, Any]] = None,
                              custom_filtering_instructions: Optional[str] = None) -> Tuple[bool, Dict[str, Any], str]:
        """Analyze a single security finding to filter false positives.
        
        Args:
            finding: Single security finding to analyze
            pr_context: Optional PR context for better analysis
            custom_filtering_instructions: Optional custom filtering instructions
            
        Returns:
            Tuple of (success, analysis_result, error_message)
        """
        pass
    
    @abstractmethod
    def generate_system_prompt(self) -> str:
        """Generate system prompt for security analysis."""
        pass
    
    @abstractmethod
    def generate_single_finding_prompt(self, 
                                     finding: Dict[str, Any], 
                                     pr_context: Optional[Dict[str, Any]] = None,
                                     custom_filtering_instructions: Optional[str] = None) -> str:
        """Generate prompt for analyzing a single security finding.
        
        Args:
            finding: Single security finding
            pr_context: Optional PR context
            custom_filtering_instructions: Optional custom filtering instructions
            
        Returns:
            Formatted prompt string
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.config.provider.value
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.config.model_name
