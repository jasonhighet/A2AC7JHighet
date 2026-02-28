"""
db/run_migrations.py
--------------------
Applies pending SQL migrations in order.

Usage:
    uv run python db/run_migrations.py

Migrations are stored as plain .sql files in db/migrations/, named with a
numeric prefix (e.g. 001_create_applications.sql). This script:
  1. Creates a _migrations tracking table if it doesn't exist.
  2. Reads all .sql files in order.
  3. Runs any migration that hasn't been recorded in _migrations.
"""

import os
import sys
from pathlib import Path

import psycopg2

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Fall back to reading .env manually (keeps this script dependency-free)
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    database_url = line.split("=", 1)[1]
                    break
    if not database_url:
        print("ERROR: DATABASE_URL not set. Copy .env.example to .env and configure it.")
        sys.exit(1)
    return psycopg2.connect(database_url)


def ensure_migrations_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS _migrations (
                filename   VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
            """
        )
    conn.commit()


def get_applied(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM _migrations")
        return {row[0] for row in cur.fetchall()}


def apply_migration(conn, path: Path):
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "INSERT INTO _migrations (filename) VALUES (%s)",
            (path.name,),
        )
    conn.commit()


def main():
    conn = get_connection()
    try:
        ensure_migrations_table(conn)
        applied = get_applied(conn)

        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        if not migration_files:
            print("No migration files found.")
            return

        ran = 0
        for path in migration_files:
            if path.name in applied:
                print(f"  skip  {path.name}")
            else:
                print(f"  apply {path.name} ... ", end="", flush=True)
                apply_migration(conn, path)
                print("done")
                ran += 1

        print(f"\n{ran} migration(s) applied.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
