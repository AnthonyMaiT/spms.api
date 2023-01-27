from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from sqlalchemy import func, text
from .. import models, utils, oauth2
from ..schemas import Winners as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use this router to route methods
# prefix for routes in file
# tags for documentation
router = APIRouter(
    prefix='/student-winners',
    tags=['Student Winners']
)

# description of get winners
get_winners_description = "Get all of the winners from database"
# get all winners from the db session
# routes to /student-winners
# response model returns a schema list of StudentWinners that is paginated
@router.get('/', response_model=Page[schemas.StudentWinner], description=get_winners_description)
# connects to db session
# authenticate if user is logged in
# filters for winners
def get_winners(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user), student_id: str = '', quarter_range_id: str = ''):
    # winners query
    winners = db.query(models.StudentWinner)
    # filters based on user id and winner id
    if student_id.isdigit():
        winners = winners.filter(models.StudentWinner.user_id == int(student_id))
    if quarter_range_id.isdigit():
        winners = winners.filter(models.StudentWinner.quarter_range_id == int(quarter_range_id))
    # return a paginated list of winners
    return paginate(winners.all())

# description to create all winners
create_winners_description = "Creates all winners which is added to db"
# creates and add winners to db
# routes to /student-winners
# response status would be 201
# reponse model returns a schema of a list of StudentWinner
@router.post('/', response_model=List[schemas.StudentWinner], status_code=status.HTTP_201_CREATED, description=create_winners_description)
# CreateWinner schema for user to pass in data to create event time
# connects to db session
# authenticate if user is logged in
def create_winners(quarter: schemas.CreateWinner, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    winners = [] # define a list of winners to be added to response
    # checks if quarter with id exists. returns exception if false
    quarter_query = db.query(models.Quarter_Range).filter(quarter.quarter_range_id == models.Quarter_Range.id)
    if not quarter_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quarter range with id: {quarter.quarter_range_id} was not found")
    # checks if already top winner. creates a winner with the most amount of points
    check_top_winner = db.query(models.StudentWinner).filter(quarter.quarter_range_id == models.StudentWinner.quarter_range_id, models.StudentWinner.top_points == True).first()
    if not check_top_winner:
        # get winner based on the quarter and points
        winner_query = db.query(models.User, func.count(models.StudentPoint.user_id).label("points")).join(
            models.StudentPoint, models.StudentPoint.user_id == models.User.id, isouter=True).join(models.EventTime, models.StudentPoint.event_time_id == models.EventTime.id).filter(
                models.EventTime.quarter_range_id == quarter.quarter_range_id).group_by(
                models.User.id).order_by(text("points DESC")).first()
        # check if students have any points 
        if winner_query:
            # level of prize for winner
            level = return_prize_level(winner_query.points)
            # get random prize based on points
            prize = db.query(models.Prize).filter(
                level == models.Prize.level).order_by(
                text("RANDOM()")).first()
            # checks if no prize based on level
            if not prize:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Prize with level: {level} was not found")
            # add top winner to db and add to winners list
            top_winner_dict = {"user_id": winner_query.User.id, "quarter_range_id":quarter.quarter_range_id, "prize_id":prize.id, "top_points":True, "points": winner_query.points}
            winner = models.StudentWinner(**top_winner_dict)
            db.add(winner)
            db.commit()
            db.refresh(winner)
            winners.append(winner)
    # Get a random student from each grade wtih a point
    for grade in range(9, 13):
        # checks if grade winner already exists for quarter
        check_winner = db.query(models.StudentWinner).join(models.User, models.User.id == models.StudentWinner.user_id, isouter=True).filter(
            models.StudentWinner.quarter_range_id == quarter.quarter_range_id,
            models.User.grade == grade, models.StudentWinner.top_points == False).first()
        # would go to the next pass if true
        if check_winner:
            continue
        # gets a random winner based on the quarter then add to db
        grade_winner = db.query(models.User, func.count(models.StudentPoint.user_id).label("points")).join(
            models.User, models.StudentPoint.user_id == models.User.id, isouter=True).join(models.EventTime, models.StudentPoint.event_time_id == models.EventTime.id).filter(
                models.EventTime.quarter_range_id == quarter.quarter_range_id, models.User.grade == grade).group_by(
                models.User.id).order_by(text("RANDOM()")).first()
        # checks if ANY winner exists for the grade
        if grade_winner:
            # level of prize for winner
            level = return_prize_level(grade_winner.points)
            # get random prize based on points
            prize = db.query(models.Prize).filter(
                level == models.Prize.level).order_by(
                text("RANDOM()")).first()
            # checks if no prize based on level
            if not prize:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Prize with level: {level} was not found")
            # add grade quarter winner to db and to list
            quarter_winner = {"user_id": grade_winner.User.id, "quarter_range_id":quarter.quarter_range_id, "prize_id":prize.id, "top_points":False, "points": grade_winner.points}
            winner = models.StudentWinner(**quarter_winner)
            db.add(winner)
            db.commit()
            db.refresh(winner)
            winners.append(winner)
    # check if winners is empty and return exception
    if not winners:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No winners to add to db")
    # return the list of winners
    return winners

# description of updating winner
update_winner_description = "Updates a winner in the database"
# updates winner in db (only prize)
# routes to /student-winners/id where id is an id of a certain winner
# response model is a schema of StudentWinner
@router.put('/{id}', response_model=schemas.StudentWinner, description=update_winner_description)
# id for an id of a certain winner
# UpdateWinner schema for user to pass in data to update winner
# connects to db session
# authenticate if user is logged in
def update_winner(id: int, winner: schemas.UpdateWinner, 
    db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # check if winner with id exist. returns exception if false
    winner_query = db.query(models.StudentWinner).filter(id == models.StudentWinner.id)
    if not winner_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Winner with id: {id} was not found")
    # check if prize id exists. returns exception if false
    prize = db.query(models.Prize).filter(winner.prize_id == models.Prize.id).first()
    if not prize:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prize with id: {winner.prize_id} was not found")
    # updates winner and returns winner
    winner_query.update(winner.dict(), synchronize_session=False)
    db.commit()
    return winner_query.first()

# description of deleting winner
delete_winner_description = "Delete a winner from the database"
# deletes a winner
# routes to /student-winners/id where id is an id of a certain winner
# returns 204 if success
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
# id for an id of winner
# connects to db session
# authenticate if user is logged in
def delete_winner(id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # checks if not admin, returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create quarter range")
    # check if winner with id exist. returns exception if false
    winner_query = db.query(models.StudentWinner).filter(id == models.StudentWinner.id)
    if not winner_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Winner with id: {id} was not found")
    # delete winner and returns status code
    winner_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# would return prize level for certain amount of points
def return_prize_level(count: int):
    if count < 5:
        return 1
    elif count < 15:
        return 2
    else:
        return 3