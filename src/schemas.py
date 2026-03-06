"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models import RoleEnum


class UserBase(BaseModel):
    """Base user schema"""
    email: str
    username: str


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    role: RoleEnum
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityBase(BaseModel):
    """Base activity schema"""
    name: str
    description: str
    schedule: str
    max_participants: int


class ActivityCreate(ActivityBase):
    """Schema for activity creation"""
    pass


class ActivityResponse(ActivityBase):
    """Schema for activity response"""
    id: int
    created_at: datetime
    enrolled_count: int = 0

    class Config:
        from_attributes = True


class ActivityDetailResponse(ActivityResponse):
    """Detailed activity response with enrolled users"""
    enrolled_users: List[UserResponse] = []

    class Config:
        from_attributes = True


class EnrollmentResponse(BaseModel):
    """Schema for enrollment response"""
    activity_id: int
    user_id: int
    enrolled_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str


class ErrorResponse(BaseModel):
    """Schema for error response"""
    detail: str
