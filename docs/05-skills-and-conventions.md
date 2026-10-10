# Skills and conventions

## Local setup

From the repo root:

```bash
docker compose up -d
copy .env.example .env
```

Fill `JWT_SECRET` and the three `SEED_*_PASSWORD` values in `.env`. Do not commit `.env`.

Backend (from `backend/`):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
pytest
```

Frontend (from `frontend/`):

```bash
npm install
npm start
```

`npm start` serves on port 4200 and uses `proxy.conf.json`.

## Conventions

- API changes ship with pytest coverage in the same change.
- Schema changes ship with an Alembic revision. Do not edit a migration that has already been applied anywhere shared.
- Feature work updates the matching `docs/*.md` file, including `docs/06-follow-ups-and-roadmap.md` when a question or debt item appears.
- Cursor rules in `.cursor/rules/` must match the decisions in `docs/01-architecture.md` and `docs/04-coding-standards.md`.

## Seed accounts

Emails default to `admin@example.com`, `manager@example.com`, and `employee@example.com`. Passwords are whatever you set in `.env`. The seed skips emails that already exist. Addresses use `example.com` because Pydantic `EmailStr` rejects the reserved `.local` suffix.
