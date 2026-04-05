from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from authlib.integrations.base_client import OAuthError

from app.auth import get_google_client, google_oauth_ready
from app.db import get_db
from app.models import User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    if not google_oauth_ready():
        raise HTTPException(status_code=500, detail="Google OAuth credentials are not configured.")

    google = get_google_client()
    redirect_uri = request.url_for("auth_callback")
    return await google.authorize_redirect(request, redirect_uri)


@router.get("/callback", name="auth_callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    google = get_google_client()

    try:
        token = await google.authorize_access_token(request)
    except OAuthError as error:
        raise HTTPException(status_code=400, detail=f"Google sign-in failed: {error.error}") from error

    user_info = token.get("userinfo")
    if not user_info:
        user_info = await google.parse_id_token(request, token)

    if not user_info:
        raise HTTPException(status_code=400, detail="Unable to read user profile from Google.")

    google_sub = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name") or email
    picture = user_info.get("picture")

    if not google_sub or not email:
        raise HTTPException(status_code=400, detail="Google profile response missing required fields.")

    user = db.execute(select(User).where(User.google_sub == google_sub)).scalar_one_or_none()

    if user is None:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    if user is None:
        user = User(google_sub=google_sub, email=email, name=name, picture=picture)
        db.add(user)
    else:
        user.google_sub = google_sub
        user.email = email
        user.name = name
        user.picture = picture

    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=302)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out."}


@router.get("/logout")
def logout_redirect(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)
