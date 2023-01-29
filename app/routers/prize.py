from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from .. import models, utils, oauth2
from ..schemas import Prizes as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use this router to route methods
# prefix for routes in file
# tags for documentation
router = APIRouter(
    prefix='/prizes',
    tags=['Prizes']
)

# description of get prizes
get_prizes_description = "Get all of the prizes from database"
# get all prizes from the db session
# routes to /prizes
# response model returns a schema list of Prizes that is paginated
@router.get('/', response_model=Page[schemas.Prize], description=get_prizes_description)
# connects to db
# authenticate if user is logged in
# filters for prizes
def get_prizes(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user), name: str = ''):
    # gets all prizes in db with added filter
     prizes = db.query(models.Prize).filter(models.Prize.name.contains(name)).all()
     # returns a paginated list of prizes
     return paginate(prizes)

# description of create prize
create_prize_description = "Creates a prize which is added to db"
# creates and add prize to db
# routes to /prizes
# response status would be 201
# reponse model returns a schema of Prizes
@router.post('/', response_model=schemas.Prize, status_code=status.HTTP_201_CREATED, description=create_prize_description)
# CreateUpdatePrize schema for user to pass in data to create prize
# connects to db session
# authenticate if user is logged in
def create_prize(prize: schemas.CreateUpdatePrize,db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # returns exception if user isn't an admin
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # checks if prize name exists in db. return exception if true
    prize_query = db.query(models.Prize).filter(prize.name == models.Prize.name).first()
    if prize_query:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Prize name: {prize.name} already exists")
    # adds prize to db and returns prize to user
    new_prize = models.Prize(**prize.dict())
    db.add(new_prize)
    db.commit()
    db.refresh(new_prize)
    return new_prize

# description of updating prize
update_prize_description = "Updates an prize time in the database"
# updates prize in db
# routes to /prizes/id where id is an id of a certain prize
# response model is a schema of Prize
@router.put('/{id}', response_model=schemas.Prize, description=update_prize_description)
# id for an id of a certain prize
# CreateUpdatePrize schema for user to pass in data to update prize
# connects to db session
# authenticate if user is logged in
def update_prize(id:int,prize:schemas.CreateUpdatePrize,
    db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # checks if id not in db. returns error if true
    prize_query = db.query(models.Prize).filter(models.Prize.id == id)
    if not prize_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prize with id: {id} was not found")
    # checks if prize name exists in db. return exception if true
    prize_name = db.query(models.Prize).filter(prize.name == models.Prize.name)
    check_prize_name = prize_name.first()
    if check_prize_name:
        if check_prize_name.id !=id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Prize name: {prize.name} already exists")
    # updates prize and returns prize to user
    prize_query.update(prize.dict(),synchronize_session=False)
    db.commit()
    return prize_query.first()
    
# description of deleting prize time
delete_prize_description = "Delete a prize from the database"
# deletes an prize time
# routes to /prizes/id where id is an id of a certain prize
# returns 204 if success
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT, description=delete_prize_description)
# id for an id of prize
# connects to db session
# authenticate if user is logged in
def delete_prize(id:int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # checks if id not in db. returns error if true
    prize_query = db.query(models.Prize).filter(models.Prize.id == id)
    if not prize_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prize with id: {id} was not found")
    # deletes prize and returns status code
    prize_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)