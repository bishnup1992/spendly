import sqlite3

import pytest

from database.db import get_db, init_db, seed_db

CATEGORIES = {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    return path


def test_get_db_returns_row_factory_and_foreign_keys_on(tmp_path):
    conn = get_db(tmp_path / "fk.db")
    try:
        assert conn.row_factory is sqlite3.Row
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


def test_init_db_creates_tables(db_path):
    conn = get_db(db_path)
    try:
        tables = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()
    assert {"users", "expenses"} <= tables


def test_init_db_is_idempotent(db_path):
    conn = get_db(db_path)
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES ('A', 'a@x.com', 'h')"
        )
        conn.commit()
    finally:
        conn.close()

    init_db(db_path)  # must not raise or drop existing data

    conn = get_db(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()
    assert count == 1


def test_duplicate_email_raises(db_path):
    conn = get_db(db_path)
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES ('A', 'a@x.com', 'h')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES ('B', 'a@x.com', 'h')"
            )
    finally:
        conn.close()


def test_expense_with_invalid_user_id_raises(db_path):
    conn = get_db(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date) "
                "VALUES (999, 1.0, 'Food', '2026-01-01')"
            )
    finally:
        conn.close()


def test_seed_db_creates_hashed_demo_user_and_eight_expenses(db_path):
    seed_db(db_path)
    conn = get_db(db_path)
    try:
        user = conn.execute(
            "SELECT id, name, password_hash FROM users WHERE email = ?",
            ("demo@spendly.com",),
        ).fetchone()
        expenses = conn.execute(
            "SELECT category, date, amount FROM expenses WHERE user_id = ?",
            (user["id"],),
        ).fetchall()
    finally:
        conn.close()

    assert user is not None
    assert user["name"] == "Demo User"
    assert user["password_hash"] != "demo123"  # stored hashed, not plaintext

    assert len(expenses) == 8
    assert {row["category"] for row in expenses} == CATEGORIES
    assert all(isinstance(row["amount"], float) for row in expenses)


def test_seed_db_dates_are_in_current_month(db_path):
    from datetime import date

    seed_db(db_path)
    prefix = date.today().strftime("%Y-%m-")
    conn = get_db(db_path)
    try:
        dates = [row["date"] for row in conn.execute("SELECT date FROM expenses")]
    finally:
        conn.close()
    assert all(d.startswith(prefix) and len(d) == 10 for d in dates)


def test_seed_db_is_safe_to_rerun(db_path):
    seed_db(db_path)
    seed_db(db_path)
    conn = get_db(db_path)
    try:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        expenses = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    finally:
        conn.close()
    assert users == 1
    assert expenses == 8
