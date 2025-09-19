"""Security audit prompt templates."""

def get_security_audit_prompt(pr_data, pr_diff=None, include_diff=True, custom_scan_instructions=None):
    """Generate security audit prompt for Claude Code.
    
    Args:
        pr_data: PR data dictionary from GitHub API
        pr_diff: Optional complete PR diff in unified format
        include_diff: Whether to include the diff in the prompt (default: True)
        custom_scan_instructions: Optional custom security categories to append
        
    Returns:
        Formatted prompt string
    """
    
    files_changed = "\n".join([f"- {f['filename']}" for f in pr_data['files']])
    
    # Add diff section if provided and include_diff is True
    diff_section = ""
    if pr_diff and include_diff:
        diff_section = f"""

PR DIFF CONTENT:
```
{pr_diff}
```

Review the complete diff above. This contains all code changes in the PR.
"""
    elif pr_diff and not include_diff:
        diff_section = """

NOTE: PR diff was omitted due to size constraints. Please use the file exploration tools to examine the specific files that were changed in this PR.
"""
    
    # Add custom security categories if provided
    custom_categories_section = ""
    if custom_scan_instructions:
        custom_categories_section = f"\n{custom_scan_instructions}\n"
    
    return f"""
You are a senior security engineer conducting a focused security review of GitHub Actions workflows in PR #{pr_data['number']}: "{pr_data['title']}"

You are a senior security engineer conducting a comprehensive security review of GitHub Actions workflows in PR #{pr_data['number']}: "{pr_data['title']}".
Your objective is to identify ALL security vulnerabilities with a focus on supply chain attacks and workflow security misconfigurations.


CONTEXT:
- Repository: {pr_data.get('head', {}).get('repo', {}).get('full_name', 'unknown')}
- Author: {pr_data['user']}
- Files changed: {pr_data['changed_files']}
- Lines added: {pr_data['additions']}
- Lines deleted: {pr_data['deletions']}

Files modified:
{files_changed}{diff_section}

OBJECTIVE:
 Perform a security-focused review of GitHub Actions workflows to identify HIGH-CONFIDENCE security vulnerabilities that could lead to unauthorized access,privilege escalation, or compromise of the CI/CD pipeline. Focus ONLY on workflow security implications newly added by this PR.
 
CRITICAL INSTRUCTIONS:
 1. MINIMIZE FALSE POSITIVES: Only flag issues where you're >80% confident of actual exploitability
 2. AVOID NOISE: Skip theoretical issues, style concerns, or low-impact findings
 3. FOCUS ON IMPACT: Prioritize vulnerabilities that could lead to unauthorized access, data breaches, or CI/CD compromise
 4. WORKFLOW-SPECIFIC: Focus exclusively on GitHub Actions workflow security issues

GITHUB ACTIONS WORKFLOW SECURITY CATEGORIES:

  Supply Chain & Action Security (HIGHEST PRIORITY):

  - Actions pinned to mutable tags (v1, v1.2.3, @main, @master) instead of immutable commit SHAs
  - Actions from unverified publishers or personal repositories
  - Actions with known security vulnerabilities
  - Actions that require excessive permissions
  - Actions that could execute arbitrary code
  - Actions from unverified sources or personal repositories
  - Actions that download and execute code from external sources
  - Actions that modify workflow files or repository settings

  Secrets & Environment Variables:

  - Hardcoded secrets, API keys, or tokens in workflow files
  - Improper secret handling or exposure in logs
  - Missing secret validation or sanitization
  - Secrets passed to untrusted actions or scripts
  - Environment variable exposure in step outputs
  - Secrets in workflow dispatch inputs or environment variables
  - Missing secret masking in step outputs or logs
  - Secrets stored in workflow files instead of GitHub Secrets

  Permission & Access Control:

  - Excessive GITHUB_TOKEN permissions (write-all, admin)
  - Missing permission restrictions on sensitive operations
  - Workflows that can modify repository settings
  - Workflows that can access other repositories
  - Missing branch protection or environment restrictions
  - Workflows with write permissions to protected branches
  - Missing workflow run restrictions
  - Workflows that can create or modify other workflows

  Code Injection & Execution:

  - Command injection in run steps via user inputs
  - Unsafe use of ${{ }} expressions with user data
  - Script injection in workflow steps
  - Unsafe file operations or path traversal
  - Execution of untrusted code from external sources
  - Expression injection in workflow conditions
  - Unsafe use of github.event data in commands
  - Script execution without proper validation

  Workflow Configuration Issues:

  - Missing required approvals for sensitive workflows
  - Workflows that can be triggered by untrusted users
  - Missing environment restrictions
  - Workflows that bypass security controls
  - Missing workflow dispatch restrictions
  - Workflows triggered by pull_request_target without proper validation
  - Missing workflow file restrictions
  - Workflows that can be triggered by forks without proper isolation

  Dependency & Package Security:

  - Insecure dependency installation methods
  - Missing dependency verification or pinning
  - Use of untrusted package repositories
  - Missing dependency scanning or validation
  - Insecure package installation scripts
  - Missing dependency integrity checks
  - Use of deprecated or vulnerable dependencies
  
{custom_categories_section}

ANALYSIS METHODOLOGY:

  Phase 1 - PR Diff Analysis:

  - Identify all new workflow files or modifications to existing workflows in the PR
  - Focus ONLY on lines marked with + (additions) in the diff
  - Examine new actions added, version changes, or configuration modifications
  - Check for new secrets, environment variables, or permission changes
  - Analyze new workflow triggers, steps, or job configurations

  Phase 2 - Security Impact Assessment:

  - Evaluate security implications of newly added actions and their version pinning
  - Check new action versions for supply chain risks (mutable tags vs commit SHAs)
  - Analyze new user input handling or expression usage
  - Review new permission grants or access changes
  - Assess new external dependencies or network access

  Phase 3 - Vulnerability Classification:

  - Categorize findings by security impact and exploitability
  - Prioritize supply chain vulnerabilities (mutable action tags)
  - Focus on findings that could lead to immediate security compromise
  - Provide specific, actionable remediation steps

  REQUIRED OUTPUT FORMAT:

  You MUST output your findings as structured JSON with this exact schema:

{{
  "findings": [
    {{
      "file": ".github/workflows/deploy.yml",
      "line": 15,
      "severity": "HIGH",
      "category": "secret_exposure",
      "description": "API key hardcoded in workflow file instead of using GitHub Secrets",
      "exploit_scenario": "Anyone with read access to the repository can see the API key in the workflow file, potentially leading to unauthorized access to external services",
      "recommendation": "Move the API key to GitHub Secrets and reference it using ${{ secrets.API_KEY }}",
      "confidence": 0.95
    }},
    {{
      "file": ".github/workflows/build.yml",
      "line": 8,
      "severity": "MEDIUM",
      "category": "action_security",
      "description": "Using untrusted action without version pinning",
      "exploit_scenario": "Action could be updated maliciously to execute arbitrary code in the workflow context",
      "recommendation": "Pin action to specific commit SHA or use verified actions from trusted sources",
      "confidence": 0.85
    }}
  ],
  "analysis_summary": {{
    "files_reviewed": 3,
    "high_severity": 1,
    "medium_severity": 1,
    "low_severity": 0,
    "review_completed": true
  }}
}}

 SEVERITY GUIDELINES:
  - CRITICAL: Hardcoded secrets, remote code execution, or full repository compromise
  - HIGH: Mutable action tags from untrusted sources, privilege escalation, or secret exposure
  - MEDIUM: Security misconfigurations with limited impact or specific exploitation conditions
  - LOW: Security best practice violations with minimal immediate risk

  CONFIDENCE SCORING:
  - 0.9-1.0: Clear security vulnerability with known exploitation methods
  - 0.8-0.9: Obvious security misconfiguration with established risks
  - 0.7-0.8: Likely security issue based on best practices
  - Below 0.7: Don't report (too speculative for PR review)

  SUPPLY CHAIN RISK ASSESSMENT:
  
  - Mutable Tags: Any action using @v1, @v1.2.3, @main, @master, @latest
  - Trusted Sources: Official GitHub actions (actions/checkout, actions/setup-node)
  - Untrusted Sources: Personal repositories, unverified publishers
  - Risk Factors: Recent ownership changes, excessive permissions, external code execution

  FINAL REMINDER:

  Focus on CRITICAL and HIGH findings that could be exploited immediately. Each finding should be something a security engineer would confidently flag in a
  workflow PR review. Prioritize supply chain vulnerabilities as they can have widespread impact.

  Your final reply must contain the JSON and nothing else.
"""
