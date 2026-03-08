import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from backend.core.config import get_settings
from backend.core.security import encrypt, decrypt

_conn: sqlite3.Connection | None = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        db_path = Path(get_settings().db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(db_path), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _init_schema(_conn)
    return _conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS alerts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            text            TEXT    NOT NULL,
            location_enc    BLOB    NOT NULL,
            category        TEXT    NOT NULL,
            severity        TEXT    NOT NULL,
            digest_summary  TEXT    NOT NULL,
            digest_steps    TEXT    NOT NULL,
            method          TEXT    NOT NULL,
            source          TEXT    NOT NULL DEFAULT 'api',
            created_at      TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id    TEXT    NOT NULL,
            ciphertext  BLOB    NOT NULL,
            created_at  TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_alerts_severity  ON alerts(severity);
        CREATE INDEX IF NOT EXISTS idx_alerts_category  ON alerts(category);
        CREATE INDEX IF NOT EXISTS idx_alerts_created   ON alerts(created_at);
        CREATE INDEX IF NOT EXISTS idx_messages_group   ON messages(group_id);
    """)
    conn.commit()
    _migrate_schema(conn)


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """Migrate old schema (location TEXT) to new schema (location_enc BLOB)."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(alerts)").fetchall()}
    if "location" in cols and "location_enc" not in cols:
        import logging
        logging.getLogger(__name__).warning(
            "Old schema detected (location TEXT). Migrating to location_enc BLOB — old location data will be re-encrypted."
        )
        conn.executescript("""
            ALTER TABLE alerts RENAME TO alerts_old;
            CREATE TABLE alerts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                text            TEXT    NOT NULL,
                location_enc    BLOB    NOT NULL,
                category        TEXT    NOT NULL,
                severity        TEXT    NOT NULL,
                digest_summary  TEXT    NOT NULL,
                digest_steps    TEXT    NOT NULL,
                method          TEXT    NOT NULL,
                source          TEXT    NOT NULL DEFAULT 'api',
                created_at      TEXT    NOT NULL
            );
        """)
        from backend.core.security import encrypt
        rows = conn.execute("SELECT * FROM alerts_old").fetchall()
        for row in rows:
            row = dict(row)
            location_plain = row.get("location", "unknown")
            conn.execute(
                """INSERT INTO alerts
                   (id, text, location_enc, category, severity, digest_summary, digest_steps, method, source, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["id"], row["text"], encrypt(location_plain),
                    row["category"], row["severity"],
                    row.get("digest_summary", ""), row.get("digest_steps", "[]"),
                    row.get("method", "fallback"), row.get("source", "api"), row["created_at"],
                ),
            )
        conn.execute("DROP TABLE alerts_old")
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_alerts_severity  ON alerts(severity);
            CREATE INDEX IF NOT EXISTS idx_alerts_category  ON alerts(category);
            CREATE INDEX IF NOT EXISTS idx_alerts_created   ON alerts(created_at);
        """)
        conn.commit()
        logging.getLogger(__name__).info("Schema migration complete. %d rows migrated.", len(rows))


def save_alert(alert: dict, source: str = "api") -> int:
    import json
    conn = get_conn()
    steps_json = json.dumps(alert["digest"]["steps"])
    cur = conn.execute(
        """INSERT INTO alerts
           (text, location_enc, category, severity, digest_summary, digest_steps, method, source, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            alert["alert"],
            encrypt(alert["location"]),          # location encrypted at rest
            alert["category"],
            alert["severity"],
            alert["digest"]["summary"],
            steps_json,
            alert["method"],
            source,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    return cur.lastrowid


def _row_to_dict(r: sqlite3.Row) -> dict:
    import json
    d = dict(r)
    d["location"] = decrypt(d.pop("location_enc"))
    d["digest"] = {
        "summary": d.pop("digest_summary"),
        "steps": json.loads(d.pop("digest_steps")),
    }
    return d


def search_alerts(keyword: str, limit: int = 50) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM alerts WHERE text LIKE ? ORDER BY created_at DESC LIMIT ?",
        (f"%{keyword}%", limit),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_stats() -> dict:
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    by_severity = {
        r["severity"]: r["cnt"]
        for r in conn.execute(
            "SELECT severity, COUNT(*) as cnt FROM alerts GROUP BY severity"
        ).fetchall()
    }
    by_category = {
        r["category"]: r["cnt"]
        for r in conn.execute(
            "SELECT category, COUNT(*) as cnt FROM alerts GROUP BY category"
        ).fetchall()
    }
    recent = []
    for r in conn.execute(
        "SELECT text, location_enc, severity, created_at FROM alerts ORDER BY created_at DESC LIMIT 5"
    ).fetchall():
        row = dict(r)
        row["location"] = decrypt(row.pop("location_enc"))
        recent.append(row)

    return {
        "total_alerts": total,
        "by_severity": by_severity,
        "by_category": by_category,
        "recent": recent,
    }


def save_message(group_id: str, ciphertext: bytes) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO messages (group_id, ciphertext, created_at) VALUES (?, ?, ?)",
        (group_id, ciphertext, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def get_messages(group_id: str) -> list[bytes]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT ciphertext FROM messages WHERE group_id = ? ORDER BY created_at ASC",
        (group_id,),
    ).fetchall()
    return [r["ciphertext"] for r in rows]


def get_message_count(group_id: str) -> int:
    conn = get_conn()
    return conn.execute(
        "SELECT COUNT(*) FROM messages WHERE group_id = ?", (group_id,)
    ).fetchone()[0]
