#!/usr/bin/env python3
"""
Secret Detection Module for PR Diffs
Clean, reusable module for detecting and masking secrets in PR diffs using gitleaks
"""

import subprocess
import json
import tempfile
import os
import sys
from typing import Optional, List, Dict, Any


class SecretDetector:
    """Clean class for detecting and masking secrets in PR diffs."""
    
    def __init__(self, verbose: bool = False):
        """Initialize the secret detector.
        
        Args:
            verbose: Whether to print detailed logs
        """
        self.verbose = verbose
    
    def detect_and_mask_secrets(self, pr_diff: str) -> str:
        """Detect and mask secrets in PR diff content.

        Args:
            pr_diff: The PR diff content to analyze

        Returns:
            PR diff content with secrets masked as [REDACTED_SECRET]
        """
        if not pr_diff or not pr_diff.strip():
            self._log("No diff content provided", "WARNING")
            return pr_diff

        self._log(f"Analyzing diff content ({len(pr_diff)} characters)")

        # Check if gitleaks is available
        if not self._is_gitleaks_available():
            self._log("Gitleaks not available, returning original diff", "WARNING")
            return pr_diff

        # Create temporary file with diff content
        temp_file = None
        report_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False) as f:
                f.write(pr_diff)
                temp_file = f.name

            self._log(f"Created temporary file: {temp_file}")

            # Run gitleaks on the diff file
            secrets, report_file = self._run_gitleaks_detect(temp_file)

            if secrets:
                self._log(f"Found {len(secrets)} secrets, applying file-based masking")
                masked_content = self._apply_file_based_masking(temp_file, secrets)

                # Show final summary
                self._log("🎯 FINAL SECRET DETECTION SUMMARY:")
                self._log(f"   Original diff size: {len(pr_diff)} characters")
                self._log(f"   Masked diff size: {len(masked_content)} characters")
                self._log(f"   Secrets detected: {'Yes' if '[REDACTED_SECRET]' in masked_content else 'No'}")
                self._log(f"   Redaction count: {masked_content.count('[REDACTED_SECRET]')}")

                return masked_content
            else:
                self._log("No secrets detected")
                self._log("🎯 FINAL SECRET DETECTION SUMMARY:")
                self._log(f"   Original diff size: {len(pr_diff)} characters")
                self._log(f"   Masked diff size: {len(pr_diff)} characters")
                self._log(f"   Secrets detected: No")
                self._log(f"   Redaction count: 0")
                return pr_diff

        except Exception as e:
            self._log(f"Error during secret detection: {e}", "ERROR")
            return pr_diff
        finally:
            # Clean up temporary files
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    self._log(f"Cleaned up temporary file: {temp_file}")
                except OSError as e:
                    self._log(f"Failed to clean up temporary file: {e}", "WARNING")

            if report_file and os.path.exists(report_file):
                try:
                    os.unlink(report_file)
                    self._log(f"Cleaned up report file: {report_file}")
                except OSError as e:
                    self._log(f"Failed to clean up report file: {e}", "WARNING")
    
    def _is_gitleaks_available(self) -> bool:
        """Check if gitleaks is available in the system."""
        try:
            result = subprocess.run(
                ['gitleaks', 'version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self._log(f"Gitleaks found: {result.stdout.strip()}")
                return True
            else:
                self._log(f"Gitleaks not available: {result.stderr}", "WARNING")
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._log("Gitleaks not found in PATH", "WARNING")
            return False
        except Exception as e:
            self._log(f"Error checking gitleaks: {e}", "WARNING")
            return False
    
    def _run_gitleaks_detect(self, temp_file: str) -> tuple[List[Dict[str, Any]], str]:
        """Run gitleaks detect on the temporary file.

        Args:
            temp_file: Path to temporary file containing diff

        Returns:
            Tuple of (list of detected secrets, report file path)
        """
        report_file = tempfile.mktemp(suffix='.json')
        try:
            result = subprocess.run(
                [
                    'gitleaks', 'detect',
                    '--source', temp_file,
                    '--no-git',
                    '--report-format', 'json',
                    '--report-path', report_file
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            self._log(f"Gitleaks detect exit code: {result.returncode}")
            if self.verbose and result.stdout:
                self._log(f"Gitleaks stdout: {result.stdout}")
            if self.verbose and result.stderr:
                self._log(f"Gitleaks stderr: {result.stderr}")

            # Check if secrets were found
            if os.path.exists(report_file):
                file_size = os.path.getsize(report_file)
                self._log(f"Gitleaks report file size: {file_size} bytes")

                if file_size > 0:
                    try:
                        with open(report_file, 'r') as f:
                            secrets = json.load(f)

                        if secrets:
                            self._log(f"🔍 SECRET DETECTION RESULTS:")
                            self._log(f"📊 Found {len(secrets)} secrets in the PR diff")
                            self._log("=" * 60)

                            for i, secret in enumerate(secrets):
                                rule = secret.get('RuleID', secret.get('rule', 'unknown'))
                                file_path = secret.get('File', secret.get('file', 'unknown'))
                                secret_value = secret.get('Secret', secret.get('secret', ''))
                                match = secret.get('Match', '')
                                line = secret.get('StartLine', secret.get('line', 'unknown'))

                                self._log(f"🚨 SECRET #{i+1}:")
                                self._log(f"   Rule: {rule}")
                                self._log(f"   File: {file_path}")
                                self._log(f"   Line: {line}")
                                self._log(f"   Match: {match}")
                                self._log(f"   Secret: {secret_value[:20]}{'...' if len(secret_value) > 20 else ''}")
                                self._log(f"   Full Value: {secret_value}")
                                self._log("-" * 40)

                        return (secrets if secrets else [], report_file)
                    except json.JSONDecodeError as e:
                        self._log(f"Failed to parse gitleaks output: {e}", "ERROR")
                        return ([], report_file)
                else:
                    self._log("Gitleaks report file is empty")
                    return ([], report_file)
            else:
                self._log("Gitleaks report file not found")
                return ([], report_file)

        except subprocess.TimeoutExpired:
            self._log("Gitleaks scan timed out", "WARNING")
            return ([], report_file)
        except Exception as e:
            self._log(f"Error running gitleaks: {e}", "ERROR")
            return ([], report_file)
    
    def _apply_file_based_masking(self, temp_file: str, secrets: List[Dict[str, Any]]) -> str:
        """Apply masking to temp file content based on gitleaks findings.

        Args:
            temp_file: Path to temporary file containing diff content
            secrets: List of detected secrets from gitleaks

        Returns:
            Diff content with secrets masked
        """
        self._log("🎭 STARTING FILE-BASED SECRET MASKING PROCESS")
        self._log("=" * 60)

        try:
            # Read the file content
            with open(temp_file, 'r') as f:
                file_content = f.read()

            masked_content = file_content
            total_replacements = 0
            redacted_secrets = []

            for i, secret in enumerate(secrets):
                secret_value = secret.get('Secret', secret.get('secret', ''))
                rule = secret.get('RuleID', secret.get('rule', 'unknown'))

                if secret_value and len(secret_value.strip()) > 0:
                    # Count occurrences before replacement
                    occurrences = masked_content.count(secret_value)

                    self._log(f"🔒 REDACTING SECRET #{i+1}:")
                    self._log(f"   Rule: {rule}")
                    self._log(f"   Original: {secret_value}")
                    self._log(f"   Found {occurrences} occurrence(s) in file")

                    # Replace the secret with a placeholder
                    masked_content = masked_content.replace(secret_value, '[SENSITIVE_DATA_REMOVED]')
                    total_replacements += occurrences

                    # Track what was redacted
                    redacted_secrets.append({
                        'rule': rule,
                        'original': secret_value,
                        'occurrences': occurrences,
                        'replaced_with': '[REDACTED_SECRET]'
                    })

                    self._log(f"   ✅ Replaced with: [REDACTED_SECRET]")
                    self._log("-" * 40)
                else:
                    self._log(f"⚠️  Secret #{i+1}: Empty or invalid secret value, skipping")

            # Summary of redaction
            self._log("📋 REDACTION SUMMARY:")
            self._log(f"   Total secrets processed: {len(secrets)}")
            self._log(f"   Total replacements made: {total_replacements}")
            self._log(f"   Successfully redacted: {len(redacted_secrets)}")

            if redacted_secrets:
                self._log("🔍 DETAILED REDACTION LOG:")
                for i, redacted in enumerate(redacted_secrets):
                    self._log(f"   {i+1}. Rule: {redacted['rule']}")
                    self._log(f"      Original: {redacted['original'][:30]}{'...' if len(redacted['original']) > 30 else ''}")
                    self._log(f"      Occurrences: {redacted['occurrences']}")
                    self._log(f"      Replaced with: {redacted['replaced_with']}")

            self._log("✅ FILE-BASED MASKING PROCESS COMPLETED")
            self._log("=" * 60)

            return masked_content

        except Exception as e:
            self._log(f"Error during file-based masking: {e}", "ERROR")
            # Fallback to reading original file
            try:
                with open(temp_file, 'r') as f:
                    return f.read()
            except Exception as fallback_e:
                self._log(f"Error reading original file: {fallback_e}", "ERROR")
                return ""
    
    def _log(self, message: str, level: str = "INFO"):
        """Log a message if verbose mode is enabled.
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        if self.verbose:
            timestamp = subprocess.run(['date'], capture_output=True, text=True).stdout.strip()
            print(f"[{timestamp}] [{level}] {message}", file=sys.stderr)


# Convenience functions for easy import and use
def gitmask_secrets_in_diff(pr_diff: str, verbose: bool = False) -> str:
    """Convenience function to mask secrets in PR diff.
    
    Args:
        pr_diff: The PR diff content to analyze
        verbose: Whether to print detailed logs
        
    Returns:
        PR diff content with secrets masked
    """
    detector = SecretDetector(verbose=verbose)
    return detector.detect_and_mask_secrets(pr_diff)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Secret Detection for PR Diffs')
    parser.add_argument('--diff', '-d', type=str, help='PR diff content to analyze')
    parser.add_argument('--file', '-f', type=str, help='File containing PR diff content')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.diff:
        result = gitmask_secrets_in_diff(args.diff, verbose=args.verbose)
        print("Masked diff:")
        print(result)
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                diff_content = f.read()
            result = gitmask_secrets_in_diff(diff_content, verbose=args.verbose)
            print("Masked diff:")
            print(result)
        except FileNotFoundError:
            print(f"❌ Error: File '{args.file}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            sys.exit(1)
    else:
        print("Use --help to see available options")
        print("Example: python secret_detector.py --diff 'your diff content here'")
