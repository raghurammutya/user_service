import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
def get_common_config() -> dict:
    """
    Fetch common configuration from environment variables.
    """
    try:
        common_config_keys = [
            "DATABASE_HOST", "DATABASE_PORT", 
            "LOGGING_LEVEL", "WORKING_DIRECTORY", 
            "POSTGRES_HOST", "POSTGRES_PORT"
        ]
        common_config = {key: os.getenv(key) for key in common_config_keys if os.getenv(key)}
        logging.info(f"Common Config Retrieved: {common_config}")
        return common_config
    except Exception as e:
        logging.error(f"Error fetching common config: {e}")
        return {}