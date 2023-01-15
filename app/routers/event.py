from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from sqlalchemy import desc
from .. import models, utils, oauth2
from ..schemas import Events as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use router to route methods below
# tags for documentation
router = APIRouter(
    prefix='/events',
    tags=['Events']
)

# get all events from the db
# response schema is from Events
@router.get('/', response_model=Page[schemas.Events])
# gets db session and authenticate user is logged in
def get_events(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), nameFilter: str = ''):
    # gets all events in db
    events = db.query(models.Events).filter(models.Events.name.contains(nameFilter)).order_by(
        desc(models.Events.id)).all()
    return paginate(events)

# get singular event from db with id
# response schema is from Events
@router.get('/{id}', response_model=schemas.Events)
def get_event(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # gets/return an event with id. returns exception if not exist. 
    event = db.query(models.Events).filter(models.Events.id == id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with id: {id} was not found")
    return event

# creates an event
# response schema is from Events
@router.post('/',status_code=status.HTTP_201_CREATED, response_model=schemas.Events)
# requires user to put in data like the Create Events schema
def create_event(event: schemas.CreateEvent, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # makes sure event name doesn't match any other event
    events_query = db.query(models.Events).filter(models.Events.name == event.name)
    if events_query.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Event name: {event.name} already exists")
    # creates event in db and returns it to user
    new_event = models.Events(**event.dict())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

# updates an event
# response schema is from Events
@router.put('/{id}', response_model=schemas.Events)
def update_event(id: int, event:schemas.CreateEvent,
     db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin and return exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # checks if event with id exist
    event_query = db.query(models.Events).filter(models.Events.id == id)
    if not event_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with id: {id} was not found")
    # cehcks if event with same name exist in db. returns exception if true
    test_event_name = db.query(models.Events).filter(models.Events.name == event.name).first()
    if test_event_name:
        if test_event_name.id != id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Event name: {event.name} already exists")
    # updates db and returns event
    event_query.update(event.dict(),synchronize_session=False)
    db.commit()
    return event_query.first()

# delete event from db. returns status 204
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_event(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin and returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete events")
    # checks if event with id exist. returns exception if it doesnt
    event_query = db.query(models.Events).filter(models.Events.id == id)
    if not event_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with id: {id} was not found")
    # deletes event and returns status code
    event_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    