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

CONTEXT:
- Repository: {pr_data.get('head', {}).get('repo', {}).get('full_name', 'unknown')}
- Author: {pr_data['user']}
- Files changed: {pr_data['changed_files']}
- Lines added: {pr_data['additions']}
- Lines deleted: {pr_data['deletions']}

Files modified:
{files_changed}{diff_section}

OBJECTIVE:
Perform a security-focused review of GitHub Actions workflows to identify HIGH-CONFIDENCE security vulnerabilities that could lead to unauthorized access, privilege escalation, or compromise of the CI/CD pipeline. Focus ONLY on workflow security implications newly added by this PR.

CRITICAL INSTRUCTIONS:
1. MINIMIZE FALSE POSITIVES: Only flag issues where you're >80% confident of actual exploitability
2. AVOID NOISE: Skip theoretical issues, style concerns, or low-impact findings
3. FOCUS ON IMPACT: Prioritize vulnerabilities that could lead to unauthorized access, data breaches, or CI/CD compromise
4. WORKFLOW-SPECIFIC: Focus exclusively on GitHub Actions workflow security issues

GITHUB ACTIONS WORKFLOW SECURITY CATEGORIES:

**Secrets & Environment Variables:**
- Hardcoded secrets, API keys, or tokens in workflow files
- Improper secret handling or exposure in logs
- Missing secret validation or sanitization
- Secrets passed to untrusted actions or scripts
- Environment variable exposure in step outputs
- Secrets in workflow dispatch inputs or environment variables
- Missing secret masking in step outputs or logs
- Secrets stored in workflow files instead of GitHub Secrets

**Action Security:**
- Use of untrusted or unverified third-party actions
- Actions with known security vulnerabilities
- Actions that require excessive permissions
- Actions that could execute arbitrary code
- Missing action version pinning (using @main or @master)
- Actions from unverified sources or personal repositories
- Actions that download and execute code from external sources
- Actions that modify workflow files or repository settings

**Permission & Access Control:**
- Excessive GITHUB_TOKEN permissions (write-all, admin)
- Missing permission restrictions on sensitive operations
- Workflows that can modify repository settings
- Workflows that can access other repositories
- Missing branch protection or environment restrictions
- Workflows with write permissions to protected branches
- Missing workflow run restrictions
- Workflows that can create or modify other workflows

**Code Injection & Execution:**
- Command injection in run steps via user inputs
- Unsafe use of ${{ }} expressions with user data
- Script injection in workflow steps
- Unsafe file operations or path traversal
- Execution of untrusted code from external sources
- Expression injection in workflow conditions
- Unsafe use of github.event data in commands
- Script execution without proper validation

**Workflow Configuration Issues:**
- Missing required approvals for sensitive workflows
- Workflows that can be triggered by untrusted users
- Missing environment restrictions
- Workflows that bypass security controls
- Missing workflow dispatch restrictions
- Workflows triggered by pull_request_target without proper validation
- Missing workflow file restrictions
- Workflows that can be triggered by forks without proper isolation

**Artifact & Cache Security:**
- Insecure artifact handling or storage
- Cache poisoning vulnerabilities
- Artifacts containing sensitive data
- Missing artifact cleanup or retention policies
- Unsafe artifact sharing between workflows
- Artifacts with overly broad permissions
- Missing artifact integrity verification
- Artifacts stored in public locations

**Network & External Access:**
- Workflows making insecure external API calls
- Missing TLS/SSL verification
- Workflows that expose internal services
- Insecure network configurations
- Missing firewall or network restrictions
- Workflows that make requests to internal services
- Missing certificate validation
- Insecure communication protocols

**Workflow Triggers & Events:**
- Dangerous workflow triggers (pull_request_target, workflow_dispatch)
- Missing trigger validation or restrictions
- Workflows triggered by untrusted events
- Missing event data validation
- Workflows that can be triggered by external users
- Missing workflow file path restrictions
- Workflows triggered by deleted or force-pushed commits

**Dependency & Supply Chain:**
- Insecure dependency installation methods
- Missing dependency verification or pinning
- Use of untrusted package repositories
- Missing dependency scanning or validation
- Insecure package installation scripts
- Missing dependency integrity checks
- Use of deprecated or vulnerable dependencies

**Container & Runner Security:**
- Insecure container configurations
- Missing container security scanning
- Use of untrusted base images
- Missing container resource restrictions
- Insecure container registry access
- Missing container image verification
- Containers with excessive privileges
{custom_categories_section}

ANALYSIS METHODOLOGY:

Phase 1 - Workflow Structure Analysis:
- Identify all workflow files and their triggers (push, pull_request, pull_request_target, workflow_dispatch, etc.)
- Examine workflow permissions and access controls (GITHUB_TOKEN, repository permissions)
- Check for proper secret management practices (GitHub Secrets vs hardcoded values)
- Review action usage, version pinning, and source verification
- Analyze workflow file locations and path restrictions

Phase 2 - Security Control Review:
- Verify proper permission restrictions and principle of least privilege
- Check for required approvals, environment restrictions, and branch protection
- Examine secret handling, masking, and exposure risks
- Review action security, trustworthiness, and supply chain risks
- Validate workflow trigger conditions and event data handling

Phase 3 - Vulnerability Assessment:
- Look for injection points in workflow steps (command injection, expression injection)
- Check for privilege escalation opportunities and permission abuse
- Identify potential data exposure risks (secrets, artifacts, logs)
- Examine external access, network security, and dependency risks
- Assess container security, runner configurations, and isolation issues

Phase 4 - Advanced Security Analysis:
- Check for workflow chaining and cross-workflow dependencies
- Analyze artifact sharing and cache security implications
- Review workflow dispatch inputs and external trigger validation
- Examine fork security and pull_request_target vulnerabilities
- Assess supply chain risks in actions and dependencies

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
- **HIGH**: Workflow vulnerabilities that could lead to repository compromise, secret exposure, or unauthorized code execution
- **MEDIUM**: Workflow issues that could lead to privilege escalation or data exposure with specific conditions
- **LOW**: Workflow configuration issues that improve security posture but have limited immediate impact

CONFIDENCE SCORING:
- 0.9-1.0: Clear workflow security vulnerability with known exploitation methods
- 0.8-0.9: Obvious security misconfiguration in workflow setup
- 0.7-0.8: Suspicious workflow pattern requiring specific conditions to exploit
- Below 0.7: Don't report (too speculative for workflow security)

FINAL REMINDER:
Focus on CRITICAL, HIGH and MEDIUM findings only. Better to miss some theoretical issues than flood the report with false positives. Each finding should be something a security engineer would confidently raise in a workflow PR review.

IMPORTANT EXCLUSIONS - DO NOT REPORT:
- General code quality issues not related to workflow security
- Performance or efficiency concerns in workflows
- Workflow organization or structure issues without security implications
- Missing documentation or comments in workflow files
- Workflow naming conventions or cosmetic issues

Begin your analysis now. Use the repository exploration tools to understand the codebase context, then analyze the PR changes for security implications.

Your final reply must contain the JSON and nothing else. You should not reply again after outputting the JSON.
"""
