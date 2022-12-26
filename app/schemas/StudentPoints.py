from datetime import datetime
from pydantic import BaseModel
from .Quarters import QuarterRangeOut
from .Users import UserPointOut
from .Events import Events

# for inputting student point
class StudentPoints(BaseModel):
    username: str
    event_id: int

# for admin to edit point
class EditPoint(BaseModel):
    user_id: int
    event_id: int
    attended_at: datetime

# for outputting student point 
class StudentPointsOut(BaseModel):
    id: int
    user_id: int
    user: UserPointOut
    event_id: int
    event: Events
    attended_at: datetime
    quarter_range_id: int
    quarter_range: QuarterRangeOut
    class Config:
        orm_mode = True

