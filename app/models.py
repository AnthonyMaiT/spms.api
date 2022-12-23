from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, text
from app.database import Base
from sqlalchemy.orm import relationship

class RoleType(Base):
    __tablename__ = 'roleTypes'

    id = Column(Integer,primary_key = True, nullable=False)
    role_type = Column(String, unique = True, nullable = False)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key= True, nullable = False)
    username = Column(String, nullable= False, unique=True)
    password = Column(String,nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role_type_id = Column(Integer, ForeignKey("roleTypes.id", ondelete='SET NULL'))
    created_at = Column(TIMESTAMP(timezone = True), nullable = False, server_default=text('now()'))
    edited_at = Column(TIMESTAMP(timezone=True))

    role_type = relationship("RoleType")