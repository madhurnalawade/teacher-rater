from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.access import is_admin_user
from app.config import settings
from app.db import Base, apply_mvp_schema_fixes, engine
from app.dependencies import get_optional_user
from app.models import User
from app.routers import auth, professors, users


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    apply_mvp_schema_fixes()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie_name,
    same_site="lax",
    https_only=not settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(professors.router)
app.include_router(users.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, user: User | None = Depends(get_optional_user)):
    user_payload = None
    if user is not None:
        is_admin = is_admin_user(user)
        user_payload = {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "picture": user.picture,
            "is_admin": is_admin,
        }
    else:
        is_admin = False

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "is_admin": is_admin,
            "needs_username": bool(user and not user.username),
            "user_payload": user_payload,
            "google_configured": bool(settings.google_client_id and settings.google_client_secret),
        },
    )


@app.get("/health")
def healthcheck():
    return {"status": "ok"}
