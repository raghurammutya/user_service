import time

def retry_operation(fn, retries=3, backoff_in_seconds=2):
    """
    Utility for retrying an operation in case of transient failures.
    """
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(backoff_in_seconds * (2 ** attempt))
            else:
                raise e