import secrets
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv, find_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Explicitly load the .env file from the app directory
dotenv_path = find_dotenv(filename="app/.env", usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path)
    logger.info(f"Loaded .env file from: {dotenv_path}")
    # Debug: Log what credentials are loaded (remove this in production)
    loaded_username = os.getenv("BASIC_AUTH_USERNAME")
    loaded_password = os.getenv("BASIC_AUTH_PASSWORD")
    logger.info(f"DEBUG - Loaded BASIC_AUTH_USERNAME: '{loaded_username}'")
    logger.info(f"DEBUG - Loaded BASIC_AUTH_PASSWORD: '{loaded_password}'")
else:
    logger.warning("WARNING: .env file not found or not loaded correctly.")

security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    username = os.getenv("BASIC_AUTH_USERNAME")
    password = os.getenv("BASIC_AUTH_PASSWORD")

    # Debug logging (remove in production)
    logger.info(f"DEBUG - Auth attempt - Provided username: '{credentials.username}'")
    logger.info(f"DEBUG - Auth attempt - Expected username: '{username}'")
    logger.info(f"DEBUG - Auth attempt - Provided password: '{credentials.password}'")
    logger.info(f"DEBUG - Auth attempt - Expected password: '{password}'")

    if not (username and password):
        logger.error("BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD environment variables not set!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error: BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD environment variables not set.",
        )

    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)

    logger.info(f"DEBUG - Username match: {correct_username}")
    logger.info(f"DEBUG - Password match: {correct_password}")

    if not (correct_username and correct_password):
        logger.warning(f"Auth failed for user: '{credentials.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    logger.info(f"Auth successful for user: '{credentials.username}'")
    return credentials.username
