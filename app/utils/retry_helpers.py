# Use shared_architecture retry policies instead of custom implementation
from shared_architecture.resilience.retry_policies import (
    RetryPolicy, RetryConfig, BackoffStrategy,
    retry_with_exponential_backoff, retry_with_linear_backoff,
    get_retry_policy, retry
)

# Export commonly used retry decorators for backward compatibility
__all__ = [
    "retry_with_exponential_backoff",
    "retry_with_linear_backoff", 
    "retry",
    "get_retry_policy"
]

# For backward compatibility, keep the old function signature
def retry_with_backoff(fn, retries=3, backoff_in_seconds=2):
    """
    Retry a function call with exponential backoff.
    DEPRECATED: Use shared_architecture retry policies instead.
    """
    from shared_architecture.utils.logging_utils import log_info
    log_info("Using deprecated retry_with_backoff, consider upgrading to shared retry policies")
    
    # Use the new retry system
    config = RetryConfig(
        name="legacy_backoff",
        max_attempts=retries,
        base_delay=backoff_in_seconds,
        backoff_strategy=BackoffStrategy.EXPONENTIAL
    )
    policy = RetryPolicy(config)
    return policy.execute(fn)