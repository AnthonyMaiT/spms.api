from datetime import datetime
from pydantic import BaseModel
from .Quarters import QuarterRangeOut
from .Users import UserPointOut
from .Events import EventTimes

# for inputting student point
class StudentPoint(BaseModel):
    user_id: int
    event_time_id: int

# for admin to edit point
class EditPoint(BaseModel):
    user_id: int
    event_time_id: int
    
# for outputting student point 
class StudentPointsOut(BaseModel):
    id: int
    user_id: int
    user: UserPointOut
    event_time_id: int
    event_time: EventTimes
    class Config:
        orm_mode = True

