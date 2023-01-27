from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..schemas import Main as schemas
from .. import database, models, utils, oauth2

# app would use this router to route methods
# tags for documentation
router = APIRouter(tags=['Authentication'])

# description for route
login_description = "To authenticate a user's credential for app. Requires username and password of type string and would set http cookie"
# to login a certain user at /login
# response_model would return a Token schema
# passes in description to route
@router.post('/login', response_model=schemas.Token, description=login_description)
# response to set token to cookie
# oauth2 username and password request form
# method would connect to db 
def login(response: Response, user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # checks if username exists in db and returns exception if don't
    user = db.query(models.User).filter(models.User.username == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    # if password from db doesn't match the password entered by user, return error
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    # create a token
    access_token = oauth2.create_access_token(data = {"user_id": user.id, "role_type_id":user.role_type_id})
    # sets token to http cookie
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    # return the access token to user
    return {"access_token": access_token, "token_type": "bearer"}

# removes token from cookie to logout user
logout_description = "Removes token from cookie to logout user"
@router.get('/logout', status_code=status.HTTP_204_NO_CONTENT, description=logout_description)
def logout(response: Response):
    # deletes cookie from response
    response.delete_cookie("access_token")
    return {"response" : "logged out"}

