from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .Users import UserPointOut
from .Quarters import QuarterRangeOut
from .Prizes import Prize

# used to create a winner in db
class CreateWinner(BaseModel):
    quarter_range_id: int

# used to update a prize of a winner in db
class UpdateWinner(BaseModel):
    prize_id: int

# used to output the winner in db
class StudentWinner(BaseModel):
    id: int
    top_points: bool
    user_id: int
    user: UserPointOut
    quarter_range_id: int
    quarter_range: QuarterRangeOut
    prize_id: int
    prize: Prize
    class Config:
        orm_mode=True
