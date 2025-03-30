import requests
from app.core.config import AppConfig

def get_keycloak_token(username: str, password: str):
    """
    Authenticate with Keycloak and retrieve an access token.
    """
    url = f"{AppConfig.keycloak_url}/realms/{AppConfig.keycloak_realm}/protocol/openid-connect/token"
    data = {
        "client_id": AppConfig.keycloak_client_id,
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        raise ValueError(f"Keycloak Authentication Failed: {response.text}")
    return response.json()["access_token"]