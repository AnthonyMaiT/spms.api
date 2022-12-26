# defines the models of the tabels inside app
from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, text
from app.database import Base
from sqlalchemy.orm import relationship

# role table for users
class RoleType(Base):
    # sets table name of model inside db
    __tablename__ = 'roleTypes'
    # columns inside the table
    id = Column(Integer,primary_key = True, nullable=False)
    role_type = Column(String, unique = True, nullable = False)

# users table
class User(Base):
    # sets table name inside db
    __tablename__ = 'users'
    # columns inside the table
    id = Column(Integer, primary_key= True, nullable = False)
    username = Column(String, nullable= False, unique=True)
    password = Column(String,nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    grade = Column(Integer)
    role_type_id = Column(Integer, ForeignKey("roleTypes.id", ondelete='SET NULL'))
    created_at = Column(TIMESTAMP(timezone = True), nullable = False, server_default=text('now()'))
    edited_at = Column(TIMESTAMP(timezone=True))

    # references role (does not store in db)
    role_type = relationship("RoleType")

# Quarters table
class Quarter(Base):
    # sets table name inside db
    __tablename__ = 'quarters'
    # columns inside the table
    id = Column(Integer, primary_key = True, nullable=False)
    quarter = Column(String, unique=True, nullable=False)

# Quarter Range Table (defines how long a quarter is)
class Quarter_Range(Base):
    # sets table name to quarter-ranges
    __tablename__ = 'quarter-ranges'
    # columns inside the table
    id = Column(Integer, primary_key = True, nullable= False)
    start_range = Column(TIMESTAMP(timezone=True), nullable=False)
    end_range = Column(TIMESTAMP(timezone=True), nullable=False)
    quarter_id = Column(Integer, ForeignKey("quarters.id", ondelete='CASCADE'), nullable=False)
    # references quarter table above
    quarter = relationship("Quarter")

# Events Table
class Events(Base):
    # sets table name to events
    __tablename__ = 'events'
    # columns inside the table
    id = Column(Integer, nullable=False, primary_key= True)
    name = Column(String, nullable = False, unique = True)
    is_sport = Column(Boolean, nullable = False)

# Student Points Table
class StudentPoint(Base):
    # sets table name to student_points
    __tablename__ = 'student_points'
    # columns inside the table
    id = Column(Integer, primary_key = True, nullable=False)
    attended_at = Column(TIMESTAMP(timezone=True), nullable = False, server_default=text('now()'))
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    quarter_range_id = Column(Integer, ForeignKey("quarter-ranges.id", ondelete='CASCADE'), nullable = False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete='CASCADE'), nullable =False)
    # references users, quarter_range, and events table above.
    user = relationship("User")
    quarter_range = relationship("Quarter_Range")
    event = relationship("Events")

# Prizes table
class Prize(Base):
    # sets table name to prizes
    __tablename__ = 'prizes'
    # columns inside the table
    id = Column(Integer, primary_key = True, nullable = False)
    name = Column(String, nullable = False, unique= True)
    level = Column(Integer, nullable = False)