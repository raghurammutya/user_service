import os
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
def get_scoped_config(configmap_name: str) -> dict:
    """
    Fetch service-specific scoped configuration from environment variables.
    """
    try:
        scoped_config_data = os.getenv(configmap_name, "{}")
        scoped_config = json.loads(scoped_config_data)
        logging.info(f"Scoped Config Retrieved for {configmap_name}: {scoped_config}")
        return scoped_config
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding scoped ConfigMap data for {configmap_name}: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error fetching scoped configuration: {e}")
        return {}