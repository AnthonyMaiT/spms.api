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

# description of get past winners
get_past_winners_description = "Get all of the past winners from database"
# get all events from the db session
# routes to /past-winners
# response model returns a schema list of StudentWinner
@router.get('/past-winners', response_model=List[schemas.StudentWinner], description=get_past_winners_description)
# connects to db session
# authenticate if user is logged in
# filters for past winners
def get_past_winners(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user), quarter_range_id: str = ''):
    # past winner query
    past_winners = db.query(models.StudentWinner)
    # checks quarter range id filter 
    if quarter_range_id.isdigit():
        past_winners = past_winners.filter(models.StudentWinner.quarter_range_id == quarter_range_id).limit(5).all()
        if not past_winners:
            return []
        return past_winners
    return []

# description of get past quarter
get_past_quarter_description = "Get all of the past quarter ranges from database"
# get all events from the db session
# routes to /past-quarter
# response model returns a schema QuarterRangeOut
@router.get('/past-quarter', response_model=schemas.QuarterRangeOut, description=get_past_quarter_description)
def get_past_quarter_range(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # gets the current datetime
    current_time = datetime.now()
    # gets current quarter from the current datetime
    current_quarter = db.query(models.Quarter_Range).filter(
        models.Quarter_Range.end_range > current_time, models.Quarter_Range.start_range < current_time
        ).first()
    # quarter range query
    previous_quarter = db.query(models.Quarter_Range)
    # finds quarters that are not the current one and in the past
    if current_quarter:
        previous_quarter = previous_quarter.filter(models.Quarter_Range.id != current_quarter.id)
    previous_quarter = previous_quarter.filter(models.Quarter_Range.end_range < current_time).order_by(
        desc(models.Quarter_Range.end_range)
    ).first()
    # return http exception if none exist
    if not previous_quarter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No past quarters found")
    # return the previous quarter
    return previous_quarter

# gets all the user points accumulated together and return a paginated leaderboard if there are any
# all depends on the quarter range id
# description of get leaderboards
get_leaderboards_description = "Get all of the leaderboards from database"
# get all leaderboards from the db session
# routes to /leaderboards
# response model returns a schema list of Points that is paginated
# filters for leaderboard
@router.get('/leaderboards', response_model=Page[schemas.Points], description=get_leaderboards_description)
def get_current_leaderboard(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), quarter_range_id: str = ''):
    # accumlate all user point for a certain quarter range and return it if exists
    if quarter_range_id.isdigit():
        user_points = db.query(models.User, func.count(models.StudentPoint.user_id).label("points")).join(
            models.StudentPoint, models.StudentPoint.user_id == models.User.id , isouter= True
            ).join(models.EventTime, models.EventTime.id == models.StudentPoint.event_time_id).filter(
            models.EventTime.quarter_range_id == int(quarter_range_id)
        ).group_by(models.User.id).order_by(text("points DESC")).all()
        if not user_points:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user points found for quarter")
        return paginate(user_points)
    # return if no user points at all
    return paginate([])

# gets the current points of the user for the quarter range
# description of get user points
get_user_points_description = "Get the points for the current user"
# get points for current user from the db session
# routes to /user-points
# response model returns a schema Points
@router.get('/user-points', response_model=schemas.Points)
# connects to db session
# authenticate if user is logged in
# filters for points
def get_current_user_points(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), quarter_range_id: str = ''):
    # returns exception if current user not a student
    if current_user.role_type_id != 3:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No points for current user")
    # returns exception if quarter range id not a number 
    if (quarter_range_id.isdigit()):
        # get all the points for the current user and certain quarter
        user_points = db.query(models.User, func.count(models.StudentPoint.id).label("points")).join(
            models.StudentPoint, models.StudentPoint.user_id == models.User.id , isouter= True
        ).join(models.EventTime, models.EventTime.id == models.StudentPoint.event_time_id, isouter=True).filter(
            models.EventTime.quarter_range_id == quarter_range_id, models.User.id == current_user.id
        ).group_by(models.User.id).first()
        # return exception if no points exists for user
        if not user_points:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student points found for user")
        return user_points
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="quarter range id not found")