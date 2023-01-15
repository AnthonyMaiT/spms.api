from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from sqlalchemy import desc
from .. import models, utils, oauth2
from ..schemas import Quarters as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use router to route methods below
# tags for documentation
router = APIRouter(
    tags=['Quarters']
)

# get all quarters from the db
# response_model returns a list of quarters using model Quarter from schemas
@router.get('/quarters', response_model=List[schemas.Quarter])
# connects to db
# Authenticates user to see if login (would return 401 if no user)
def get_quarters(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # return quarters to user
    quarters = db.query(models.Quarter).all()
    return quarters

# get the quarter ranges from db
# response would have fields from QuarterRangeOut
@router.get('/quarter-ranges', response_model=Page[schemas.QuarterRangeOut])
def get_quarter_ranges(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # retrieves data from db and returns it back to user
    quarter_ranges = db.query(models.Quarter_Range).order_by(desc(models.Quarter_Range.start_range)).all()
    return paginate(quarter_ranges)

# get a singular quarter range from db
# response would have fields from QuarterRangeOut
@router.get('/quarter-ranges/{id}', response_model=schemas.QuarterRangeOut)
def get_quarter_ranges(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if quarter_range exist and returns exception if doesn't. returns quarter_range if it does
    quarter_range = db.query(models.Quarter_Range).filter(models.Quarter_Range.id == id).first()
    if not quarter_range:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quarter Range with id: {id} was not found")
    return quarter_range

# adds quarter range to db
# response would be a 201 and response would have fields from QuarterRangeOut
@router.post('/quarter-ranges', status_code=status.HTTP_201_CREATED, response_model=schemas.QuarterRangeOut)
def create_quarter_range(quarter_range: schemas.QuarterRange, 
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if admin. raise exception if not
    if current_user.role_type_id == 1:
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
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")

# updates quarter-range
# return response model with fields from QuarterRangeOut
@router.put('/quarter-ranges/{id}', response_model=schemas.QuarterRangeOut)
def update_quarter_range(id: int, quarter_range: schemas.QuarterRange, 
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
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

# delete a quarter range
# returns status 204 if success
@router.delete('/quarter-ranges/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_quarter_range(id:int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin. returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete quarter range")
    # test if id is in the db. raise exception if not
    quarter_range_query = db.query(models.Quarter_Range).filter(models.Quarter_Range.id == id)
    test_quarter_range = quarter_range_query.first()
    if not test_quarter_range:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quarter Range with id: {id} was not found")
    # deletes quarter-range and returns 204 when completed
    quarter_range_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)