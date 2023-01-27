from datetime import datetime
from typing import Optional
from pydantic import BaseModel, conint

from app.schemas import Main as schemas

# schema for creating a user
class UserCreate(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    grade: Optional[conint(ge=1,le=12)] = None # only accepts int from 1 to 12 inclusive
    role_type_id: Optional[conint(ge=1,le=3)] = None # only accepts int from 1 to 3 inclusive

# schema for updating a user
class UserUpdate(BaseModel):
    username: str
    first_name: str
    last_name: str
    grade: Optional[conint(ge=1,le=12)] = None # only accepts int from 1 to 12 inclusive
    role_type_id: Optional[conint(ge=1,le=3)] = None # only accepts int from 1 to 3 inclusive

# schema for outputing user
class UserOut(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    created_at: datetime
    grade: Optional[conint(ge=1,le=12)] = None # only accepts int from 1 to 3 inclusive
    edited_at: Optional[datetime] = None
    role_type_id: Optional[conint(ge=1,le=3)] = None # only accepts int from 1 to 3 inclusive
    role_type: Optional[schemas.RoleType] = None
    # used to output model
    class Config:
        orm_mode = True

# schema used to output user for a created point
class UserPointOut(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    grade: Optional[conint(ge=1,le=12)] = None
    # used to output model
    class Config:
        orm_mode = True

# schema for logging in user
class UserLogin(BaseModel):
    email: str
    password: str

# schema for changing password
class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str

# schema for resetting password
class ResetPassword(BaseModel):
    new_password: str
    confirm_new_password: str
