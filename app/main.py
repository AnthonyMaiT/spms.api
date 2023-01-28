from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from app import models
from .routers import auth, user, quarter, event, student_points, prize, winner, event_times, leaderboard

from app.database import get_db
from sqlalchemy.orm import Session

# defines that app is for FastAPI
app = FastAPI()

# origins of which server can access the app
origins = ["http://localhost:4200"]

# enable cors to add origins and allow certain methods/headers 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # for exporting student points to user
    expose_headers=["content-disposition"]
)

# adds routes to app
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(quarter.router)
app.include_router(event.router)
app.include_router(student_points.router)
app.include_router(prize.router)
app.include_router(winner.router)
app.include_router(event_times.router)
app.include_router(leaderboard.router)

# adds pagination for datatables in angular
add_pagination(app)