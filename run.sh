#!/bin/sh
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
fi
python scripts/seed.py
python scripts/make_assets.py
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
