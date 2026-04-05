# Teacher Rating

Python app starter that lets users sign in with Google, rate professors from 1-5 stars, and leave text reviews.

## Stack

- FastAPI for the backend and routing
- SQLAlchemy for models and data access
- Authlib for Google OAuth 2.0 + OpenID Connect
- Jinja2 templates + vanilla JS for the initial frontend
- SQLite by default (easy local setup), PostgreSQL ready via `DATABASE_URL`

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment file:

   ```bash
   cp .env.example .env
   ```

4. Set Google OAuth credentials in `.env`:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

Also set your admin identity so only you can add professors:

- `ADMIN_EMAIL` (recommended)
- or `ADMIN_GOOGLE_SUB`

Create credentials in Google Cloud Console and add this redirect URI:

- `http://localhost:8000/auth/callback`

5. Run the app:

   ```bash
   uvicorn app.main:app --reload
   ```

6. Open:

- `http://localhost:8000`

## API Overview

- `GET /auth/login` - Start Google sign-in
- `GET /auth/callback` - Google callback
- `POST /auth/logout` - Log out
- `GET /api/me` - Current signed-in user
- `POST /api/me/username` - Set or update your public username
- `GET /api/professors` - List professors with average rating and count
- `POST /api/professors` - Add professor (admin only)
- `DELETE /api/professors/{professor_id}` - Delete professor (admin only)
- `GET /api/professors/{professor_id}` - Professor details + reviews
- `POST /api/professors/{professor_id}/reviews` - Add review (requires sign-in and username)
- `DELETE /api/reviews/{review_id}` - Delete review (admin only)

`POST /api/professors` accepts optional `photo_url` (http(s) or `/...`) so admins can attach a teacher photo.

## Notes

- Each signed-in user can submit one review per professor.
- Users must pick a unique username (3-15 characters, letters/numbers/underscore, no explicit language) before posting reviews.
- Reviewer emails are only returned to the admin account.
- Non-admin users do not see the add-professor form.
- Admins can attach a teacher photo URL when creating a professor.
- Tables are created automatically on app start for this MVP.
- For production, use Alembic migrations and a managed PostgreSQL instance.
