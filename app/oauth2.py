from jose import ExpiredSignatureError, JWTError, jwt
from datetime import datetime, timedelta

from pydantic import ValidationError

from .schemas import Main as schemas
from . import database, models, main
from fastapi import Depends, Request, status, HTTPException
from sqlalchemy.orm import Session
from .config import settings
from starlette.responses import RedirectResponse
from fastapi.security.utils import get_authorization_scheme_param

from typing import Dict
from typing import Optional

from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2

# like the oauth2passwordbearer class but only accepts cookie data from user
class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.cookies.get(
            "access_token"
        )  # changed to accept access token from httpOnly Cookie
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param

# place to get token is at /login
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl='login')

# Secret key that is used to generate a jwt token for authorization of users
#32 bit hexadecmial
SECRET_KEY = settings.secret_key
# Algorithm for generating jwt token
ALGORITHM = settings.algorithm
# expiration date of the token
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# creates token for user with user data inside of the token
def create_access_token(data: dict):
    to_encode = data.copy()
    # Adds expiration time to the token
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # creates token and return 
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# verifies there is a valid token and not expired
def verify_access_token(token: str, credentials_exception):
    try:
        # decods token to get data
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # data from the token
        id: str = payload.get("user_id")
        # verifies there is an id
        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id)
    # would run if error/expired
    except (JWTError):
        raise credentials_exception
    return token_data

# returns current user from token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    # exception to be used for verification
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                detail=f'Could not validate credentials', 
                                headers={"WWW-Authenticate": "Bearer"})
    # verifies the token
    token = verify_access_token(token, credentials_exception)
    # gets User object from the user_id inside token and returns it
    user = db.query(models.User).filter(models.User.id == token.id).first()
    return user