"""
Input validation policies for AXIOM.

Implements sanitization and validation for:
- User chat messages (XSS, injection attacks)
- SQL injection prevention
- File path validation
- Configuration values
"""

import re
from pathlib import Path
from typing import Optional, List
from axiom.policy.policies import Policy, PolicyContext, PolicyResult
from axiom.utils.errors import ErrorCode, PolicyError
from axiom.utils.logging import get_logger, log_policy_evaluation

logger = get_logger(__name__)


class InputSanitizationPolicyEnhanced(Policy):
    """
    Enhanced input sanitization that validates all user inputs.
    
    Checks for:
    - SQL injection patterns
    - XSS attempts
    - Path traversal
    - Excessive length
    - Invalid characters
    """
    
    def __init__(self, max_length: int = 500):
        self.max_length = max_length
        
        # SQL injection patterns
        self.sql_patterns = [
            r";\s*--",  # Comment attacks
            r"\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|EXEC|EXECUTE)\b",  # DDL/DML
            r"UNION\s+SELECT",  # Union attacks
            r"'\s*(OR|AND)\s+'",  # Always-true conditions
            r"--",  # SQL comments
            r"/\*.*?\*/",  # Multi-line comments
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",  # Event handlers
            r"<iframe",
            r"<object",
            r"<embed",
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\"
        ]
    
    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Validate and sanitize user input."""
        text = context.user_input or ""
        violations = {}
        
        # Check length
        if len(text) > self.max_length:
            violations["length_exceeded"] = {
                "current": len(text),
                "max": self.max_length
            }
        
        # Check for SQL injection
        for pattern in self.sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations["sql_injection"] = {
                    "pattern": pattern,
                    "detected": "SQL injection attempt detected"
                }
                logger.warning(
                    "SQL injection attempt detected",
                    pattern=pattern,
                    input_preview=text[:100]
                )
                break
        
        # Check for XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations["xss_attempt"] = {
                    "pattern": pattern,
                    "detected": "Cross-site scripting attempt detected"
                }
                logger.warning(
                    "XSS attempt detected",
                    pattern=pattern,
                    input_preview=text[:100]
                )
                break
        
        # Check for path traversal
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, text):
                violations["path_traversal"] = {
                    "pattern": pattern,
                    "detected": "Path traversal attempt detected"
                }
                logger.warning(
                    "Path traversal attempt detected",
                    pattern=pattern,
                    input_preview=text[:100]
                )
                break
        
        passed = not violations
        log_policy_evaluation(
            logger,
            policy_name=self.get_name(),
            passed=passed,
            violations=violations,
            input_length=len(text)
        )
        
        return PolicyResult(passed=passed, violations=violations)
    
    def get_name(self) -> str:
        return "InputSanitizationPolicyEnhanced"
    
    def get_description(self) -> str:
        return "Validates and sanitizes user input against SQL injection, XSS, and path traversal attacks."


class ConfigPathValidationPolicy(Policy):
    """
    Validates that configuration file paths are within the allowed configs/ directory.
    """
    
    def __init__(self, allowed_dir: Path = Path("configs")):
        self.allowed_dir = allowed_dir.resolve()
    
    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Validate configuration file paths."""
        violations = {}
        
        # Check if path is provided in context
        config_path = context.user_input
        if not config_path:
            return PolicyResult(passed=True, violations={})
        
        try:
            # Resolve path and check if it's within allowed directory
            path = Path(config_path).resolve()
            
            # Check if path is within allowed directory
            try:
                path.relative_to(self.allowed_dir)
            except ValueError:
                violations["invalid_path"] = {
                    "path": str(path),
                    "allowed_dir": str(self.allowed_dir),
                    "error": "Path is outside allowed configuration directory"
                }
                logger.warning(
                    "Invalid config path detected",
                    path=str(path),
                    allowed_dir=str(self.allowed_dir)
                )
            
            # Check if file exists (optional - may be creating new config)
            if not path.exists():
                logger.debug(
                    "Config path does not exist (may be new file)",
                    path=str(path)
                )
        
        except Exception as e:
            violations["path_validation_error"] = {
                "error": str(e),
                "path": config_path
            }
            logger.error(
                "Error validating config path",
                error=str(e),
                path=config_path
            )
        
        passed = not violations
        log_policy_evaluation(
            logger,
            policy_name=self.get_name(),
            passed=passed,
            violations=violations
        )
        
        return PolicyResult(passed=passed, violations=violations)
    
    def get_name(self) -> str:
        return "ConfigPathValidationPolicy"
    
    def get_description(self) -> str:
        return f"Ensures configuration files are within {self.allowed_dir}"


class AlphanumericWithPunctuationPolicy(Policy):
    """
    Validates that input contains only alphanumeric characters and standard punctuation.
    """
    
    def __init__(self):
        # Allow alphanumeric, spaces, and common punctuation
        self.allowed_pattern = r'^[a-zA-Z0-9\s\.,!?\-\'\"();:@#$%&*+=\/\[\]{}]+$'
    
    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Validate character set."""
        text = context.user_input or ""
        violations = {}
        
        if text and not re.match(self.allowed_pattern, text):
            # Find invalid characters
            invalid_chars = set()
            for char in text:
                if not re.match(r'[a-zA-Z0-9\s\.,!?\-\'\"();:@#$%&*+=\/\[\]{}]', char):
                    invalid_chars.add(char)
            
            violations["invalid_characters"] = {
                "characters": list(invalid_chars),
                "message": "Input contains invalid characters"
            }
            logger.debug(
                "Invalid characters detected in input",
                invalid_chars=list(invalid_chars)
            )
        
        passed = not violations
        log_policy_evaluation(
            logger,
            policy_name=self.get_name(),
            passed=passed,
            violations=violations
        )
        
        return PolicyResult(passed=passed, violations=violations)
    
    def get_name(self) -> str:
        return "AlphanumericWithPunctuationPolicy"
    
    def get_description(self) -> str:
        return "Ensures input contains only alphanumeric characters and standard punctuation."
