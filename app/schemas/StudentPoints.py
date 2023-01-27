from datetime import datetime
from pydantic import BaseModel
from .Quarters import QuarterRangeOut
from .Users import UserPointOut
from .Events import EventTime

# point schema for inputting student point
class CreatePoint(BaseModel):
    user_id: int
    event_time_id: int

# point schema for admin to edit point
class EditPoint(BaseModel):
    user_id: int
    event_time_id: int
    
# student points schema for outputting 
class StudentPointsOut(BaseModel):
    id: int
    user_id: int
    user: UserPointOut
    event_time_id: int
    event_time: EventTime
    class Config:
        orm_mode = True

