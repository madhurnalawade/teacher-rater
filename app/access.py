from app.config import settings
from app.models import User


def is_admin_user(user: User | None) -> bool:
    if user is None:
        return False

    admin_google_sub = settings.admin_google_sub.strip()
    if admin_google_sub and user.google_sub == admin_google_sub:
        return True

    admin_email = settings.admin_email.strip().lower()
    if admin_email and user.email.lower() == admin_email:
        return True

    return False
