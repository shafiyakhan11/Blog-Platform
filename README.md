# DraftFlow

DraftFlow is a React and TypeScript publishing workspace backed by a small Python HTTP API and PostgreSQL database.

## Run locally

Install the frontend dependencies, then use two terminals:

```powershell
npm install
python -m pip install -r backend/requirements.txt
python backend/server.py
npm run dev
```

Create a PostgreSQL database named `draftflow` before starting the API. The API runs at `http://127.0.0.1:8000`. The Vite app runs at the URL printed by `npm run dev` (normally `http://localhost:5173`). Tables are created automatically at API startup, and the existing sample posts are bootstrapped on the first frontend load.

Set `DATABASE_URL` for PostgreSQL, using [backend/.env.example](backend/.env.example) as a template. Set `VITE_API_URL` when the API is hosted elsewhere, for example `VITE_API_URL=https://api.example.com/api`.

## API surface

- `GET /api/health`, `GET /api/posts`, `GET /api/profile`
- `POST /api/posts`, `PUT /api/posts/:id`, `DELETE /api/posts/:id`
- `POST /api/posts/:id/like|bookmark|follow|share`
- `POST /api/posts/:id/comments`, `POST /api/comments/:id/like`
- `POST /api/auth`, `PUT /api/profile`

The backend uses `psycopg` for PostgreSQL connectivity. The database schema is created with PostgreSQL SQL in `backend/server.py`.
