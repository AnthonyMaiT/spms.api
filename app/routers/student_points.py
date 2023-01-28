from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi.responses import StreamingResponse
from fastapi_pagination import Page, paginate
from sqlalchemy import asc, desc, func, text
from .. import models, utils, oauth2
from ..schemas import StudentPoints as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session
import pandas as pd
import io

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

# description of export student points
export_student_points_description = "Export student points from database into excel sheet"
# export student points from the db session
# routes to /student-points/export
# response model returns a schema list of StudentPointsOut that is paginated
@router.get('/export',description=export_student_points_description)
# connects to db session
# authenticate if user is logged in
# filters for student points
def get_points_for_export(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user), quarter_range_id: str = ''):
    # checks if not admin and returns exception if true
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to export student points")
    # checks if the quarter range is not a digit and return exception if true
    if quarter_range_id.isdigit() == False:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict with quarter range id filter")
    # get quarter range from the filter
    quarter_range = db.query(models.Quarter_Range).join(models.Quarter, models.Quarter_Range.quarter_id == models.Quarter.id).filter(
        models.Quarter_Range.id == quarter_range_id).first()
    # returns exception if quarter range doesn't exists
    if not quarter_range:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quarter range with filter not found")
    # query all users with points
    user_points = db.query(models.User, func.count(models.StudentPoint.user_id).label("points")).join(
            models.StudentPoint, models.StudentPoint.user_id == models.User.id , isouter= True
            ).join(models.EventTime, models.EventTime.id == models.StudentPoint.event_time_id).filter(
            models.EventTime.quarter_range_id == int(quarter_range_id)
        ).group_by(models.User.id)
    # Creates a dataframe from pandas, apply filter for each grade, set column names and content
    df = pd.read_sql(sql=user_points.filter(models.User.grade==9).with_entities(
            models.User.id.label('User ID'),
            models.User.username.label('Username'), 
            models.User.first_name.label('First Name'),
            models.User.last_name.label('Last Name'),
            models.User.grade.label('Grade Level'),
            func.count(models.StudentPoint.user_id).label("points")
        ).statement, con=engine)
    df1 = pd.read_sql(sql=user_points.filter(models.User.grade==10).with_entities(
            models.User.id.label('User ID'),
            models.User.username.label('Username'), 
            models.User.first_name.label('First Name'),
            models.User.last_name.label('Last Name'),
            models.User.grade.label('Grade Level'),
            func.count(models.StudentPoint.user_id).label("points")
        ).statement, con=engine)
    df2 = pd.read_sql(sql=user_points.filter(models.User.grade==11).with_entities(
            models.User.id.label('User ID'),
            models.User.username.label('Username'), 
            models.User.first_name.label('First Name'),
            models.User.last_name.label('Last Name'),
            models.User.grade.label('Grade Level'),
            func.count(models.StudentPoint.user_id).label("points")
        ).statement, con=engine)
    df3 = pd.read_sql(sql=user_points.filter(models.User.grade==12).with_entities(
            models.User.id.label('User ID'),
            models.User.username.label('Username'), 
            models.User.first_name.label('First Name'),
            models.User.last_name.label('Last Name'),
            models.User.grade.label('Grade Level'),
            func.count(models.StudentPoint.user_id).label("points")
        ).statement, con=engine)
    # for exporting excel file data to the user instead of using a path
    out = io.BytesIO()
    # writes excel file
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        # seperates each data frame into sheets of different grades
        df.to_excel(excel_writer=writer,index=False,sheet_name='Grade 9')
        df1.to_excel(excel_writer=writer,index=False,sheet_name='Grade 10')
        df2.to_excel(excel_writer=writer,index=False,sheet_name='Grade 11')
        df3.to_excel(excel_writer=writer,index=False,sheet_name='Grade 12')
        # auto adjust column width
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['Grade 9'].set_column(col_idx, col_idx, column_length)
        for column in df1:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df2.columns.get_loc(column)
            writer.sheets['Grade 10'].set_column(col_idx, col_idx, column_length)
        for column in df2:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['Grade 11'].set_column(col_idx, col_idx, column_length)
        for column in df3:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['Grade 12'].set_column(col_idx, col_idx, column_length)
    # start and end range for file name
    start_range = quarter_range.start_range.strftime('%Y%m%d')
    end_range = quarter_range.end_range.strftime('%Y%m%d')
    # creates a response with media type and headers for the file name
    response = StreamingResponse(iter([out.getvalue()]), media_type="application/x-xls", headers={
        'content-disposition':f'attachment; filename={start_range}-{end_range} {quarter_range.quarter.quarter} Points.xlsx'})
    # return the response
    return response