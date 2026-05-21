from fastapi import APIRouter, HTTPException, Depends

from sqlalchemy.orm import Session

from services.db_service import SessionLocal

from models.schemas import User

from auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)
from auth.dependencies import get_optional_user
from auth.dependencies import verify_internal_key
from jose import JWTError, jwt
from auth.dependencies import SECRET_KEY, ALGORITHM

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
        raise HTTPException(status_code=401, detail="Invalid credentials")

    valid = verify_password(
        data["password"],
        user.hashed_password
    )

    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ CREATE TOKENS
    access_token = create_access_token({
        "user_id": user.id,
        "role": user.role
    })

    refresh_token = create_refresh_token({
        "user_id": user.id
    })

    # ✅ SAVE REFRESH TOKEN
    user.refresh_token = refresh_token
    user_role = user.role
    db.commit()
    db.close()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": user_role 
    }
    
@router.post("/refresh")
def refresh_token(data: dict):

    token = data.get("refresh_token")

    if not token:
        raise HTTPException(status_code=400, detail="Missing refresh token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("user_id")

        db: Session = SessionLocal()

        user = db.query(User).filter(User.id == user_id).first()

        if not user or user.refresh_token != token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = create_access_token({
            "user_id": user.id,
            "role": user.role
        })

        return {
            "access_token": new_access_token
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
