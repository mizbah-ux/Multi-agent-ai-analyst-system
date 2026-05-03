from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

from jose import jwt, JWTError

from sqlalchemy.orm import Session

from services.db_service import SessionLocal

from models.schemas import User

from auth.security import (
    SECRET_KEY,
    ALGORITHM
)

security = HTTPBearer()


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