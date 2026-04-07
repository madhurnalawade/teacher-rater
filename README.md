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
- `PUT /api/professors/{professor_id}` - Edit professor (admin only)
- `DELETE /api/professors/{professor_id}` - Delete professor (admin only)
- `GET /api/professors/{professor_id}` - Professor details + reviews
- `POST /api/professors/{professor_id}/reviews` - Add review (requires sign-in and username)
- `DELETE /api/reviews/{review_id}` - Soft-delete review (review owner or admin)

`POST /api/professors` accepts optional `photo_url` (http(s) or `/...`) so admins can attach a teacher photo.

## Notes

- Each signed-in user can submit one review per professor.
- Users must pick a unique username (3-15 characters, letters/numbers/underscore, no explicit language) before posting reviews.
- Reviewer emails are only returned to the admin account.
- Non-admin users do not see the add-professor form.
- Admins can attach a teacher photo URL when creating a professor.
- Admins can edit professor records without removing existing reviews.
- Deleted reviews are hidden from regular users; admins can still see them in a grayscale style.
- Explicit words in review text are masked for non-admin users; admins see uncensored text.
- Tables are created automatically on app start for this MVP.
- For production, use Alembic migrations and a managed PostgreSQL instance.

## Deploy On Vercel

This project is now configured for Vercel using:

- `api/index.py` as the serverless entrypoint
- `vercel.json` to route all requests to FastAPI

### 1. Push to GitHub

Commit and push this project to GitHub.

### 2. Import in Vercel

- Go to Vercel dashboard
- Import your GitHub repository
- Keep the root directory as project root

### 3. Set Environment Variables in Vercel

Set these in Project Settings -> Environment Variables:

- `APP_NAME=Teacher Rating`
- `DEBUG=false`
- `SECRET_KEY=<long-random-secret>`
- `GOOGLE_CLIENT_ID=<your-google-client-id>`
- `GOOGLE_CLIENT_SECRET=<your-google-client-secret>`
- `GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration`
- `ADMIN_EMAIL=<your-admin-google-email>`
- `FRONTEND_ORIGIN=https://<your-vercel-domain>`

Database:

- Recommended: set `DATABASE_URL` to managed Postgres (Neon, Supabase, Vercel Postgres, etc.)
- If `DATABASE_URL` is left as local sqlite, Vercel will use `/tmp/teacher_rating.db` (ephemeral, not persistent)

### 4. Update Google OAuth Redirect URI

In Google Cloud Console OAuth client settings, add:

- `https://<your-vercel-domain>/auth/callback`

Keep your local URI too if you still develop locally:

- `http://localhost:8000/auth/callback`

### 5. Deploy

Trigger deployment from Vercel dashboard or by pushing to your main branch.

