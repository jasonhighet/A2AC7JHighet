"""
app/configurations/repository.py
---------------------------------
Raw psycopg2 SQL queries for the Configurations table.
"""

import json

import psycopg2.extras
import psycopg2.errors
from ulid import ULID

from app.exceptions import NotFoundError


def _row_to_dict(row, cursor) -> dict:
    cols = [desc[0] for desc in cursor.description]
    return dict(zip(cols, row))


class ConfigurationRepository:
    def create(
        self,
        conn,
        *,
        application_id: str,
        name: str,
        comments: str | None,
        config: dict,
    ) -> dict:
        new_id = str(ULID())
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO configurations (id, application_id, name, comments, config)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, application_id, name, comments, config
                """,
                (new_id, application_id, name, comments, json.dumps(config)),
            )
            row = cur.fetchone()
            conn.commit()
            return _row_to_dict(row, cur)

    def update(
        self,
        conn,
        *,
        id: str,
        name: str | None,
        comments: str | None,
        config: dict | None,
    ) -> dict:
        fields, values = [], []
        if name is not None:
            fields.append("name = %s")
            values.append(name)
        if comments is not None:
            fields.append("comments = %s")
            values.append(comments)
        if config is not None:
            fields.append("config = %s")
            values.append(json.dumps(config))

        if not fields:
            return self.get_by_id(conn, id=id)

        values.append(id)
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE configurations SET {', '.join(fields)} WHERE id = %s RETURNING id, application_id, name, comments, config",
                values,
            )
            row = cur.fetchone()
            if row is None:
                conn.rollback()
                raise NotFoundError("Configuration", id)
            conn.commit()
            return _row_to_dict(row, cur)

    def get_by_id(self, conn, *, id: str) -> dict:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, application_id, name, comments, config FROM configurations WHERE id = %s",
                (id,),
            )
            row = cur.fetchone()
            if row is None:
                raise NotFoundError("Configuration", id)
            return _row_to_dict(row, cur)
