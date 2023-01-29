from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, conint

# schema so user knows what params to do. pydantic model
# defines structure of a request and response

# schema for role type for Users
class RoleType(BaseModel):
    id: int
    role_type: str
    # used to output model
    class Config:
        orm_mode = True

# token schema to output to user after login
class Token(BaseModel):
    access_token: str
    token_type: str

# would add id to token
class TokenData(BaseModel):
    id: Optional[str] = None

# for the chatbot input of the user
class ChatBotInput(BaseModel):
    message: str