import logging
from shared_architecture.utils.logging_helper import configure_logging

def setup_logging():
    """
    Configures the logging format, levels, and other behavior for the app.
    """
    configure_logging()
    logger = logging.getLogger("user_service")
    logger.setLevel(logging.INFO)
    return logger