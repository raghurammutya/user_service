import requests
import logging
from circuitbreaker import circuit
import traceback

class ApiHandler:
    def __init__(self, config, session=None):
        self.config = config
        self.session = session

    @circuit(failure_threshold=3, recovery_timeout=30)
    def execute(self, service_instance, api_function, pre_hook=None, post_hook=None, **kwargs):
        try:
            # Execute pre-hook if provided
            if pre_hook:
                pre_hook()

            # Service instance-based API call
            if service_instance:
                return self._handle_service_call(service_instance, api_function, **kwargs)

            # HTTP API call
            return self._handle_http_call(api_function, **kwargs)

        except Exception as e:
            logging.error(f"API execution failed: {e}")
            traceback.print_exc()
            raise
        finally:
            if post_hook:
                post_hook()

    def _handle_service_call(self, service_instance, api_function, **kwargs):
        try:
            logging.info(f"Calling service API: {api_function} with params: {kwargs}")
            response = getattr(service_instance, api_function)(**kwargs)
            return response
        except Exception as e:
            logging.error(f"Service API call failed: {e}")
            raise

    def _handle_http_call(self, api_function, **kwargs):
        headers = {"Content-Type": "application/json"}
        payload = {"action": api_function, "data": kwargs}

        try:
            logging.info(f"Making HTTP POST request with payload: {payload}")
            response = requests.post(self.config.get("url_with_port"), headers=headers, json=payload)
            response.raise_for_status()  # Raise for HTTP errors

            if response.headers.get("Content-Type") == "application/json":
                return response.json()

            return response.text

        except requests.RequestException as e:
            logging.error(f"HTTP API call failed: {e}")
            raise