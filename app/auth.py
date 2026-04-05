from authlib.integrations.starlette_client import OAuth

from app.config import settings


oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url=settings.google_discovery_url,
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    client_kwargs={"scope": "openid email profile"},
)


def google_oauth_ready() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret)


def get_google_client():
    return oauth.create_client("google")
