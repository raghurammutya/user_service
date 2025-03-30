import time
from shared_architecture.utils.retry_helpers import retry_operation

def retry_with_backoff(fn, retries=3, backoff_in_seconds=2):
    """
    Retry a function call with exponential backoff.
    """
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(backoff_in_seconds * (2 ** attempt))
            else:
                raise e