from datetime import datetime
from typing import Optional
from pydantic import BaseModel, conint

from app.schemas import Main as schemas


class UserCreate(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    role_type_id: Optional[conint(ge=1,le=3)] = None

class UserUpdate(BaseModel):
    username: str
    first_name: str
    last_name: str
    role_type_id: Optional[conint(ge=1,le=3)] = None

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

class UserLogin(BaseModel):
    email: str
    password: str

class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str

class ResetPassword(BaseModel):
    new_password: str
    confirm_new_password: str
