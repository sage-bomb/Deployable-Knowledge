from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from core.db import SessionLocal, User


class UserInfo(BaseModel):
    id: str
    email: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserInfo])
def list_users():
    """Return all users."""
    with SessionLocal() as db:
        users = db.query(User).all()
        return [UserInfo.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserInfo)
def get_user(user_id: str):
    """Return a single user by identifier."""
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="user not found")
        return UserInfo.model_validate(user)
