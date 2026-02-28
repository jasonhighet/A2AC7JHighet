"""
app/applications/repository.py
-------------------------------
Raw psycopg2 SQL queries for the Applications table.
All methods accept an open connection (injected by the service layer).
"""

import psycopg2.extras
from ulid import ULID

from app.exceptions import DuplicateNameError, NotFoundError


def _row_to_dict(row, cursor) -> dict:
    cols = [desc[0] for desc in cursor.description]
    return dict(zip(cols, row))


class ApplicationRepository:
    def create(self, conn, *, name: str, comments: str | None) -> dict:
        new_id = str(ULID())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO applications (id, name, comments)
                    VALUES (%s, %s, %s)
                    RETURNING id, name, comments
                    """,
                    (new_id, name, comments),
                )
                row = cur.fetchone()
                conn.commit()
                return _row_to_dict(row, cur)
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            raise DuplicateNameError("Application", name)

    def update(self, conn, *, id: str, name: str | None, comments: str | None) -> dict:
        # Build a dynamic SET clause — only update provided fields
        fields, values = [], []
        if name is not None:
            fields.append("name = %s")
            values.append(name)
        if comments is not None:
            fields.append("comments = %s")
            values.append(comments)

        if not fields:
            return self.get_by_id(conn, id=id)

        values.append(id)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE applications SET {', '.join(fields)} WHERE id = %s RETURNING id, name, comments",
                    values,
                )
                row = cur.fetchone()
                if row is None:
                    conn.rollback()
                    raise NotFoundError("Application", id)
                conn.commit()
                return _row_to_dict(row, cur)
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            raise DuplicateNameError("Application", name)

    def get_by_id(self, conn, *, id: str) -> dict:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, comments FROM applications WHERE id = %s",
                (id,),
            )
            row = cur.fetchone()
            if row is None:
                raise NotFoundError("Application", id)
            return _row_to_dict(row, cur)

    def list_all(self, conn) -> list[dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, comments FROM applications ORDER BY name")
            rows = cur.fetchall()
            return [_row_to_dict(row, cur) for row in rows]
