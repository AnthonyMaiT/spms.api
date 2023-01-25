from datetime import datetime
from typing import List
from fastapi import APIRouter, Response, status, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy import desc, func, text
from ..schemas import Winners as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session
from .. import models, utils, oauth2


router = APIRouter(
    tags=['Leaderboards']
)

# gets all the past winners depending on the past quarter
@router.get('/past-winners', response_model=List[schemas.StudentWinner])
def get_past_winners(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), quarter_range_id: str = ''):
    past_winners = db.query(models.StudentWinner)
    if quarter_range_id.isdigit():
        past_winners = past_winners.filter(models.StudentWinner.quarter_range_id == quarter_range_id).limit(5).all()
        if not past_winners:
            return []
        return past_winners
    return []

# gets the past quarter from the db that isn't the current quarter
@router.get('/past-quarter', response_model=schemas.QuarterRangeOut)
def get_past_quarter_range(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    current_time = datetime.now()
    current_quarter = db.query(models.Quarter_Range).filter(
        models.Quarter_Range.end_range > current_time, models.Quarter_Range.start_range < current_time
        ).first()
    previous_quarter = db.query(models.Quarter_Range)
    if current_quarter:
        previous_quarter = previous_quarter.filter(models.Quarter_Range.id != current_quarter.id)
    previous_quarter = previous_quarter.filter(models.Quarter_Range.end_range < current_time).order_by(
        desc(models.Quarter_Range.end_range)
    ).first()
    if not previous_quarter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No past quarters found")
    return previous_quarter

# gets all the user points accumulated together and return a paginated leaderboard
@router.get('/current-leaderboards', response_model=Page[schemas.Points])
def get_current_leaderboard(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    current_date = datetime.now()
    current_quarter_range = db.query(models.Quarter_Range).filter(
        models.Quarter_Range.start_range < current_date, 
        models.Quarter_Range.end_range > current_date
    ).first()
    if not current_quarter_range:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No quarter range for today's date")
    user_points = db.query(models.User, func.count(models.StudentPoint.user_id).label("points")).join(
        models.StudentPoint, models.StudentPoint.user_id == models.User.id , isouter= True
    ).join(models.EventTime, models.EventTime.id == models.StudentPoint.event_time_id).filter(
        models.EventTime.quarter_range_id == current_quarter_range.id
    ).group_by(models.User.id).order_by(text("points DESC")).all()
    return paginate(user_points)

# gets the current points of the user
@router.get('/current-points', response_model=schemas.Points)
def get_current_user_points(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user.role_type_id != 3:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No points for current user")
    current_date = datetime.now()
    current_quarter_range = db.query(models.Quarter_Range).filter(
        models.Quarter_Range.start_range < current_date, 
        models.Quarter_Range.end_range > current_date
    ).first()
    # checks if any point exists for the user
    if not current_quarter_range:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No quarter range for today's date")
    user_points = db.query(models.User, func.count(models.StudentPoint.id).label("points")).join(
        models.StudentPoint, models.StudentPoint.user_id == models.User.id , isouter= True
    ).join(models.EventTime, models.EventTime.id == models.StudentPoint.event_time_id, isouter=True).filter(
        models.EventTime.quarter_range_id == current_quarter_range.id, models.User.id == current_user.id
    ).group_by(models.User.id).first()
    if not user_points:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student points found for user")
    return user_points