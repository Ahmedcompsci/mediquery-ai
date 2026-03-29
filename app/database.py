"""
database.py — SQLite connection and schema initialization
=========================================================
Uses a single SQLite file for portability.
Swap DATABASE_URL environment variable for PostgreSQL or MySQL in production.

Table: patients
    id          — primary key
    name        — full name
    age         — integer age
    diagnosis   — free-text diagnosis string
    admitted    — ISO date string (YYYY-MM-DD)
    discharged  — ISO date string or NULL if still admitted
    department  — hospital department name
    status      — 'admitted' or 'discharged'
"""

import sqlite3
import os

# ── Config ────────────────────────────────────────────────────────────────────

DB_PATH = os.getenv("DB_PATH", "mediquery.db")


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row factory enabled for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows accessible as dicts
    return conn


def init_db():
    """
    Create the patients table and seed sample data if it doesn't exist.
    Called once at application startup.
    """
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            age         INTEGER NOT NULL,
            diagnosis   TEXT    NOT NULL,
            admitted    TEXT    NOT NULL,
            discharged  TEXT,
            department  TEXT    NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'admitted'
        );

        -- Seed only if table is empty
        INSERT INTO patients (name, age, diagnosis, admitted, discharged, department, status)
        SELECT * FROM (VALUES
            ('Alice Chen',     34, 'Hypertension',    '2026-02-15', '2026-02-20', 'Cardiology',     'discharged'),
            ('James Rivera',   67, 'Type 2 Diabetes', '2026-02-28', NULL,          'Endocrinology',  'admitted'),
            ('Sara Okafor',    52, 'Pneumonia',        '2026-03-01', '2026-03-07', 'Pulmonology',    'discharged'),
            ('Tom Nguyen',     45, 'Appendicitis',     '2026-03-10', '2026-03-12', 'Surgery',        'discharged'),
            ('Maria Lopez',    29, 'Asthma',           '2026-03-15', NULL,          'Pulmonology',    'admitted'),
            ('David Kim',      71, 'Heart Failure',    '2026-03-18', NULL,          'Cardiology',     'admitted'),
            ('Fatima Hassan',  38, 'Kidney Stones',    '2026-03-20', '2026-03-22', 'Urology',        'discharged'),
            ('Chris Patel',    55, 'Hypertension',     '2026-03-21', NULL,          'Cardiology',     'admitted'),
            ('Nora Williams',  63, 'Type 2 Diabetes',  '2026-03-22', NULL,          'Endocrinology',  'admitted'),
            ('Eli Jordan',     44, 'Back Pain',        '2026-03-25', NULL,          'Orthopedics',    'admitted')
        ) WHERE NOT EXISTS (SELECT 1 FROM patients LIMIT 1);
    """)
    conn.commit()
    conn.close()
