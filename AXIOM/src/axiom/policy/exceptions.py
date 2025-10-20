"""Policy-related exceptions for AXIOM."""


class PolicyValidationError(Exception):
    """
    Exception raised when policy validation fails.
    
    This exception is raised when a policy check fails during input
    or response validation, indicating that the content violates
    one or more configured policies.
    """
    
    def __init__(self, message: str, policy_name: str = None, violations: list = None):
        """
        Initialize PolicyValidationError.
        
        Args:
            message: Error message describing the validation failure
            policy_name: Name of the policy that failed (optional)
            violations: List of specific violations found (optional)
        """
        super().__init__(message)
        self.policy_name = policy_name
        self.violations = violations or []
        
    def __str__(self):
        if self.policy_name:
            return f"Policy '{self.policy_name}' validation failed: {super().__str__()}"
        return super().__str__()


class PolicyEngineError(Exception):
    """
    Exception raised for general policy engine errors.
    
    This exception is raised when there are issues with the policy
    engine itself, such as configuration errors or policy registration
    failures.
    """
    pass


class PolicyNotFoundError(PolicyEngineError):
    """
    Exception raised when a requested policy is not found.
    
    This exception is raised when trying to access or remove a policy
    that has not been registered with the policy engine.
    """
    pass


class PolicyRegistrationError(PolicyEngineError):
    """
    Exception raised when policy registration fails.
    
    This exception is raised when there are issues registering a new
    policy with the policy engine, such as duplicate policy names or
    invalid policy implementations.
    """
    pass
