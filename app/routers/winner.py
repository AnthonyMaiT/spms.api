from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from sqlalchemy import func, text
from .. import models, utils, oauth2
from ..schemas import Winners as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use router to route methods below
# tags for documentation
router = APIRouter(
    prefix='/student-winners',
    tags=['Student Winners']
)

# get all winners from db
# response schema is a list of StudentWinners
@router.get('/', response_model=Page[schemas.StudentWinner])
# get db session and authenticate user login
def get_winners(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), student_id: str = '', quarter_range_id: str = ''):
    # returns winners
    winners = db.query(models.StudentWinner)
    # filters based on user id and winner id
    if student_id.isdigit():
        winners = winners.filter(models.StudentWinner.user_id == int(student_id))
    if quarter_range_id.isdigit():
        winners = winners.filter(models.StudentWinner.quarter_range_id == int(quarter_range_id))
    return paginate(winners.all())

# get a single winner from db
# response schema is of StudentWinner
@router.get('/{id}', response_model=schemas.StudentWinner)
def get_winner(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if id not in db. returns error
    winner = db.query(models.StudentWinner).filter(models.StudentWinner.id == id).first()
    if not winner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Winner with id: {id} was not found")
    return winner

# creates all winners from each grade
# response schema is recently created winners
@router.post('/', response_model=List[schemas.StudentWinner], status_code=status.HTTP_201_CREATED)
def create_winners(quarter: schemas.CreateWinner, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    winners = []
    # checks if quarter with id exists
    quarter_query = db.query(models.Quarter_Range).filter(quarter.quarter_range_id == models.Quarter_Range.id)
    if not quarter_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quarter range with id: {quarter.quarter_range_id} was not found")
    # checks if already top winner
    check_top_winner = db.query(models.StudentWinner).filter(quarter.quarter_range_id == models.StudentWinner.quarter_range_id, models.StudentWinner.top_points == True).first()
    if not check_top_winner:
        # get top winner based on the quarter
        winner_query = db.query(models.User, func.count(models.StudentPoint.user_id).label("points")).join(
            models.StudentPoint, models.StudentPoint.user_id == models.User.id, isouter=True).join(models.EventTime, models.StudentPoint.event_time_id == models.EventTime.id).filter(
                models.EventTime.quarter_range_id == quarter.quarter_range_id).group_by(
                models.User.id).order_by(text("points DESC")).first()
        if winner_query:
            level = return_prize_level(winner_query.points)
            # get random prize based on points
            prize = db.query(models.Prize).filter(
                level == models.Prize.level).order_by(
                text("RANDOM()")).first()
            if not prize:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Prize with level: {level} was not found")
            # add top winner to db
            top_winner_dict = {"user_id": winner_query.User.id, "quarter_range_id":quarter.quarter_range_id, "prize_id":prize.id, "top_points":True, "points": winner_query.points}
            winner = models.StudentWinner(**top_winner_dict)
            db.add(winner)
            db.commit()
            db.refresh(winner)
            winners.append(winner)
    # get random for each grade
    for grade in range(9, 13):
        # checks if grade winner exists for quarter
        check_winner = db.query(models.StudentWinner).join(models.User, models.User.id == models.StudentWinner.user_id, isouter=True).filter(
            models.StudentWinner.quarter_range_id == quarter.quarter_range_id,
            models.User.grade == grade, models.StudentWinner.top_points == False).first()
        if check_winner:
            continue
        # gets a random winner based on the quarter then add to db
        grade_winner = db.query(models.User, func.count(models.StudentPoint.user_id).label("points")).join(
            models.User, models.StudentPoint.user_id == models.User.id, isouter=True).join(models.EventTime, models.StudentPoint.event_time_id == models.EventTime.id).filter(
                models.EventTime.quarter_range_id == quarter.quarter_range_id, models.User.grade == grade).group_by(
                models.User.id).order_by(text("RANDOM()")).first()
        # checks if ANY winner exists
        if grade_winner:
            level = return_prize_level(grade_winner.points)
            # get random prize based on points
            prize = db.query(models.Prize).filter(
                level == models.Prize.level).order_by(
                text("RANDOM()")).first()
            if not prize:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Prize with level: {level} was not found")
            # add grade quarter winner to db
            quarter_winner = {"user_id": grade_winner.User.id, "quarter_range_id":quarter.quarter_range_id, "prize_id":prize.id, "top_points":False, "points": grade_winner.points}
            winner = models.StudentWinner(**quarter_winner)
            db.add(winner)
            db.commit()
            db.refresh(winner)
            winners.append(winner)
    # check if winners is empty
    if not winners:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No winners to add to db")
    return winners

# updates a winner from db (only prize)
@router.put('/{id}', response_model=schemas.StudentWinner)
def update_winner(id: int, winner: schemas.UpdateWinner, 
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # check if winner with id exist
    winner_query = db.query(models.StudentWinner).filter(id == models.StudentWinner.id)
    if not winner_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Winner with id: {id} was not found")
    # check if prize id exists
    prize = db.query(models.Prize).filter(winner.prize_id == models.Prize.id).first()
    if not prize:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prize with id: {winner.prize_id} was not found")
    # updates winner and returns winner
    winner_query.update(winner.dict(), synchronize_session=False)
    db.commit()
    return winner_query.first()

# delete winner from db
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_winner(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # check if winner with id exist
    winner_query = db.query(models.StudentWinner).filter(id == models.StudentWinner.id)
    if not winner_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Winner with id: {id} was not found")
    # delete winner and returns status
    winner_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# would return prize for amount of points
def return_prize_level(count: int):
    if count < 5:
        return 1
    elif count < 15:
        return 2
    else:
        return 3