# DraftFlow

DraftFlow is a React/TypeScript publishing app backed by FastAPI, SQLAlchemy, and PostgreSQL.

## Local development

1. Install frontend dependencies with `npm install`.
2. Install backend dependencies with `python -m pip install -r backend/requirements.txt`.
3. Create a PostgreSQL database and configure `backend/.env` from `backend/.env.example`.
4. Apply the database migrations:

   ```powershell
   Set-Location backend
   alembic upgrade head
   Set-Location ..
   ```

5. Start the backend and frontend in separate terminals:

   ```powershell
   Set-Location backend
   python server.py
   ```

   ```powershell
   npm run dev
   ```

The API listens on port `8000`; Vite proxies `/api` requests to it. The frontend uses the same-origin `/api/v1` and `/api` paths by default. Set `VITE_API_URL=https://api.example.com/api/v1` in `src/.env.local` if the API is on a separate origin; a bare API origin is also accepted and normalized to `/api/v1`.

## Production deployment

Use [backend/.env.production.example](./backend/.env.production.example) as a checklist, not as a file to deploy unchanged. Configure secrets through the hosting provider's secret manager:

- `ENVIRONMENT=production`
- `DATABASE_URL` for a managed PostgreSQL database, with TLS enabled
- A unique cryptographically random `JWT_SECRET_KEY` of at least 32 characters
- `CORS_ORIGINS` as a comma-separated list of explicit HTTPS frontend origins (no wildcard)
- `FRONTEND_URL` as the canonical HTTPS frontend origin
- `SMTP_HOST`, `SMTP_PORT`, and `SMTP_FROM_EMAIL` for password-reset email; supply SMTP credentials when required by the provider
- `GOOGLE_CLIENT_ID` and the production frontend origin in the Google OAuth authorized JavaScript origins, if Google sign-in is enabled
- `VITE_API_URL` at frontend build time only when the API uses a separate origin

Back up the database before upgrading. Run `alembic upgrade head` from `backend` as a release step before deploying the new API. These migrations add compatibility columns and tables and do not replace the existing users, posts, or comments. They are intentionally forward-only because dropping migrated data is not a safe rollback. Check `GET /api/health` after deployment and restore from the pre-migration backup if the release must be rolled back.

When frontend and API share a host, configure the reverse proxy to serve the frontend and forward `/api/*` to FastAPI. For a separate API host, set `VITE_API_URL` during the frontend build and list the frontend origin in `CORS_ORIGINS`. Never commit `.env` files, production credentials, or OAuth client secrets.

## API

- `GET /api/health`
- `POST /api/auth` for email/password signup and login; `POST /api/auth/google` for Google sign-in
- `POST /api/auth/password/forgot` and `POST /api/auth/password/reset`
- `GET /api/posts` for the feed and `/api/v1/posts/*` for authenticated post interactions
- `GET`/`PUT /api/profile`

Schema changes are managed with Alembic. The API does not create or seed production tables automatically.
