from datetime import datetime
from typing import List
from fastapi import Body, Response, status, HTTPException, Depends, APIRouter
from fastapi_pagination import Page, paginate
from sqlalchemy import desc
from .. import models, utils, oauth2
from ..schemas import UserSteps as schemas
from ..database import engine, get_db
from sqlalchemy.orm import Session

# app would use this router to route methods
# prefix for routes in file
# tags for documentation
router = APIRouter(
    prefix='/user-steps',
    tags=['User Steps']
)

# description of get user steps
get_steps_description = "Get all of the user steps from database"
# get all user steps from the db session
# routes to /user-steps
# response model returns a schema list of UserStep that is paginated
@router.get('/', response_model=Page[schemas.UserStep], description=get_steps_description)
# connects to db
# authenticate if user is logged in
# filters for step
def get_steps(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user), user_id: str = ''):
    if current_user.role_type_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User cannot access user steps")
    # gets all steps
    steps = db.query(models.UserStep)
    # filters for step
    if  user_id.isdigit():
        steps = steps.filter(models.UserStep.user_id == user_id)
        print(user_id)
    # returns a paginated list of users
    return paginate(steps.order_by(desc(models.UserStep.accessed_at)).all())

# description of create step
create_step_description = "Creates a step which is added to db"
# creates and add step to db
# routes to /user-steps
# response status would be 201
# reponse model returns a schema of UserStep
@router.post('/', response_model=schemas.UserStep, status_code=status.HTTP_201_CREATED, description=create_step_description)
# CreateStep schema for user to pass in data to create step
# connects to db session
# authenticate if user is logged in
def create_step(step: schemas.CreateStep,db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # adds step to db and returns step to user
    new_step = models.UserStep(**step.dict())
    db.add(new_step)
    db.commit()
    db.refresh(new_step)
    return new_step