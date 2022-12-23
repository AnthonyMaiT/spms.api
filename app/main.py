from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import models
from .routers import auth, user

from app.database import get_db
from sqlalchemy.orm import Session

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(user.router)

@app.get('/')
def main(db:Session = Depends(get_db)):
    return {'message': 'hello world!'}