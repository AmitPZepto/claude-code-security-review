"""AI-powered security runner that supports multiple providers."""

import os
import sys
import json
import time
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

from claudecode.ai_models import get_model_client
from claudecode.constants import DEFAULT_CLAUDE_MODEL, SUBPROCESS_TIMEOUT
from claudecode.json_parser import parse_json_with_fallbacks
from claudecode.logger import get_logger

logger = get_logger(__name__)


class AISecurityRunner:
    """AI-powered security runner that supports multiple providers."""
    
    def __init__(self, timeout_minutes: Optional[int] = None):
        """Initialize AI security runner.
        
        Args:
            timeout_minutes: Timeout for AI execution (defaults to SUBPROCESS_TIMEOUT)
        """
        if timeout_minutes is not None:
            self.timeout_seconds = timeout_minutes * 60
        else:
            self.timeout_seconds = SUBPROCESS_TIMEOUT
        
        # Get AI provider and model from environment
        self.provider = os.environ.get('AI_PROVIDER', 'anthropic')
        self.model = os.environ.get('AI_MODEL')
        
        # Initialize AI client
        try:
            self.ai_client = get_model_client(self.provider, self.model)
            logger.info(f"AI Security Runner initialized with {self.provider}")
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            raise
    
    def run_security_audit(self, repo_dir: Path, prompt: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Run AI-powered security audit.
        
        Args:
            repo_dir: Path to repository directory
            prompt: Security audit prompt
            
        Returns:
            Tuple of (success, error_message, parsed_results)
        """
        if not repo_dir.exists():
            return False, f"Repository directory does not exist: {repo_dir}", {}
        
        # Check prompt size
        prompt_size = len(prompt.encode('utf-8'))
        if prompt_size > 1024 * 1024:  # 1MB
            print(f"[Warning] Large prompt size: {prompt_size / 1024 / 1024:.2f}MB", file=sys.stderr)
        
        try:
            # Run AI security analysis with retry logic (no separate system prompt)
            # The prompt already contains all the instructions
            NUM_RETRIES = 3
            for attempt in range(NUM_RETRIES):
                print(f"[Debug] Running {self.provider} security analysis attempt {attempt + 1}/{NUM_RETRIES}", file=sys.stderr)
                print(f"[Debug] Model: {self.ai_client.get_model_name()}", file=sys.stderr)
                print(f"[Debug] Prompt length: {len(prompt)} characters", file=sys.stderr)
                
                success, response_text, error_msg = self.ai_client.call_with_retry(
                    prompt=prompt,
                    system_prompt=None,  # No separate system prompt - everything is in the main prompt
                    max_tokens=16384
                )
                
                if success:
                    print(f"[Debug] AI security analysis successful", file=sys.stderr)
                    print(f"[Debug] Response length: {len(response_text)} characters", file=sys.stderr)
                    
                    # Parse JSON response
                    success, parsed_result = parse_json_with_fallbacks(response_text, f"{self.provider} security analysis")
                    
                    if success:
                        # Extract security findings
                        parsed_results = self._extract_security_findings(parsed_result)
                        return True, "", parsed_results
                    else:
                        if attempt == 0:
                            print(f"[Debug] JSON parsing failed, retrying...", file=sys.stderr)
                            time.sleep(2)
                            continue
                        else:
                            return False, "Failed to parse AI response as JSON", {}
                else:
                    if attempt == 0:
                        print(f"[Debug] AI call failed: {error_msg}, retrying...", file=sys.stderr)
                        time.sleep(2)
                        continue
                    else:
                        return False, f"AI security analysis failed: {error_msg}", {}
            
            return False, "Unexpected error in retry logic", {}
            
        except Exception as e:
            return False, f"AI security analysis error: {str(e)}", {}
    
    
    def _extract_security_findings(self, ai_output: Any) -> Dict[str, Any]:
        """Extract security findings from AI's JSON response."""
        if isinstance(ai_output, dict):
            if 'findings' in ai_output:
                return ai_output
        
        # Return empty structure if no findings found
        return {
            'findings': [],
            'analysis_summary': {
                'files_reviewed': 0,
                'high_severity': 0,
                'medium_severity': 0,
                'low_severity': 0,
                'review_completed': False,
            }
        }
    
    def validate_ai_available(self) -> Tuple[bool, str]:
        """Validate that AI client is available."""
        try:
            # Test AI client access
            valid, error = self.ai_client.validate_api_access()
            if valid:
                return True, ""
            else:
                return False, f"AI client validation failed: {error}"
        except Exception as e:
            return False, f"Failed to validate AI client: {str(e)}"
