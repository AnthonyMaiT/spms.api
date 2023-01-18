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
    prefix='/event-times',
    tags=['EventTimes']
)

# get all event times from the db
# response model returns a list of event times using model EventTimes from schemas
@router.get('/', response_model=Page[schemas.EventTimes])
# connects to db
# authenticate of user is logged in
def get_event_times(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), event_id: str = '', quarter_range_id: str = ''):
    # return event times to user
    event_times = db.query(models.EventTime)
    # add filters for event and quarter id
    if event_id.isdigit():
        event_times = event_times.filter(models.EventTime.event_id == int(event_id))
    if quarter_range_id.isdigit():
        event_times = event_times.filter(models.EventTime.quarter_range_id == quarter_range_id)
    return paginate(event_times.order_by(desc(models.EventTime.end_time)).all())

# gets the current ongoing events happening at the time
@router.get('/current', response_model=List[schemas.EventTimes])
def get_current_event_times(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    current_time = datetime.now()
    event_times = db.query(models.EventTime).filter(models.EventTime.end_time > current_time, models.EventTime.start_time < current_time).all()
    return event_times

# get a singular quarter range from db
# response would have field from EventTimes
@router.get('/{id}', response_model=schemas.EventTimes)
def get_event_time(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if event time with id exist then return 
    event_time = db.query(models.EventTime).filter(models.EventTime.id == id).first()
    if not event_time:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event Time with id: {id} was not found")
    return event_time

# adds event time to db
# response would be 201 and response would have fields from EventTime
@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.EventTimes)
def create_event_time(event_time: schemas.CreateEventTime,
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if admin or not
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create event time")
    # checks if start date/time is greater than end date
    if event_time.start_time > event_time.end_time:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Start time needs to be less than end time")
    # checks if event time matches to quarter range in db
    quarter_range = db.query(models.Quarter_Range).filter(models.Quarter_Range.start_range < event_time.start_time,
        models.Quarter_Range.end_range > event_time.end_time).first()
    if not quarter_range:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event Time does not fit in Quarter Range")
    # adds event time to db and return created time back to user
    new_event_time = models.EventTime(**{'start_time': event_time.start_time, 'end_time': event_time.end_time, 'event_id': event_time.event_id,
        'quarter_range_id': quarter_range.id})
    db.add(new_event_time)
    db.commit()
    db.refresh(new_event_time)
    return new_event_time

# updates event time in db
# response model is from EventTime
@router.put('/{id}', response_model=schemas.EventTimes)
def update_event_time(id: int, event_time:schemas.CreateEventTime,
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if admin or not
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create event time")
    # checks if the id exists
    update_event_time = db.query(models.EventTime).filter(models.EventTime.id == id)
    if not update_event_time:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event time id: {id} was not found")
    # checks if start date/time is greater than end date
    if event_time.start_time > event_time.end_time:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Start time needs to be less than end time")
    # checks if event time matches to quarter range in db
    quarter_range = db.query(models.Quarter_Range).filter(models.Quarter_Range.start_range < event_time.start_time,
        models.Quarter_Range.end_range > event_time.end_time).first()
    if not quarter_range:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event Time does not fit in Quarter Range")
    # updates and return the event times
    update_event_time.update({"start_time": event_time.start_time, "end_time": event_time.end_time, "event_id": event_time.event_id
        , "quarter_range_id": quarter_range.id}, synchronize_session=False)
    db.commit()
    return update_event_time.first()

# delete an event time
# returns 204 if success
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_event_time(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if admin or not
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create event time")
    # checks if the id exists
    delete_event_time = db.query(models.EventTime).filter(models.EventTime.id == id)
    if not delete_event_time:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event time id: {id} was not found")
    # deletes event time from db
    delete_event_time.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

