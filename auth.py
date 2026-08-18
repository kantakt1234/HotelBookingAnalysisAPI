from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

# credentials
VALID_USERNAME = "admin"
VALID_PASSWORD = "admin"


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    is_valid_username = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        VALID_USERNAME.encode("utf-8")
    )
    is_valid_password = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        VALID_PASSWORD.encode("utf-8")
    )

    if not (is_valid_username and is_valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username