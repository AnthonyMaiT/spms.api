from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from .. import models, utils, oauth2
from ..schemas import Users as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/users",
    tags=['Users']
)

@router.get('/', response_model=List[schemas.UserOut])
def get_users(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user.role_type_id == 1:
        users = db.query(models.User).all()
        return users
    if current_user.role_type_id == 2:
        users = db.query(models.User).where(models.User.role_type_id == 3).all()
        return users
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view users")

@router.get('/{id}', response_model=schemas.UserOut)
def get_user(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} does not exist")
    if current_user.role_type_id == 2:
        if user.role_type_id != 3:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view user")
    if not current_user.role_type_id == 1 and not current_user.role_type_id == 2 and (
            not current_user.id == user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view user")
    return user


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user.role_type_id == 1:
        findUser = db.query(models.User).filter(models.User.username == user.username).first()
        if findUser:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Username: {user.username} already exists")
        #hash password
        hashed_password = utils.hash(user.password)
        user.password = hashed_password
        new_user = models.User(**user.dict()) 
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create user")

@router.put('/{id}', response_model=schemas.UserOut)
def update_user(id:int , updated_user: schemas.UserUpdate, db: Session = Depends(
        get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user.role_type_id == 1:
        user_query = db.query(models.User).filter(models.User.id == id)
        user = user_query.first()
        if user == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} was not found")

        userdict = updated_user.dict()
        username_query = db.query(models.User).filter(models.User.username==userdict['username']).first()
        if username_query:
            if username_query.id != id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Username: {userdict['username']} already exists")

        if current_user.role_type_id != 1 and user.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to update this user")
        
        userdict["edited_at"] = datetime.now()

        user_query.update(userdict, synchronize_session=False)
        db.commit()
        return user_query.first()
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update users")

@router.put('/change-password/{id}', response_model=schemas.UserOut)
def change_password(id:int, updated_password: schemas.ChangePassword, db: Session = Depends(
        get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user.id == id:
        user_query = db.query(models.User).filter(models.User.id == id)
        user = user_query.first()
        if not utils.verify(updated_password.current_password, user.password):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credential")
        if updated_password.confirm_new_password != updated_password.new_password:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Passwords do not match")

        user_dict = {"password": utils.hash(updated_password.new_password)}
        user_dict["edited_at"] = datetime.now()

        user_query.update(user_dict, synchronize_session=False)
        db.commit()
        return user_query.first()
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update users")


@router.put('/reset-password/{id}', response_model=schemas.UserOut)
def change_password(id:int, updated_password: schemas.ResetPassword, db: Session = Depends(
        get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user.role_type_id == 1:
        user_query = db.query(models.User).filter(models.User.id == id)
        user = user_query.first()
        if user == None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cannot find user with id: {id}")
        if updated_password.confirm_new_password != updated_password.new_password:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Passwords do not match")

        user_dict = {"password": utils.hash(updated_password.new_password)}
        user_dict["edited_at"] = datetime.now()

        user_query.update(user_dict, synchronize_session=False)
        db.commit()
        return user_query.first()
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update users")

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id:int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user.role_type_id == 1:
        user_query = db.query(models.User).filter(models.User.id == id)
        user = user_query.first()
        if user == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} was not found")
        if user.role_type_id == 1:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to delete this user")
        user_query.delete(synchronize_session=False)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete users")
