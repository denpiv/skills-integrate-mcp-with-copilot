"""
Database seed script to populate initial activities and test users.
Run this script to initialize the database with demo data.
"""

from database import SessionLocal, engine
from models import Base, User, Activity, RoleEnum
from auth import hash_password

# Create all tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Check if data already exists
if db.query(User).count() == 0:
    print("Seeding database with initial data...")
    
    # Create test users
    admin_user = User(
        email="admin@mergington.edu",
        username="admin",
        hashed_password=hash_password("admin123"),
        role=RoleEnum.ADMIN
    )
    
    organizer_user = User(
        email="organizer@mergington.edu",
        username="organizer",
        hashed_password=hash_password("organizer123"),
        role=RoleEnum.ORGANIZER
    )
    
    # Create sample students
    students = [
        User(
            email="michael@mergington.edu",
            username="michael",
            hashed_password=hash_password("student123"),
            role=RoleEnum.STUDENT
        ),
        User(
            email="emma@mergington.edu",
            username="emma",
            hashed_password=hash_password("student123"),
            role=RoleEnum.STUDENT
        ),
        User(
            email="john@mergington.edu",
            username="john",
            hashed_password=hash_password("student123"),
            role=RoleEnum.STUDENT
        ),
    ]
    
    db.add(admin_user)
    db.add(organizer_user)
    for student in students:
        db.add(student)
    
    db.commit()
    
    # Create activities
    activities = [
        Activity(
            name="Chess Club",
            description="Learn strategies and compete in chess tournaments",
            schedule="Fridays, 3:30 PM - 5:00 PM",
            max_participants=12
        ),
        Activity(
            name="Programming Class",
            description="Learn programming fundamentals and build software projects",
            schedule="Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            max_participants=20
        ),
        Activity(
            name="Gym Class",
            description="Physical education and sports activities",
            schedule="Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            max_participants=30
        ),
        Activity(
            name="Soccer Team",
            description="Join the school soccer team and compete in matches",
            schedule="Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            max_participants=22
        ),
        Activity(
            name="Basketball Team",
            description="Practice and play basketball with the school team",
            schedule="Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            max_participants=15
        ),
        Activity(
            name="Art Club",
            description="Explore your creativity through painting and drawing",
            schedule="Thursdays, 3:30 PM - 5:00 PM",
            max_participants=15
        ),
        Activity(
            name="Drama Club",
            description="Act, direct, and produce plays and performances",
            schedule="Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            max_participants=20
        ),
        Activity(
            name="Math Club",
            description="Solve challenging problems and participate in math competitions",
            schedule="Tuesdays, 3:30 PM - 4:30 PM",
            max_participants=10
        ),
        Activity(
            name="Debate Team",
            description="Develop public speaking and argumentation skills",
            schedule="Fridays, 4:00 PM - 5:30 PM",
            max_participants=12
        ),
    ]
    
    for activity in activities:
        db.add(activity)
    
    db.commit()
    
    # Add some sample enrollments
    chess_club = db.query(Activity).filter(Activity.name == "Chess Club").first()
    programming = db.query(Activity).filter(Activity.name == "Programming Class").first()
    michael = db.query(User).filter(User.username == "michael").first()
    emma = db.query(User).filter(User.username == "emma").first()
    
    if chess_club and michael:
        chess_club.enrolled_users.append(michael)
    if programming and emma:
        programming.enrolled_users.append(emma)
    
    db.commit()
    
    print("✅ Database seeded successfully!")
    print("\nTest credentials:")
    print("  Admin: username=admin, password=admin123")
    print("  Organizer: username=organizer, password=organizer123")
    print("  Student: username=michael, password=student123")
else:
    print("Database already contains data, skipping seed.")

db.close()
