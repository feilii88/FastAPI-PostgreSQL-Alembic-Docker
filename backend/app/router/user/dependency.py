from typing import Annotated
from fastapi import HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer

from app.util.auth import AuthUtil

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")
# Depends(oauth2_scheme)
async def get_current_user(token: str = Annotated[str, Header()]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return AuthUtil.verify_token(token, credentials_exception)