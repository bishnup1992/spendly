import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_PATH = os.path.join(BASE_DIR, "spendly.db")


def get_db(path=DATABASE_PATH):
    """Return a SQLite connection with dict-style rows and foreign keys enabled."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path=DATABASE_PATH):
    """Create all tables if they do not already exist."""
    conn = get_db(path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                amount      REAL    NOT NULL,
                category    TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                description TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db(path=DATABASE_PATH):
    """Insert a demo user and sample expenses for development. Runs once only."""
    conn = get_db(path)
    try:
        has_users = conn.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        if has_users:
            return

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cursor.lastrowid

        # Eight expenses spread across the current month. "Food" appears twice
        # so that all seven fixed categories are covered.
        today = date.today()
        days = [1, 3, 5, 8, 10, 12, 15, 18]
        sample = [
            (45.50, "Food", "Groceries"),
            (12.00, "Transport", "Bus pass top-up"),
            (89.99, "Bills", "Internet bill"),
            (60.00, "Health", "Pharmacy"),
            (25.00, "Entertainment", "Movie night"),
            (150.00, "Shopping", "New shoes"),
            (8.75, "Other", "Miscellaneous"),
            (32.40, "Food", "Restaurant dinner"),
        ]
        rows = [
            (user_id, amount, category, f"{today.year}-{today.month:02d}-{day:02d}", description)
            for day, (amount, category, description) in zip(days, sample)
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()
