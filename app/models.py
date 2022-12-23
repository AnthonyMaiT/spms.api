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
    role_type_id = Column(Integer, ForeignKey("roleTypes.id", ondelete='SET NULL'))
    created_at = Column(TIMESTAMP(timezone = True), nullable = False, server_default=text('now()'))
    edited_at = Column(TIMESTAMP(timezone=True))

    # references role (does not store in db)
    role_type = relationship("RoleType")