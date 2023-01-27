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
    prefix='/event-times',
    tags=['EventTimes']
)

# description of get event times
get_event_times_description = "Get all of the event times from database"
# get all event times from the db session
# routes to /event-times
# response model returns a schema list of EventTimes that is paginated
@router.get('/', response_model=Page[schemas.EventTime], description=get_event_times_description)
# connects to db
# authenticate if user is logged in
# filters for event times
def get_event_times(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user), event_id: str = '', quarter_range_id: str = ''):
    # create event time query for output
    event_times = db.query(models.EventTime)
    # add filters for event and quarter id
    if event_id.isdigit():
        event_times = event_times.filter(models.EventTime.event_id == int(event_id))
    if quarter_range_id.isdigit():
        event_times = event_times.filter(models.EventTime.quarter_range_id == quarter_range_id)
    # return a paginated list of event times ordered by descending based off end time
    return paginate(event_times.order_by(desc(models.EventTime.end_time)).all())

# description of get event times
get_current_event_time_description = "Get all event times that are ongoing of current date from database"
# gets the current ongoing events happening at the time
# routes to /event-times/current
# response model returns a schema list of EventTimes
@router.get('/current', response_model=List[schemas.EventTime], description=get_current_event_time_description)
# connects to db session
# authenticate if user is logged in
def get_current_event_times(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # gets current datetime
    current_time = datetime.now()
    # gets event times based on current time and return to user
    event_times = db.query(models.EventTime).filter(models.EventTime.end_time > current_time, models.EventTime.start_time < current_time).all()
    return event_times

# description of create event times
create_event_time_description = "Creates an event time which is added to db"
# creates and add event time to db
# routes to /event-times
# response status would be 201
# reponse model returns a schema of Event Times
@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.EventTime, description=create_event_time_description)
# CreateUpdateEventTime schema for user to pass in data to create event time
# connects to db session
# authenticate if user is logged in
def create_event_time(event_time: schemas.CreateUpdateEventTime,
    db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # returns exception if user isn't an admin
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create event time")
    # checks if start date/time is greater than end date returns exception if so
    if event_time.start_time > event_time.end_time:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Start time needs to be less than end time")
    # checks if event time matches to a quarter range in db returns exception if not
    quarter_range = db.query(models.Quarter_Range).filter(models.Quarter_Range.start_range < event_time.start_time,
        models.Quarter_Range.end_range > event_time.end_time).first()
    if not quarter_range:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event Time does not fit in Quarter Range")
    # adds event time to db and return event time back to user
    new_event_time = models.EventTime(**{'start_time': event_time.start_time, 'end_time': event_time.end_time, 'event_id': event_time.event_id,
        'quarter_range_id': quarter_range.id})
    db.add(new_event_time)
    db.commit()
    db.refresh(new_event_time)
    return new_event_time

# description of updating event times
update_event_time_description = "Updates an event time in the database"
# updates event time in db
# routes to /event-times/id where id is an id of a certain event time
# response model is a schema of EventTime
@router.put('/{id}', response_model=schemas.EventTime, description=update_event_time_description)
# id for an id of a certain event time
# CreateUpdateEventTime schema for user to pass in data to update event time
# connects to db session
# authenticate if user is logged in
def update_event_time(id: int, event_time:schemas.CreateUpdateEventTime,
    db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # returns exception if user isn't an admin
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create event time")
    # checks if the id exists in db and return exception if not
    updated_event_time = db.query(models.EventTime).filter(models.EventTime.id == id)
    if not update_event_time:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event time id: {id} was not found")
    # checks if start date/time is greater than end date  and return exception if so
    if event_time.start_time > event_time.end_time:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Start time needs to be less than end time")
    # checks if event time matches to quarter range in db and returns exception if not
    quarter_range = db.query(models.Quarter_Range).filter(models.Quarter_Range.start_range < event_time.start_time,
        models.Quarter_Range.end_range > event_time.end_time).first()
    if not quarter_range:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event Time does not fit in Quarter Range")
    # updates and return the event time
    updated_event_time.update({"start_time": event_time.start_time, "end_time": event_time.end_time, "event_id": event_time.event_id
        , "quarter_range_id": quarter_range.id}, synchronize_session=False)
    db.commit()
    return updated_event_time.first()

# description of deleting event time
delete_event_time_description = "Delete an event time from the database"
# deletes an event time
# routes to /event-times/id where id is an id of a certain event time
# returns 204 if success
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT, description=delete_event_time_description)
# id for an id of event time
# connects to db session
# authenticate if user is logged in
def delete_event_time(id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # returns exception if user isn't an admin
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create event time")
    # checks if the id exists in db and return exception if not
    delete_event_time = db.query(models.EventTime).filter(models.EventTime.id == id)
    if not delete_event_time:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event time id: {id} was not found")
    # deletes event time from db and returns status
    delete_event_time.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

