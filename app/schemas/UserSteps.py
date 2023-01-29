from pydantic import BaseModel
from .Users import UserOut
from datetime import datetime

# schema for creating a step
class CreateStep(BaseModel):
    user_id: int
    step: str

# User step schema for output
# references CreateStep for fields
class UserStep(CreateStep):
    id: int
    accessed_at: datetime
    user: UserOut
    class Config:
        orm_mode=True