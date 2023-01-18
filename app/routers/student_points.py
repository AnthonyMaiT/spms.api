from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from sqlalchemy import desc
from .. import models, utils, oauth2
from ..schemas import StudentPoints as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use router to route methods below
# tags for documentation
router = APIRouter(
    prefix='/student-points',
    tags=['Student Points']
)

# get only points from student user of user
# get all student points from the db or admin/staff
# response schema is from Student Points
# repsonse would be paged for pagination
@router.get('/', response_model=Page[schemas.StudentPointsOut])
# gets db session and authenticate user is logged in
def get_points(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), student_id: str = '', event_time_id: str = '', quarter_range_id: str = ''):
    # gets event of student for student
    if current_user.role_type_id == 3:
        student_points = db.query(models.StudentPoint).filter(models.StudentPoint.user_id == current_user.id)
        # filters for event and quarter 
        if event_time_id.isdigit():
            points = points.filter(models.StudentPoint.event_time_id == int(event_time_id))
        if quarter_range_id.isdigit():
            points = points.filter(models.EventTime.quarter_range_id == int(quarter_range_id))
        return paginate(student_points.all())
    # gets all events in db for admin/staff
    points = db.query(models.StudentPoint).join(models.EventTime, models.EventTime.id == models.StudentPoint.event_time_id).order_by(desc(models.StudentPoint.id))
    # filters for event, user, and quarter
    if student_id.isdigit():
        points = points.filter(models.StudentPoint.user_id == int(student_id))
    if event_time_id.isdigit():
        points = points.filter(models.StudentPoint.event_time_id == int(event_time_id))
    if quarter_range_id.isdigit():
        points = points.filter(models.EventTime.quarter_range_id == int(quarter_range_id))
    return paginate(points.all())

# get only point from student user of user
# get any student point from the db for admin/staff
@router.get('/{id}', response_model=schemas.StudentPointsOut)
def get_point(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks to see if id in db exists
    point_query = db.query(models.StudentPoint).filter(models.StudentPoint.id == id).first()
    if not point_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student point with id: {id} does not exist")
    # student can only access own points
    if current_user.role_type_id == 3 and current_user.id != point_query.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to get this point")
    return point_query

# add a point to the db with student id and event time id
@router.post('/',status_code=status.HTTP_201_CREATED, response_model=schemas.StudentPointsOut)
def add_point(point: schemas.StudentPoint,
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to add points")
    # checks if user id is valid
    user = db.query(models.User).filter(models.User.id == point.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find user id in db")
    # checks if point already exist
    find_point = db.query(models.StudentPoint).filter(models.StudentPoint.event_time_id == point.event_time_id, 
        models.StudentPoint.user_id == user.id).first()
    if find_point:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already attended event")
    # checks if student
    if user.role_type_id != 3:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only students can have points")
    created_point = models.StudentPoint(**point.dict())
    db.add(created_point)
    db.commit()
    db.refresh(created_point)
    return created_point
    
# edit point inside of db
@router.put('/{id}', response_model=schemas.StudentPointsOut)
def edit_point(id: int, point: schemas.EditPoint, 
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # only admin can edit point
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to add points")
    # check if id in url exists
    point_query = db.query(models.StudentPoint).filter(models.StudentPoint.id == id)
    if not point_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student point with id: {id} does not exist")

    # check if user id exists
    user = db.query(models.User).filter(models.User.id == point.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {point.user_id} does not exist")
    # checks if student
    if user.role_type_id != 3:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only students can have points")
    
    # check if event time id exists
    event_time = db.query(models.EventTime).filter(models.EventTime.id == point.event_time_id).first()
    if not event_time:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event Time with id: {point.event_time_id} does not exist")
    # checks if point already exist
    find_point = db.query(models.StudentPoint).filter(models.StudentPoint.event_time_id == point.event_time_id, 
        models.StudentPoint.user_id == user.id).first()
    if find_point:
        if find_point.id == id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already attended event")
    point_query.update(point.dict(),synchronize_session=False)
    db.commit()
    return point_query.first()

# remove student point from db
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_point(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin and returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete points")
    # check if id in url exists
    point_query = db.query(models.StudentPoint).filter(models.StudentPoint.id == id)
    if not point_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student point with id: {id} does not exist")
    # delete student point from db
    point_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

    