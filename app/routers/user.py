from datetime import datetime
from operator import or_
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from sqlalchemy import func, text
from .. import models, utils, oauth2
from ..schemas import Users as schemas
from ..schemas import Main as schema
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use router for methods
# prefix /users to all methods below
# tags for documentation
router = APIRouter(
    prefix="/users",
    tags=['Users']
)

# get all users from the db
# response_model returns a list of Users using model UserOut from schemas with Paged data
# Paged data includes total, page number, and page size
@router.get('/', response_model=Page[schemas.UserOut])
# connects to db
# Authenticates user to see if login (would return 401 if no user)
# http parameters in order to filter and sort data
def get_users(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user),
    usernameFilter: str = '', firstNameFilter: str='',lastNameFilter: str='',
        gradeFilter: int = None, roleTypeIdFilter: int = None, sortColumn: str = 'id', sortDir: str = 'desc'):
    # checks if current user is Admin
    # returns users based on filters and page
    if current_user.role_type_id == 1:
        users_query = db.query(models.User).filter(
            models.User.username.contains(usernameFilter), models.User.first_name.contains(
                firstNameFilter), models.User.last_name.contains(lastNameFilter))
        # as gradeFilter/roletype is an int, would need to pass it in if statement
        if gradeFilter != None:
            users_query = users_query.filter(models.User.grade == gradeFilter)
        if roleTypeIdFilter != None:
            users_query = users_query.filter(models.User.role_type_id == roleTypeIdFilter)
        # sorts by column name and direction
        users = users_query.order_by(text(sortColumn + ' ' + sortDir)).all()
        return paginate(users)
    # returns error if no roles/ is student / is staff
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view users")

# get all users from the db
# response_model returns a list of Users using model RoleType from schemas
@router.get('/role-types', response_model=List[schema.RoleType])
# connects to db
# Authenticates user to see if login (would return 401 if no user)
def get_role_types(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if current user is Admin and would return all role types if so
    if current_user.role_type_id == 1:
        role_types = db.query(models.RoleType).all()
        return role_types
    # returns error if no roles/ is student
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view users")

# would return the current user to frontend and checks to see if logged in
@router.get('/current', response_model=schemas.UserOut)
def get_current_user(current_user: int = Depends(oauth2.get_current_user)):
    return current_user

# checks if user is admin for client side
@router.get('/isadmin', response_model=bool)
def is_admin(current_user: int = Depends(oauth2.get_current_user)):
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an admin")
    return True

# checks if user is admin/staff for client side
@router.get('/isstaff', response_model=bool)
def is_admin(current_user: int = Depends(oauth2.get_current_user)):
    if current_user.role_type_id == 1 or current_user.role_type_id == 2:
        return True
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an admin/staff")

# gets a certain user with id
@router.get('/{id}', response_model=schemas.UserOut)
def get_user(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # gets the first user with the id from url
    user = db.query(models.User).filter(models.User.id == id).first()
    # checks if the user with id exist
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} does not exist")
    # would return error if person isn't admin
    if not current_user.role_type_id == 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view user")
    # returns user data
    return user

# status code 201 when successfully creating a user
@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
# user can only put in fields from UserCreate schema
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if admin role in current user
    if current_user.role_type_id == 1:
        # checks if username exist. returns error if it already does exist
        findUser = db.query(models.User).filter(models.User.username == user.username).first()
        if findUser:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Username: {user.username} already exists")
        #hash password and add to UserCreate Model
        hashed_password = utils.hash(user.password)
        user.password = hashed_password
        new_user = models.User(**user.dict()) 
        # adds to db and returns created user.
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    # returns error if not admin
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create user")


# when user changes OWN password
@router.put('/change-password', response_model=schemas.UserOut)
# uses ChangePassword schema 
def change_password(updated_password: schemas.ChangePassword, db: Session = Depends(
        get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if the current_password matches does not match with the password in db. would return error
    if not utils.verify(updated_password.current_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credential")
    # checks if updated_password does not match confirmed password. would return error
    if updated_password.confirm_new_password != updated_password.new_password:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Passwords do not match")

    # adds new password to dict and updates edited time
    user_dict = {"password": utils.hash(updated_password.new_password)}
    user_dict["edited_at"] = datetime.now()

    # query user, updates password and returns user
    user_query = db.query(models.User).filter(models.User.id == current_user.id)
    user_query.update(user_dict, synchronize_session=False)
    db.commit()
    return user_query.first()

# updates user
@router.put('/{id}', response_model=schemas.UserOut)
# user can only use fields defined by UserUpdate schema
def update_user(id:int , updated_user: schemas.UserUpdate, db: Session = Depends(
        get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if admin
    if current_user.role_type_id == 1:
        # gets user if exist. return error if doesn't
        user_query = db.query(models.User).filter(models.User.id == id)
        user = user_query.first()
        if user == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} was not found")
        # checks if changed username already exist. returns error if it does
        userdict = updated_user.dict()
        username_query = db.query(models.User).filter(models.User.username==userdict['username']).first()
        if username_query:
            if username_query.id != id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Username: {userdict['username']} already exists")
        # adds edited_at to db
        userdict["edited_at"] = datetime.now()
        # update user to db and returns updated user.
        user_query.update(userdict, synchronize_session=False)
        db.commit()
        return user_query.first()
    # returns exception if user is not admin
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update users")

# reset password of any user
@router.put('/reset-password/{id}', response_model=schemas.UserOut)
def reset_password(id:int, updated_password: schemas.ResetPassword, db: Session = Depends(
        get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if admin
    if current_user.role_type_id == 1:
        # get user with id and if exist. returns error if doesn't
        user_query = db.query(models.User).filter(models.User.id == id)
        user = user_query.first()
        if user == None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cannot find user with id: {id}")
        # checks if passwords match
        if updated_password.confirm_new_password != updated_password.new_password:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Passwords do not match")
        # adds password and edited_at to dictionary
        user_dict = {"password": utils.hash(updated_password.new_password)}
        user_dict["edited_at"] = datetime.now()
        # updates user password to db and returns user
        user_query.update(user_dict, synchronize_session=False)
        db.commit()
        return user_query.first()
    # returns error if not admin
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update users")

# delete a certain user. returns code 204 when completed
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id:int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if admin
    if current_user.role_type_id == 1:
        # get user from db with user. if doesn't exit return error
        user_query = db.query(models.User).filter(models.User.id == id)
        user = user_query.first()
        if user == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} was not found")
        # cannot delete self
        if current_user.id == user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to delete this user")
        # delete user in db then returns response
        user_query.delete(synchronize_session=False)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    # returns error if not admin
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete users")
