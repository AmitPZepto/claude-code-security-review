"""Azure OpenAI API client implementation."""

import os
import json
import time
from typing import Dict, Any, Tuple, Optional
from openai import AzureOpenAI
from .base_client import AIModelClient, ModelConfig


class AzureOpenAIClient(AIModelClient):
    """Azure OpenAI API client for security analysis."""
    
    def __init__(self, config: ModelConfig):
        """Initialize Azure OpenAI client.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        
        # Azure OpenAI configuration
        self.azure_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
        self.api_version = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        
        if not self.azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required for Azure OpenAI")
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=self.config.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
        )
    
    def validate_api_access(self) -> Tuple[bool, str]:
        """Validate that Azure OpenAI API access is working.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Test with a simple completion
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True, ""
        except Exception as e:
            return False, f"Azure OpenAI API validation failed: {str(e)}"
    
    def call_with_retry(self, 
                       prompt: str,
                       system_prompt: Optional[str] = None,
                       max_tokens: Optional[int] = None) -> Tuple[bool, str, str]:
        """Make Azure OpenAI API call with retry logic.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (success, response_text, error_message)
        """
        max_tokens = max_tokens or self.config.max_tokens
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.1  # Low temperature for consistent security analysis
                )
                
                response_text = response.choices[0].message.content
                return True, response_text, ""
                
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    return False, "", f"Azure OpenAI API call failed after {self.config.max_retries} attempts: {str(e)}"
                
                # Wait before retry
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return False, "", "Unexpected error in retry logic"
    
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
        try:
            prompt = self.generate_single_finding_prompt(finding, pr_context, custom_filtering_instructions)
            
            success, response_text, error_msg = self.call_with_retry(prompt)
            if not success:
                return False, {}, error_msg
            
            # Parse JSON response
            try:
                analysis_result = json.loads(response_text)
                return True, analysis_result, ""
            except json.JSONDecodeError as e:
                return False, {}, f"Failed to parse JSON response: {str(e)}"
                
        except Exception as e:
            return False, {}, f"Error analyzing finding: {str(e)}"
    
    def generate_system_prompt(self) -> str:
        """Generate system prompt for security analysis."""
        return """You are a senior security engineer conducting a comprehensive security review.
Your objective is to identify security vulnerabilities and provide structured JSON output.

Respond ONLY with valid JSON in the exact format specified in the user prompt.
Do not include explanatory text, markdown formatting, or code blocks."""
    
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
        pr_info = ""
        if pr_context:
            pr_info = f"""
PR Context:
- Repository: {pr_context.get('repo_name', 'unknown')}
- PR Number: {pr_context.get('pr_number', 'unknown')}
- Title: {pr_context.get('title', 'unknown')}
- Description: {pr_context.get('description', 'unknown')}
"""
        
        custom_instructions = ""
        if custom_filtering_instructions:
            custom_instructions = f"\n\nCustom Filtering Instructions:\n{custom_filtering_instructions}"
        
        return f"""You are a senior security engineer reviewing a potential security finding.

{pr_info}

Security Finding to Review:
{json.dumps(finding, indent=2)}

{custom_instructions}

Your task is to determine if this finding is a FALSE POSITIVE or a VALID security issue.

Consider:
1. Is this a real security vulnerability or just a false positive?
2. Is the confidence score appropriate for the severity?
3. Is the exploit scenario realistic?
4. Is the recommendation actionable?

Respond with JSON in this exact format:
{{
  "is_false_positive": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of your decision",
  "updated_severity": "CRITICAL/HIGH/MEDIUM/LOW" (if not false positive)
}}

Respond ONLY with the JSON, no other text."""
    
    def _read_file(self, file_path: str) -> str:
        """Read file content for analysis.
        
        Args:
            file_path: Path to file to read
            
        Returns:
            File content as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"
