from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from sqlalchemy import desc
from .. import models, utils, oauth2
from ..schemas import StudentPoints as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use this router to route methods
# prefix for routes in file
# tags for documentation
router = APIRouter(
    prefix='/student-points',
    tags=['Student Points']
)

# description of get student points
get_student_points_description = "Get all of the student points from database"
# get all student points from the db session
# routes to /student-points
# response model returns a schema list of StudentPointsOut that is paginated
@router.get('/', response_model=Page[schemas.StudentPointsOut],description=get_student_points_description)
# connects to db session
# authenticate if user is logged in
# filters for student points
def get_points(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user), student_id: str = '', event_time_id: str = '', quarter_range_id: str = ''):
    # checks if current user is a student
    if current_user.role_type_id == 3:
        # get student points based on current user and join with event time table
        student_points = db.query(models.StudentPoint).join(models.EventTime, models.EventTime.id == models.StudentPoint.event_time_id).order_by(desc(models.StudentPoint.id)).filter(models.StudentPoint.user_id == current_user.id)
        # filters for event time and quarter range
        if event_time_id.isdigit():
            student_points = student_points.filter(models.StudentPoint.event_time_id == int(event_time_id))
        if quarter_range_id.isdigit():
            student_points = student_points.filter(models.EventTime.quarter_range_id == int(quarter_range_id))
        # return a paginated list of student poitns
        return paginate(student_points.all())
    # gets all event times in db for admin/staff
    points = db.query(models.StudentPoint).join(models.EventTime, models.EventTime.id == models.StudentPoint.event_time_id).order_by(desc(models.StudentPoint.id))
    # filters for event, user, and quarter
    if student_id.isdigit():
        points = points.filter(models.StudentPoint.user_id == int(student_id))
    if event_time_id.isdigit():
        points = points.filter(models.StudentPoint.event_time_id == int(event_time_id))
    if quarter_range_id.isdigit():
        points = points.filter(models.EventTime.quarter_range_id == int(quarter_range_id))
    # return a paginated list of student points
    return paginate(points.all())

# description of create student point
create_point_description = "Creates a student point which is added to db"
# creates and add student point to db
# routes to /student-points
# response status would be 201
# reponse model returns a schema of StudentPointsOut
@router.post('/',status_code=status.HTTP_201_CREATED, response_model=schemas.StudentPointsOut, description=create_point_description)
# CreatePoint schema for user to pass in data to create student point
# connects to db session
# authenticate if user is logged in
def add_point(point: schemas.CreatePoint,
    db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # returns exception if user isn't an admin
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to add points")
    # checks if user id is valid. return exception if isn't
    user = db.query(models.User).filter(models.User.id == point.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find user id in db")
    # checks if point already exist and return exception if true
    find_point = db.query(models.StudentPoint).filter(models.StudentPoint.event_time_id == point.event_time_id, 
        models.StudentPoint.user_id == user.id).first()
    if find_point:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already attended event")
    # checks if data is a student and return exception if false
    if user.role_type_id != 3:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only students can have points")
    # adds student point to db and return point back to user
    created_point = models.StudentPoint(**point.dict())
    db.add(created_point)
    db.commit()
    db.refresh(created_point)
    return created_point
    
# description of updating student point
update_point_description = "Updates a student point in the database"
# updates student point in db
# routes to /student-points/id where id is an id of a certain point
# response model is a schema of StudentPointsOut
@router.put('/{id}', response_model=schemas.StudentPointsOut, description=update_point_description)
# id for an id of a certain student point
# EditPoint schema for user to pass in data to update point
# connects to db session
# authenticate if user is logged in
def edit_point(id: int, point: schemas.EditPoint, 
    db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # only admin can edit point returns exception if false
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to add points")
    # check if id in url exists returns exception if false
    point_query = db.query(models.StudentPoint).filter(models.StudentPoint.id == id)
    if not point_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student point with id: {id} does not exist")
    # check if user id exists returns exception if false
    user = db.query(models.User).filter(models.User.id == point.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {point.user_id} does not exist")
    # checks if student returns exception if false
    if user.role_type_id != 3:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only students can have points")
    # check if event time id exists returns exception if false
    event_time = db.query(models.EventTime).filter(models.EventTime.id == point.event_time_id).first()
    if not event_time:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event Time with id: {point.event_time_id} does not exist")
    # checks if point already exist returns exception if false
    find_point = db.query(models.StudentPoint).filter(models.StudentPoint.event_time_id == point.event_time_id, 
        models.StudentPoint.user_id == user.id).first()
    if find_point:
        if find_point.id == id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already attended event")
    # updates point in db and returns point
    point_query.update(point.dict(),synchronize_session=False)
    db.commit()
    return point_query.first()

# description of deleting point
delete_point_description = "Delete a student point from the database"
# deletes a student point
# routes to /student-points/id where id is an id of a certain point
# returns 204 if success
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT, description=delete_point_description)
# id for an id of student point
# connects to db session
# authenticate if user is logged in
def delete_point(id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # checks if not admin and returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete points")
    # check if id in url exists returns exception if false
    point_query = db.query(models.StudentPoint).filter(models.StudentPoint.id == id)
    if not point_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student point with id: {id} does not exist")
    # delete student point from db and return response
    point_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

    