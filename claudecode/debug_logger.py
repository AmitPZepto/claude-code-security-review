"""
Centralized debug logging utility for Claude Code Security Review
Provides consistent debug logging across all modules without corrupting JSON output
"""

import os
import sys
import json
from typing import Any, Dict, Optional
from datetime import datetime


class DebugLogger:
    """Centralized debug logger that writes to stderr and files without corrupting stdout."""

    def __init__(self, module_name: str = "unknown"):
        self.module_name = module_name
        self.debug_enabled = os.environ.get('CLAUDE_DEBUG', 'false').lower() == 'true'
        self.verbose_enabled = os.environ.get('CLAUDE_VERBOSE', 'false').lower() == 'true'
        self.log_to_file = os.environ.get('CLAUDE_LOG_FILE', 'false').lower() == 'true'
        self.debug_file = 'claude-debug.log'

    def _get_timestamp(self) -> str:
        """Get formatted timestamp."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_to_stderr(self, message: str, level: str = "DEBUG"):
        """Write message to stderr with formatting."""
        timestamp = self._get_timestamp()
        formatted_msg = f"[{timestamp}] [{level}] [{self.module_name}] {message}"
        print(formatted_msg, file=sys.stderr)
        sys.stderr.flush()

    def _write_to_file(self, message: str, level: str = "DEBUG"):
        """Write message to debug file."""
        if not self.log_to_file:
            return

        timestamp = self._get_timestamp()
        formatted_msg = f"[{timestamp}] [{level}] [{self.module_name}] {message}\n"

        try:
            with open(self.debug_file, 'a') as f:
                f.write(formatted_msg)
        except Exception:
            pass  # Silently ignore file write errors

    def debug(self, message: str):
        """Log debug message."""
        if not self.debug_enabled:
            return

        self._write_to_stderr(message, "DEBUG")
        self._write_to_file(message, "DEBUG")

    def info(self, message: str):
        """Log info message."""
        if not (self.debug_enabled or self.verbose_enabled):
            return

        self._write_to_stderr(message, "INFO")
        self._write_to_file(message, "INFO")

    def warning(self, message: str):
        """Log warning message."""
        self._write_to_stderr(message, "WARN")
        self._write_to_file(message, "WARN")

    def error(self, message: str):
        """Log error message."""
        self._write_to_stderr(message, "ERROR")
        self._write_to_file(message, "ERROR")

    def section(self, title: str, content: str = ""):
        """Log a section with visual separation."""
        if not self.debug_enabled:
            return

        separator = "=" * 60
        self.debug(separator)
        self.debug(f"🔍 {title}")
        self.debug(separator)

        if content:
            self.debug(content)
            self.debug(separator)

    def json_data(self, title: str, data: Any):
        """Log JSON data in a readable format."""
        if not self.debug_enabled:
            return

        try:
            json_str = json.dumps(data, indent=2)
            self.section(title, json_str)
        except Exception as e:
            self.debug(f"Failed to serialize JSON for {title}: {e}")

    def api_request(self, endpoint: str, method: str = "POST", headers: Optional[Dict] = None, payload_preview: str = ""):
        """Log API request details."""
        if not self.debug_enabled:
            return

        self.section(f"API REQUEST - {method} {endpoint}")

        if headers:
            # Mask sensitive headers
            safe_headers = {}
            for k, v in headers.items():
                if 'auth' in k.lower() or 'key' in k.lower() or 'token' in k.lower():
                    safe_headers[k] = f"{v[:10]}..." if len(v) > 10 else "[MASKED]"
                else:
                    safe_headers[k] = v
            self.debug(f"Headers: {json.dumps(safe_headers, indent=2)}")

        if payload_preview:
            self.debug(f"Payload preview: {payload_preview[:300]}...")

    def api_response(self, status_code: int, response_preview: str = "", duration: float = 0):
        """Log API response details."""
        if not self.debug_enabled:
            return

        self.section(f"API RESPONSE - Status: {status_code}")

        if duration > 0:
            self.debug(f"Duration: {duration:.2f}s")

        if response_preview:
            self.debug(f"Response preview: {response_preview[:300]}...")

    def claude_prompt(self, prompt_type: str, system_prompt: str = "", user_prompt: str = ""):
        """Log Claude API prompts."""
        if not self.debug_enabled:
            return

        self.section(f"CLAUDE {prompt_type} PROMPT")

        if system_prompt:
            self.debug(f"System prompt length: {len(system_prompt)} chars")
            self.debug(f"System prompt preview: {system_prompt[:200]}...")

            if os.environ.get('CLAUDE_FULL_PROMPTS', 'false').lower() == 'true':
                self.debug("FULL SYSTEM PROMPT:")
                self.debug(system_prompt)

        if user_prompt:
            self.debug(f"User prompt length: {len(user_prompt)} chars")
            self.debug(f"User prompt preview: {user_prompt[:200]}...")

            if os.environ.get('CLAUDE_FULL_PROMPTS', 'false').lower() == 'true':
                self.debug("FULL USER PROMPT:")
                self.debug(user_prompt)

    def claude_response(self, response_text: str, input_tokens: int = 0, output_tokens: int = 0, duration: float = 0):
        """Log Claude API response."""
        if not self.debug_enabled:
            return

        self.section("CLAUDE API RESPONSE")

        if duration > 0:
            self.debug(f"Duration: {duration:.2f}s")
        if input_tokens > 0:
            self.debug(f"Input tokens: {input_tokens}")
        if output_tokens > 0:
            self.debug(f"Output tokens: {output_tokens}")

        self.debug(f"Response length: {len(response_text)} chars")
        self.debug(f"Response preview: {response_text[:300]}...")

        if os.environ.get('CLAUDE_FULL_RESPONSES', 'false').lower() == 'true':
            self.debug("FULL RESPONSE:")
            self.debug(response_text)

    def timing(self, operation: str, duration: float):
        """Log timing information."""
        self.info(f"⏱️  {operation}: {duration:.2f}s")

    def step(self, step_name: str):
        """Log a processing step."""
        self.info(f"🔄 {step_name}")

    def success(self, message: str):
        """Log success message."""
        self.info(f"✅ {message}")

    def failure(self, message: str):
        """Log failure message."""
        self.error(f"❌ {message}")


# Global instances for easy importing
debug_logger = DebugLogger("global")

def get_debug_logger(module_name: str) -> DebugLogger:
    """Get a debug logger for a specific module."""
    return DebugLogger(module_name)


# Convenience functions
def debug_section(title: str, content: str = ""):
    """Quick debug section."""
    debug_logger.section(title, content)

def debug_json(title: str, data: Any):
    """Quick JSON debug."""
    debug_logger.json_data(title, data)

def debug_step(step_name: str):
    """Quick step debug."""
    debug_logger.step(step_name)
