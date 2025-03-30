import logging

def configure_logging():
    """
    Configures logging behavior for the microservice.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    return logging.getLogger("shared_logger")