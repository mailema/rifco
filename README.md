# RIFCO — Ringim Football Coaches Organization

A Flask web application for a football coaches organization: a public
site plus three authenticated portals (Chairman, Coach, Transfer).

## Features

- **Public site** — homepage, about, leagues, teams, players, contact
- **Chairman Portal** — register/search/edit members, create and manage
  leagues and teams, view stats, open/close player-updates and
  transfers system-wide
- **Coach Portal** — register players to your own team (with photo
  upload), search/view/edit/remove your own roster only
- **Transfer Portal** — search a player by ID + current team, then
  execute a transfer to a new team, with a full audit history
- Role-based access control enforced on every route on the backend
  (not just hidden UI) — verified with an automated route test, see
  below
- Works against SQLite out of the box for local development, and
  against Postgres/Neon in production via `DATABASE_URL`

## Quick start

```bash
cd RIFCO
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env
# Generate a real secret key:
python -c "import secrets; print(secrets.token_hex(32))"
# Paste it into .env as SECRET_KEY=...
# Leave DATABASE_URL empty to use the local SQLite fallback, or set it
# to a real Postgres/Neon connection string.

python app.py
```

Visit http://127.0.0.1:5000

The very first run creates the tables automatically (never drops
existing data). You still need an account to log in — RIFCO has no
public sign-up, by design, since every member is registered by the
Chairman. Bootstrap the first Chairman account with:

```bash
python seed.py
```

Follow the prompts, then log in at `/login`.

## Typical workflow

1. `python seed.py` → creates the first Chairman account.
2. Log in as Chairman → create a League → create a Team in that
   league → register a Member with rank "Coach" and assign them to
   that team → also register a Member with rank "Transfer Committee"
   (no team assignment needed for this rank).
3. Log out, log in as that Coach → register players to the team.
4. Back as Chairman → open "Transfers" under System Controls.
5. Log out, log in as the Transfer Committee member → use the
   Transfer Portal (this rank is the only one with access — see
   `routes/decorators.py`) to move a player between teams.

## Project structure

```
RIFCO/
├── app.py                 application factory / entry point
├── config.py               environment-driven configuration
├── constants.py             centralized rank & position lists
├── extensions.py            db / login_manager instances
├── models.py                 SQLAlchemy models
├── seed.py                    bootstrap the first Chairman account
├── requirements.txt
├── .env.example
├── routes/
│   ├── decorators.py         login/chairman/coach/transfer decorators
│   ├── public.py              homepage & public pages
│   ├── auth.py                 login / logout
│   ├── chairman.py              chairman portal routes
│   ├── coach.py                  coach portal routes
│   └── transfer.py                transfer portal routes
├── templates/                  Jinja templates (see subfolders)
└── static/
    ├── css/style.css            design system (navy/green/gold)
    ├── js/main.js
    └── uploads/players/          player photo uploads
```

## Notes on decisions made while building

- **Single `models.py`** instead of a `models/` package — at this
  project's size, one file is easier to scan; splitting later is a
  safe, mechanical move if the schema grows.
- **Transfer permission is limited to a dedicated "Transfer Committee"
  rank.** Neither the Chairman nor a Coach can access the Transfer
  Portal — each rank is confined to exactly one portal (Chairman ->
  Chairman Portal, Coach -> Coach Portal, Transfer Committee ->
  Transfer Portal). `routes/decorators.py:transfer_required` is the
  one place this is enforced, so widening it later (e.g. letting the
  Chairman in too) is a one-line change.
- **Hero background image** (`static/images/football-bg.jpg`) is
  referenced in CSS but not included — no real photo was provided.
  The hero still looks intentional without it (gradient + subtle
  pitch-line pattern); drop a stadium photo at that path to complete
  it.
- **CSRF protection** is enabled globally via Flask-WTF on every POST
  form.
- File uploads are re-named with a random UUID on save (never trust
  the client's filename) and restricted to png/jpg/jpeg/webp, 3&nbsp;MB max.

## What to check before real deployment

- Set a real `SECRET_KEY` and `DATABASE_URL` (Postgres/Neon) in the
  production environment — never commit `.env`.
- Set `FLASK_ENV=production` so cookies are marked `Secure` and debug
  mode is off.
- Run `python seed.py` once against the production database to create
  the real first Chairman account, then delete/rotate that password.
- Put the app behind a real WSGI server (gunicorn/uwsgi) — `app.run()`
  is for local development only.
