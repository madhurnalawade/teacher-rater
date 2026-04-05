from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.access import is_admin_user
from app.db import get_db
from app.dependencies import get_current_user
from app.models import User
from app.username_policy import validate_username_policy


router = APIRouter(prefix="/api", tags=["users"])


@router.get("/me", response_model=schemas.MeRead)
def me(current_user: User = Depends(get_current_user)):
    return schemas.MeRead(
        id=current_user.id,
        username=current_user.username,
        name=current_user.name,
        email=current_user.email,
        picture=current_user.picture,
        is_admin=is_admin_user(current_user),
    )


@router.post("/me/username", response_model=schemas.MeRead, status_code=status.HTTP_200_OK)
def set_username(
    payload: schemas.UsernameUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        validate_username_policy(payload.username)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    conflicting_user = db.execute(
        select(User).where(
            func.lower(User.username) == payload.username.lower(),
            User.id != current_user.id,
        )
    ).scalar_one_or_none()
    if conflicting_user is not None:
        raise HTTPException(status_code=409, detail="That username is already taken.")

    current_user.username = payload.username
    db.commit()
    db.refresh(current_user)

    return schemas.MeRead(
        id=current_user.id,
        username=current_user.username,
        name=current_user.name,
        email=current_user.email,
        picture=current_user.picture,
        is_admin=is_admin_user(current_user),
    )
