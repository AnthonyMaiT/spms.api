from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from sqlalchemy import desc
from .. import models, utils, oauth2
from ..schemas import Quarters as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use this router to route methods
# prefix for routes in file
# tags for documentation
router = APIRouter(
    tags=['Quarters']
)

# description of get quarters
get_quarters_description = "Get all of the quarters from database"
# get all quarters from the db session
# routes to /quarters
# response model returns a schema list of Quarter
@router.get('/quarters', response_model=List[schemas.Quarter], description=get_quarters_description)
# connects to db session
# authenticate if user is logged in
def get_quarters(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # return all quarters to user
    quarters = db.query(models.Quarter).all()
    return quarters

# description of get current quarter range
get_current_quarter_range_description = "Get current quarter range from database"
# get current quarter range from the db session
# routes to /quarter-ranges/current
# response model returns a schema of QuarterRangeOut
@router.get('/quarter-ranges/current', response_model=schemas.QuarterRangeOut, description=get_current_quarter_range_description)
# connects to db session
# authenticate if user is logged in
def get_current_quarter_range(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # gets current datetime
    current_time = datetime.now()
    # find current quarter range with current time
    current_quarter_range = db.query(models.Quarter_Range).filter(models.Quarter_Range.end_range > current_time, models.Quarter_Range.start_range < current_time).first()
    # returns exception of no quarter range is set for current time
    if not current_quarter_range:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No quarter range set for today")
    # returns current quarter range
    return current_quarter_range

# description of get quarter ranges
get_quarter_ranges_description = "Get all of the quarter ranges from database"
# get all quarter ranges from the db session
# routes to /quarter-ranges
# response model returns a schema list of QuarterRangeOut that is paginated
@router.get('/quarter-ranges', response_model=Page[schemas.QuarterRangeOut], description=get_quarter_ranges_description)
# connects to db session
# authenticate if user is logged in
def get_quarter_ranges(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # retrieves data from db and returns it back to user
    # order data from start range descending
    quarter_ranges = db.query(models.Quarter_Range).order_by(desc(models.Quarter_Range.start_range)).all()
    # return paginated list of quarter ranges
    return paginate(quarter_ranges)

# description of create quarter range
create_quarter_range_description = "Creates a quarter range which is added to db"
# creates and add quarter range to db
# routes to /quarter-ranges
# response status would be 201
# reponse model returns a schema of QuarterRangeOut
@router.post('/quarter-ranges', status_code=status.HTTP_201_CREATED, response_model=schemas.QuarterRangeOut, description=create_quarter_range_description)
# CreateUpdateQuarterRange schema for user to pass in data to create quarter range
# connects to db session
# authenticate if user is logged in
def create_quarter_range(quarter_range: schemas.CreateUpdateQuarterRange, 
    db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # checks if admin. raise exception if not
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # checks if start date is greater than end date then raise exception if true
    if quarter_range.start_range > quarter_range.end_range:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Start date needs to be less than end date")
    # checks if start/end date is between any range in table and returns exception if true
    test_start_date = db.query(models.Quarter_Range).filter(
        quarter_range.start_range >= models.Quarter_Range.start_range, 
        quarter_range.start_range <= models.Quarter_Range.end_range).first()
    if test_start_date:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Start date conflicts with other quarter ranges")
    test_end_date = db.query(models.Quarter_Range).filter(
        quarter_range.end_range >= models.Quarter_Range.start_range, 
        quarter_range.end_range <= models.Quarter_Range.end_range).first()
    if test_end_date:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="End date conflicts with other quarter ranges")
    # add the quarter_range to db and return the created range back to user
    new_quarter = models.Quarter_Range(**quarter_range.dict())
    db.add(new_quarter)
    db.commit()
    db.refresh(new_quarter)
    return new_quarter

# description of updating quarter range
update_quarter_range_description = "Updates a quarter range in the database"
# updates quarter range in db
# routes to /quarter-ranges/id where id is an id of a certain quarter range
# response model is a schema of QuarterRangeOut
@router.put('/quarter-ranges/{id}', response_model=schemas.QuarterRangeOut, description=update_quarter_range_description)
# id for an id of a certain quarter range
# CreateUpdateQuarterRange schema for user to pass in data to update quarter range
# connects to db session
# authenticate if user is logged in
def update_quarter_range(id: int, quarter_range: schemas.CreateUpdateQuarterRange, 
    db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # checks if not admin. raise exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update quarter range")
    # check if quarter range exists. if false return exception
    quarter_range_query = db.query(models.Quarter_Range).filter(models.Quarter_Range.id == id)
    test_quarter_range = quarter_range_query.first()
    if not test_quarter_range:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quarter Range with id: {id} was not found")
    # checks if start_range is greater than end_range. returns exception if true
    if quarter_range.start_range > quarter_range.end_range:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Start date needs to be less than end date")
    # checks if both start/end dates conflict with other dates in the db
    test_start_date = db.query(models.Quarter_Range).filter(
        quarter_range.start_range >= models.Quarter_Range.start_range, 
        quarter_range.start_range <= models.Quarter_Range.end_range).first()
    if test_start_date and test_start_date.id != id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Start date conflicts with other quarter ranges")
    test_end_date = db.query(models.Quarter_Range).filter(
        quarter_range.end_range >= models.Quarter_Range.start_range, 
        quarter_range.end_range <= models.Quarter_Range.end_range).first()
    if test_end_date and test_end_date.id != id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="End date conflicts with other quarter ranges")
    # updates and return the quarter_range
    quarter_range_query.update(quarter_range.dict(), synchronize_session=False)
    db.commit()
    return quarter_range_query.first()

# description of deleting quarter range
delete_quarter_range_description = "Delete a quarter range from the database"
# deletes a quarter range
# routes to /quarter-ranges/id where id is an id of a certain quarter range
# returns 204 if success
@router.delete('/quarter-ranges/{id}', status_code=status.HTTP_204_NO_CONTENT, description=delete_quarter_range_description)
# id for an id of quarter range
# connects to db session
# authenticate if user is logged in
def delete_quarter_range(id:int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # checks if not admin. returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete quarter range")
    # test if id is in the db. raise exception if not
    quarter_range_query = db.query(models.Quarter_Range).filter(models.Quarter_Range.id == id)
    if not quarter_range_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quarter Range with id: {id} was not found")
    # deletes quarter-range and returns 204 when completed
    quarter_range_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)