from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from sqlalchemy import desc
from .. import models, utils, oauth2
from ..schemas import Events as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use this router to route methods
# prefix for routes in file
# tags for documentation
router = APIRouter(
    prefix='/events',
    tags=['Events']
)

# description of get events
get_events_description = "Get all of the events from database"
# get all events from the db session
# routes to /events
# response model returns a schema list of Events that is paginated
@router.get('/', response_model=Page[schemas.Event], description=get_events_description)
# connects to db session
# authenticate if user is logged in
# filters for events
def get_events(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user), nameFilter: str = ''):
    # gets all events in db with added filter and ordering id descending
    events = db.query(models.Events).filter(models.Events.name.contains(nameFilter)).order_by(
        desc(models.Events.id)).all()
    # return a paginated list of events
    return paginate(events)

# description of create event
create_event_description = "Creates an event which is added to db"
# creates and add event to db
# routes to /events
# response status would be 201
# reponse model returns a schema of Events
@router.post('/',status_code=status.HTTP_201_CREATED, response_model=schemas.Event, description=create_event_description)
# CreateUpdateEvent schema for user to pass in data to create event time
# connects to db session
# authenticate if user is logged in
def create_event(event: schemas.CreateUpdateEvent, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # returns exception if user isn't an admin
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # returns exception if event name matches with any other event name
    events_query = db.query(models.Events).filter(models.Events.name == event.name)
    if events_query.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Event name: {event.name} already exists")
    # adds event to db and return event back to user
    new_event = models.Events(**event.dict())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

# description of updating event
update_event_description = "Updates an event in the database"
# updates event in db
# routes to /events/id where id is an id of a certain event
# response model is a schema of Event
@router.put('/{id}', response_model=schemas.Event, description=update_event_description)
# id for an id of a certain event
# CreateUpdateEvent schema for user to pass in data to update event
# connects to db session
# authenticate if user is logged in
def update_event(id: int, event:schemas.CreateUpdateEvent,
     db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # returns exception if user isn't an admin
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # checks if the id exists in db and return exception if not
    event_query = db.query(models.Events).filter(models.Events.id == id)
    if not event_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with id: {id} was not found")
    # checks if event with same name exist in db. returns exception if true
    test_event_name = db.query(models.Events).filter(models.Events.name == event.name).first()
    if test_event_name:
        if test_event_name.id != id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Event name: {event.name} already exists")
    # updates event in db and returns event
    event_query.update(event.dict(),synchronize_session=False)
    db.commit()
    return event_query.first()

# description of deleting event
delete_event_description = "Delete an event from the database"
# deletes an event
# routes to /events/id where id is an id of a certain event
# returns 204 if success
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT, description=delete_event_description)
# id for an id of event
# connects to db session
# authenticate if user is logged in
def delete_event(id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # returns exception if user isn't an admin
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete events")
    # checks if the id exists in db and return exception if not
    event_query = db.query(models.Events).filter(models.Events.id == id)
    if not event_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with id: {id} was not found")
    # deletes event from db and returns status code
    event_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    