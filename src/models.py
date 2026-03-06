"""
SQLAlchemy database models for the activities management system.
"""

from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# Association table for many-to-many relationship between users and activities
enrollment_association = Table(
    'enrollments',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('activity_id', Integer, ForeignKey('activities.id'), primary_key=True),
    Column('enrolled_at', DateTime, default=datetime.utcnow)
)


class RoleEnum(str, enum.Enum):
    """User roles in the system"""
    STUDENT = "student"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.STUDENT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    activities = relationship(
        "Activity",
        secondary=enrollment_association,
        back_populates="enrolled_users"
    )


class Activity(Base):
    """Activity model for extracurricular activities"""
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=False)
    schedule = Column(String, nullable=False)
    max_participants = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    enrolled_users = relationship(
        "User",
        secondary=enrollment_association,
        back_populates="activities"
    )
