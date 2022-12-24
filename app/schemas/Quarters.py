from datetime import datetime
from typing import Optional
from pydantic import BaseModel, conint

from app.schemas import Main as schemas

# Quarter schema for retrieving a quarter
class Quarter(BaseModel):
    id: int
    quarter: str
    # used to output a model
    class Config:
        orm_mode = True
# Quarter Range schema for put/post method
class QuarterRange(BaseModel):
    start_range: datetime
    end_range: datetime
    quarter_id: conint(le=4, ge=1) # only accepts an int from 1 to 4 inclusive

# Quarter Range schema referencing the above schema for user output
class QuarterRangeOut(QuarterRange):
    id: int
    quarter: Quarter
    # used to output model
    class Config:
        orm_mode = True