from datetime import datetime
from pydantic import BaseModel

from app.schemas.Quarters import QuarterRangeOut

# schema for creating an event
class CreateEvent(BaseModel):
    name: str
    is_sport: bool

# define Events schema for output
# refrences CreateEvent to add name and is_sport fields
class Events(CreateEvent):
    id: int
    # in order to return schema to user
    class Config:
        orm_mode=True

# schema for creating event time
class CreateEventTime(BaseModel):
    start_time: datetime
    end_time: datetime
    event_id: int

# schema for outputting event time
class EventTimes(CreateEventTime):
    id: int
    event: Events
    quarter_range_id: int
    quarter_range: QuarterRangeOut
    # to return schema to user
    class Config: 
        orm_mode=True