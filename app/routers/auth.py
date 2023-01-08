from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..schemas import Main as schemas
from .. import database, models, utils, oauth2

# app would use this router to route methods
# tags for documentation
router = APIRouter(tags=['Authentication'])

# to login a certain user at /login
# response_model would return Token and type of token
@router.post('/login', response_model=schemas.Token)
# oauth2 password  request form returns username and password and have to use form-data in postman
# method would connect to db 
# response to set data to cookie
def login(response: Response, user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # gets user from db using username
    user = db.query(models.User).filter(models.User.username == user_credentials.username).first()
    # if username doesn't exist, return error
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    # if password from db doesn't match the password entered by user, return error
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    # create a token
    # return token to user
    access_token = oauth2.create_access_token(data = {"user_id": user.id, "role_type_id":user.role_type_id})
    # sets data to cookie
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return {"access_token": access_token, "token_type": "bearer"}

# removes token from cookie to logout user
@router.get('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"response" : "logged out"}

