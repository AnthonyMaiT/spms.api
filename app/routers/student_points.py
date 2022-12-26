from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
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
@router.get('/', response_model=List[schemas.StudentPointsOut])
# gets db session and authenticate user is logged in
def get_points(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # gets event of student for student
    if current_user.role_type_id == 3:
        student_points = db.query(models.StudentPoint).filter(models.StudentPoint.user_id == current_user.id).all()
        return student_points
    # gets all events in db for admin/staff
    points = db.query(models.StudentPoint).all()
    return points

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

# add point to db
@router.post('/',status_code=status.HTTP_201_CREATED, response_model=schemas.StudentPointsOut)
def add_point(point: schemas.StudentPoints, 
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # checks if not admin/staff
    if current_user.role_type_id != 1 and current_user.role_type_id != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to add points")

    # checks if username is valid
    user = db.query(models.User).filter(models.User.username == point.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find username in db")
    # checks if student
    if user.role_type_id != 3:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only students can have points")

    # check if event id exists
    event = db.query(models.Events).filter(models.Events.id == point.event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with id: {point.event_id} does not exist")
    
    # check if attended time fits in quarter
    attended_time = datetime.now()
    quarter_range = db.query(models.Quarter_Range).filter(attended_time >= models.Quarter_Range.start_range, 
        attended_time <= models.Quarter_Range.end_range).first()
    if not quarter_range:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find quarter range in db")
    
    # create db to add point
    new_point = {"user_id": user.id, "quarter_range_id": quarter_range.id, "event_id": point.event_id,
        "attended_at": attended_time}
    # add point and return created point
    created_point = models.StudentPoint(**new_point)
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
    
    # check if event id exists
    event = db.query(models.Events).filter(models.Events.id == point.event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with id: {point.event_id} does not exist")
    
    # check if attended time fits in quarter
    quarter_range = db.query(models.Quarter_Range).filter(point.attended_at >= models.Quarter_Range.start_range, 
        point.attended_at <= models.Quarter_Range.end_range).first()
    if not quarter_range:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find quarter range in db")

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

    