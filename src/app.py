"""
High School Management System API

A production-ready FastAPI application for managing student activities at Mergington High School
with persistent storage, authentication, and role-based access control.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import os
from pathlib import Path
from contextlib import asynccontextmanager

from database import init_db, get_db
from models import User, Activity, RoleEnum
from auth import (
    hash_password, verify_password, create_access_token, get_current_user,
    require_role, ACCESS_TOKEN_EXPIRE_MINUTES
)
from schemas import (
    UserCreate, UserResponse, ActivityCreate, ActivityResponse, 
    ActivityDetailResponse, TokenResponse
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield


app = FastAPI(
    title="Mergington High School API",
    description="API for managing extracurricular activities with authentication and authorization",
    version="1.0.0",
    lifespan=lifespan
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/v1/auth/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account (students only)"""
    
    # Check if email/username already exists
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Create new user (default to STUDENT role)
    hashed_password = hash_password(user.password)
    new_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role=RoleEnum.STUDENT
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/api/v1/auth/token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    
    # Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/auth/me", response_model=UserResponse)
def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current logged-in user information"""
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ============================================================================
# Activity Endpoints (Public)
# ============================================================================

@app.get("/")
def root():
    """Redirect to static index.html"""
    return RedirectResponse(url="/static/index.html")


@app.get("/api/v1/activities", response_model=list[ActivityResponse])
def get_activities(db: Session = Depends(get_db)):
    """Get all activities (public endpoint)"""
    activities = db.query(Activity).all()
    result = []
    for activity in activities:
        enrolled_count = len(activity.enrolled_users)
        result.append(ActivityResponse(
            id=activity.id,
            name=activity.name,
            description=activity.description,
            schedule=activity.schedule,
            max_participants=activity.max_participants,
            created_at=activity.created_at,
            enrolled_count=enrolled_count
        ))
    return result


@app.get("/api/v1/activities/{activity_id}", response_model=ActivityDetailResponse)
def get_activity_detail(activity_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return ActivityDetailResponse(
        id=activity.id,
        name=activity.name,
        description=activity.description,
        schedule=activity.schedule,
        max_participants=activity.max_participants,
        created_at=activity.created_at,
        enrolled_count=len(activity.enrolled_users),
        enrolled_users=[
            UserResponse(
                id=u.id,
                email=u.email,
                username=u.username,
                role=u.role,
                created_at=u.created_at
            )
            for u in activity.enrolled_users
        ]
    )


# ============================================================================
# Activity Management Endpoints (Organizer/Admin only)
# ============================================================================

@app.post("/api/v1/activities", response_model=ActivityResponse)
def create_activity(
    activity: ActivityCreate,
    current_user: dict = Depends(require_role([RoleEnum.ORGANIZER, RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """Create a new activity (organizer/admin only)"""
    
    # Check if activity name already exists
    existing_activity = db.query(Activity).filter(Activity.name == activity.name).first()
    if existing_activity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity with this name already exists"
        )
    
    new_activity = Activity(
        name=activity.name,
        description=activity.description,
        schedule=activity.schedule,
        max_participants=activity.max_participants
    )
    
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    
    return ActivityResponse(
        id=new_activity.id,
        name=new_activity.name,
        description=new_activity.description,
        schedule=new_activity.schedule,
        max_participants=new_activity.max_participants,
        created_at=new_activity.created_at,
        enrolled_count=0
    )


@app.patch("/api/v1/activities/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: int,
    activity_update: ActivityCreate,
    current_user: dict = Depends(require_role([RoleEnum.ORGANIZER, RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update an activity (organizer/admin only)"""
    
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    activity.name = activity_update.name
    activity.description = activity_update.description
    activity.schedule = activity_update.schedule
    activity.max_participants = activity_update.max_participants
    
    db.commit()
    db.refresh(activity)
    
    return ActivityResponse(
        id=activity.id,
        name=activity.name,
        description=activity.description,
        schedule=activity.schedule,
        max_participants=activity.max_participants,
        created_at=activity.created_at,
        enrolled_count=len(activity.enrolled_users)
    )


# ============================================================================
# Enrollment Endpoints
# ============================================================================

@app.post("/api/v1/activities/{activity_id}/enroll")
def enroll_in_activity(
    activity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enroll current user in an activity"""
    
    # Get current user
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get activity
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check if already enrolled
    if user in activity.enrolled_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already enrolled in this activity"
        )
    
    # Check capacity
    if len(activity.enrolled_users) >= activity.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity is at full capacity"
        )
    
    # Add enrollment
    activity.enrolled_users.append(user)
    db.commit()
    
    return {"message": f"Successfully enrolled in {activity.name}"}


@app.delete("/api/v1/activities/{activity_id}/enroll")
def unenroll_from_activity(
    activity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unenroll current user from an activity"""
    
    # Get current user
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get activity
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check if enrolled
    if user not in activity.enrolled_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not enrolled in this activity"
        )
    
    # Remove enrollment
    activity.enrolled_users.remove(user)
    db.commit()
    
    return {"message": f"Successfully unenrolled from {activity.name}"}


@app.get("/api/v1/activities/{activity_id}/enrollments")
def get_activity_enrollments(
    activity_id: int,
    current_user: dict = Depends(require_role([RoleEnum.ORGANIZER, RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get list of enrollments for an activity (organizer/admin only)"""
    
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return {
        "activity_id": activity.id,
        "activity_name": activity.name,
        "total_enrolled": len(activity.enrolled_users),
        "max_participants": activity.max_participants,
        "enrolled_users": [
            UserResponse(
                id=u.id,
                email=u.email,
                username=u.username,
                role=u.role,
                created_at=u.created_at
            )
            for u in activity.enrolled_users
        ]
    }
