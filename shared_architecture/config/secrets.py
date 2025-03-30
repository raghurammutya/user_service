import os
import base64
import logging
import json
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
def decode_secret(encoded_value: str) -> str:
    """
    Decode a base64-encoded secret.
    """
    try:
        return base64.b64decode(encoded_value).decode("utf-8")
    except Exception as e:
        logging.error(f"Error decoding secret: {e}")
        return ""

def get_secure_config(secret_name: str, key: str) -> str:
    """
    Fetch secure configuration for a specific key from Secrets.
    """
    try:
        secret_data = os.getenv(secret_name, "{}")
        secrets = json.loads(secret_data)
        encoded_value = secrets.get(key)
        if encoded_value:
            return decode_secret(encoded_value)
        else:
            raise ValueError(f"Key {key} not found in Secrets.")
    except Exception as e:
        logging.error(f"Error fetching secure config for {key}: {e}")
        return ""