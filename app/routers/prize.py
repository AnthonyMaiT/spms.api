from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from .. import models, utils, oauth2
from ..schemas import Prizes as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use router to route methods below
# tags for documentation
router = APIRouter(
    prefix='/prizes',
    tags=['Prizes']
)

# get all prizes from db
# response schema is a list of Prizes
@router.get('/', response_model=Page[schemas.Prize])
# get db session and authenticates user login
def get_prizes(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), name: str = ''):
     # gets all prizes from db with name filter
     prizes = db.query(models.Prize).filter(models.Prize.name.contains(name)).all()
     return paginate(prizes)
    
# gets a singular prize from db
# response schema is Prize
@router.get('/{id}', response_model=schemas.Prize)
def get_prize(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if id not in db. returns error
    prize = db.query(models.Prize).filter(models.Prize.id == id).first()
    if not prize:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prize with id: {id} was not found")
    return prize

# add a new prize to db
@router.post('/', response_model=schemas.Prize, status_code=status.HTTP_201_CREATED)
def create_prize(prize: schemas.CreatePrize,db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # checks if prize name exists in db. return exception if true
    prize_query = db.query(models.Prize).filter(prize.name == models.Prize.name).first()
    if prize_query:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Prize name: {prize.name} already exists")
    # adds prize to db and returns it to user
    new_prize = models.Prize(**prize.dict())
    db.add(new_prize)
    db.commit()
    db.refresh(new_prize)
    return new_prize

# update existing prize in db
@router.put('/{id}', response_model=schemas.Prize)
def update_prize(id:int,prize:schemas.CreatePrize,
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # checks if id not in db. returns error
    prize_query = db.query(models.Prize).filter(models.Prize.id == id)
    if not prize_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prize with id: {id} was not found")
    # checks if prize name exists in db. return exception if true
    prize_name = db.query(models.Prize).filter(prize.name == models.Prize.name)
    check_prize_name = prize_name.first()
    if check_prize_name:
        if check_prize_name.id !=id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Prize name: {prize.name} already exists")
    # updates prize and returns it
    prize_query.update(prize.dict(),synchronize_session=False)
    db.commit()
    return prize_query.first()
    
# delete prize from db. returns 204 
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_prize(id:int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # checks if id exists
    # checks if id not in db. returns error
    prize_query = db.query(models.Prize).filter(models.Prize.id == id)
    if not prize_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prize with id: {id} was not found")
    # deletes prize and returns status code
    prize_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)