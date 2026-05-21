from fastapi import Depends, HTTPException ,Request
from fastapi.security import HTTPBearer
import os
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from services.db_service import SessionLocal
from models.schemas import User
from fastapi import Header
from auth.security import (
    SECRET_KEY,
    ALGORITHM
)


security = HTTPBearer()

def get_optional_user(request: Request):
    from jose import jwt, JWTError
    from services.db_service import SessionLocal
    from models.schemas import User

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None  # allow internal calls (n8n)

    try:
        token = auth_header.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if not user_id:
            return None

        db = SessionLocal()
        user = db.query(User).filter(User.id == user_id).first()
        db.close()

        return user

    except JWTError:
        return None
    
def require_role(required_role: str):

    def role_checker(user=Depends(get_current_user)):

        if user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: insufficient role"
            )

        return user

    return role_checker


def get_current_user(
    credentials=Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if not user_id:

            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        db: Session = SessionLocal()

        user = db.query(User).filter(
            User.id == user_id
        ).first()
        db.close()

        if not user:

            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        return user

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    
INTERNAL_API_KEY = "internal-secret"


def verify_internal_key(
    x_internal_key: str = Header(None)
):

    if x_internal_key != INTERNAL_API_KEY:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )
