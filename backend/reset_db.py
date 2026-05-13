#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.db_service import SessionLocal, engine
from models.schemas import Base, User
from auth.security import hash_password

def reset_database():
    """Reset database and create a fresh test user"""
    print("Resetting database...")
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("Dropped all tables")
    
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    print("Created all tables")
    
    # Create a test user
    db = SessionLocal()
    try:
        # Use very short passwords to avoid bcrypt issues
        test_user = User(
            email="admin@test.com",
            hashed_password=hash_password("admin"),
            role="admin"
        )
        db.add(test_user)
        
        regular_user = User(
            email="user@test.com", 
            hashed_password=hash_password("user"),
            role="user"
        )
        db.add(regular_user)
        
        db.commit()
        print("Created test users:")
        print("- admin@test.com / admin")
        print("- user@test.com / user")
        
    except Exception as e:
        print(f"Error creating users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
