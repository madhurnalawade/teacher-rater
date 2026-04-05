from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.access import is_admin_user
from app.config import settings
from app.db import get_db
from app.models import User


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        return None

    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in with Google to continue.",
        )
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not (settings.admin_email.strip() or settings.admin_google_sub.strip()):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin account is not configured. Set ADMIN_EMAIL or ADMIN_GOOGLE_SUB in .env.",
        )

    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the admin account can add professors.",
        )

    return current_user
