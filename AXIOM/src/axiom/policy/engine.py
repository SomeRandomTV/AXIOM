"""Policy evaluation engine."""

import logging
from typing import Dict, Any, Optional
from typing import List
import json
from datetime import datetime

from .policies import Policy, PolicyContext, PolicyResult

logger = logging.getLogger(__name__)

class PolicyEngine:
    """
    Evaluates registered policies for input and response guardrails.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None, audit_log_path: Optional[str] = None):
        self._policies: List[Policy] = []
        self.config = config or {}
        self.audit_log_path = audit_log_path
        self._audit_log_enabled = bool(audit_log_path)
    def set_config(self, config: Dict[str, Any]) -> None:
        """Update policy engine configuration."""
        self.config = config

    def enable_audit_logging(self, path: str) -> None:
        """Enable audit logging to the specified file path."""
        self.audit_log_path = path
        self._audit_log_enabled = True

    def audit_log(self, entry: Dict[str, Any]) -> None:
        """Write an audit log entry if enabled."""
        if not self._audit_log_enabled or not self.audit_log_path:
            return
        entry['timestamp'] = datetime.now().isoformat()
        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to write audit log: {e}")
    
    def add_policy(self, policy: Policy) -> None:
        self._policies.append(policy)
        logger.debug(f"Policy registered: {policy.get_name()}")
    
    def evaluate_response(self, response: str) -> PolicyResult:
        context = PolicyContext(response=response)
        return self._evaluate(context)
    
    def evaluate_input(self, user_input: str) -> PolicyResult:
        context = PolicyContext(user_input=user_input)
        return self._evaluate(context)
    
    def _evaluate(self, context: PolicyContext) -> PolicyResult:
        violations = {}
        for policy in self._policies:
            result = policy.evaluate(context)
            if not result.passed:
                violations[policy.get_name()] = result.violations
        policy_result = PolicyResult(passed=(not violations), violations=violations)
        # Audit log the evaluation
        self.audit_log({
            "context": context.__dict__,
            "result": policy_result.__dict__,
            "policies": [p.get_name() for p in self._policies]
        })
        return policy_result