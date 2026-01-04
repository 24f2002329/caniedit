Backend APIs for CanIEdit (FastAPI)
===================================

## Quick start

1. Install dependencies
	```bash
	pip install -r requirements.txt
	```
2. Copy `.env.example` to `.env` and set a strong `AUTH_SECRET_KEY`
3. Run the API (from the repository root)
	```bash
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend --env-file backend/.env
	```

## Environment variables

- `DATABASE_URL` (optional): defaults to `sqlite:///./data/app.db`.
- `AUTH_SECRET_KEY`: secret used to sign JWTs (set a strong value in production).
- `ACCESS_TOKEN_EXPIRE_MINUTES` (optional): token TTL, defaults to `60` minutes.

Create a `.env` file in `backend/` (see `.env.example`) or export these variables before running the server.

## Auth endpoints

- `POST /api/auth/register` — create a user (email + password, optional name)
- `POST /api/auth/login` — exchange credentials for a bearer token
- `GET /api/auth/me` — get the current user (requires `Authorization: Bearer <token>`)

## Other endpoints

- `POST /api/pdf/merge` — merge uploaded PDFs
- `DELETE /api/pdf/merge/{filename}` — delete a merged PDF by filename

The server exposes temporary outputs at `/temp_outputs/<filename>`.
