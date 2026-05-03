from fastapi import APIRouter, HTTPException

from sqlalchemy.orm import Session

from services.db_service import SessionLocal

from models.schemas import User

from auth.security import (
    hash_password,
    verify_password,
    create_access_token
)

router = APIRouter()


@router.post("/signup")
def signup(data: dict):

    db: Session = SessionLocal()

    existing = db.query(User).filter(
        User.email == data["email"]
    ).first()

    if existing:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    user = User(
        email=data["email"],
        hashed_password=hash_password(
            data["password"]
        )
    )

    db.add(user)

    db.commit()

    return {
        "message": "User created"
    }


@router.post("/login")
def login(data: dict):

    db: Session = SessionLocal()

    user = db.query(User).filter(
        User.email == data["email"]
    ).first()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    valid = verify_password(
        data["password"],
        user.hashed_password
    )

    if not valid:

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "user_id": user.id
    })

    return {
        "access_token": token
    }