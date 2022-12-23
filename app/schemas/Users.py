from datetime import datetime
from typing import Optional
from pydantic import BaseModel, conint

from app.schemas import Main as schemas

# creates schema for creating a user
class UserCreate(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    role_type_id: Optional[conint(ge=1,le=3)] = None

# creates schema for updating a user
class UserUpdate(BaseModel):
    username: str
    first_name: str
    last_name: str
    role_type_id: Optional[conint(ge=1,le=3)] = None

# for outputing user
class UserOut(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    created_at: datetime
    edited_at: Optional[datetime] = None
    role_type_id: Optional[int] = None
    role_type: Optional[schemas.RoleType] = None
    class Config:
        orm_mode = True

# for logging in user
class UserLogin(BaseModel):
    email: str
    password: str

# for changing password
class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str

# for resetting password
class ResetPassword(BaseModel):
    new_password: str
    confirm_new_password: str
