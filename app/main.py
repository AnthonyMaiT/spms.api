from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import models
from .routers import auth, user, quarter, event

from app.database import get_db
from sqlalchemy.orm import Session

# defines that app is for FastAPI
app = FastAPI()

# origins of which server can access the app
origins = ["*"]

# enable cors to add origins and allow certain methods/headers 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# adds routes to app
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(quarter.router)
app.include_router(event.router)

# path / would return hello world
@app.get('/')
def main(db:Session = Depends(get_db)):
    return {'message': 'hello world!'}