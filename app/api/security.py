import os
import logging
from fastapi import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

logger = logging.getLogger(__name__)


def get_api_key_secret() -> str:
    """
    Retrieve the API key secret from the environment. A default value is provided for development purposes.
    
    Returns:
        str: The API key secret.
    """
    return os.getenv("API_KEY_SECRET", "default-secret")


def validate_api_key(api_key: str) -> bool:
    """
    Validate the provided API key against the secret stored in the environment.
    
    Args:
        api_key (str): The API key provided in the request header.
        
    Returns:
        bool: True if the API key matches the secret; otherwise, False.
    """
    secret_key = get_api_key_secret()
    if not secret_key:
        logger.error("API_KEY_SECRET is not configured in the environment.")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="API key configuration error")

    return api_key == secret_key


def require_api_key(api_key: str) -> None:
    """
    Ensure that the provided API key is present and valid.
    Raises an HTTPException if validation fails.
    
    Args:
        api_key (str): The API key provided in the request header.
        
    Raises:
        HTTPException: If the API key is missing or invalid.
    """
    if not api_key:
        logger.warning("Missing API key in request")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing API key")
    if not validate_api_key(api_key):
        logger.warning("Invalid API key provided")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid API key")
