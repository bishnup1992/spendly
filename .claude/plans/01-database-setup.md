# Plan: 01 — Database Setup

## Context
Step 1 of Spendly replaces the `database/db.py` stub with a working SQLite layer and wires it into `app.py` startup. Spec: `.claude/specs/01-database-setup.md`.

**Important finding:** the earlier implementation from this session (`database/db.py`, `tests/test_db.py`) is NOT on disk. `git status` shows `database/__init__.py` and `database/db.py` as deleted, and `database/` and `tests/` are empty. It must be re-implemented. The earlier version also diverged from the spec (see "Corrections" below), so rebuild against the spec rather than restoring it.

Branch: `feature/database-setup` (already created).

## Files to change
| File | Change |
|---|---|
| `database/__init__.py` | Restore (empty) — it is tracked in HEAD and was deleted |
| `database/db.py` | Implement `get_db()`, `init_db()`, `seed_db()` |
| `app.py` | Import helpers; run `init_db()` + `seed_db()` inside `app.app_context()` at startup |
| `tests/test_db.py` | New tests (pytest) |

No template, route, `requirements.txt` or `.gitignore` changes (`*.db` is already ignored at `.gitignore:9`).

## Implementation (`database/db.py`)
- `get_db()` — no required args; opens `spendly.db` in the project root, sets `row_factory = sqlite3.Row`, runs `PRAGMA foreign_keys = ON`, returns the connection. An optional `path` argument is acceptable for tests as long as the default is the root DB.
- `init_db()` — `CREATE TABLE IF NOT EXISTS` for:
  - `users`: `id` INTEGER PK AUTOINCREMENT, `name` TEXT NOT NULL, `email` TEXT NOT NULL UNIQUE, `password_hash` TEXT NOT NULL, `created_at` TEXT DEFAULT `datetime('now')`
  - `expenses`: `id` INTEGER PK AUTOINCREMENT, `user_id` INTEGER NOT NULL FK → `users(id)`, `amount` REAL NOT NULL, `category` TEXT NOT NULL, `date` TEXT NOT NULL (YYYY-MM-DD), `description` TEXT, `created_at` TEXT DEFAULT `datetime('now')`
  - Safe to call repeatedly.
- `seed_db()` — return early if `users` already has any rows (spec's guard; not an email lookup). Otherwise insert:
  - Demo user: "Demo User", `demo@spendly.com`, `generate_password_hash("demo123")` (`from werkzeug.security import generate_password_hash` — spec line 150 has a mangled import).
  - **8 expenses** across the current month, covering the fixed category list: Food, Transport, Bills, Health, Entertainment, Shopping, Other (7 categories → one category used twice so every category appears at least once). Build dates from today's year/month.
- All SQL parameterized (`?`); no f-strings in SQL. Use `executemany` for the expenses.

## Corrections vs. the lost version
- Seed 8 expenses, not 5; use the spec category list ("Bills", not "Utilities"); dates in the current month, not hardcoded.
- Seed guard = "users table non-empty", not an email check.
- Add the `app.py` startup wiring (the earlier version deliberately skipped it).

## `app.py`
Add `from database.db import get_db, init_db, seed_db` and, after `app = Flask(__name__)`:
```python
with app.app_context():
    init_db()
    seed_db()
```
Leave all routes and `port=5001` untouched. Do not implement any stub route.

## Tests (`tests/test_db.py`)
Use `tmp_path` DBs (via the optional `path` arg or monkeypatching the DB path) so the real `spendly.db` is never touched. Cover: row factory + FK pragma on; both tables created; `init_db` idempotent; duplicate email raises `IntegrityError`; expense with nonexistent `user_id` raises `IntegrityError`; seed creates 1 hashed demo user and 8 expenses spanning all 7 categories; seed twice → no duplicates.

## Verification
1. Delegate to a subagent (CLAUDE.md policy): run `venv\Scripts\python.exe -m pytest -v` (bare `pytest` is not on PATH here) and report counts and any tracebacks.
2. Start the app (`venv\Scripts\python.exe app.py`), confirm no startup errors on port 5001, `spendly.db` is created, and restarting does not duplicate seed data.
3. Inspect the DB with a short `sqlite3` query: 2 tables, 1 user whose `password_hash` is not `demo123`, 8 expenses.
4. Confirm `git status` shows only the four files above (+ `.claude/` / `CLAUDE.md` untracked as before).

## Notes
- The requested save location `.claude/plans/01-database-setup.md` could not be written in plan mode; copy this file there as the first step after approval.
- Nothing is committed until the user asks.
