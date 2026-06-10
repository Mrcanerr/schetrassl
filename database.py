import aiosqlite
import os
from config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS owners (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                added_by    INTEGER NOT NULL,
                added_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS groups (
                group_id    INTEGER PRIMARY KEY,
                title       TEXT    NOT NULL,
                added_by    INTEGER NOT NULL,
                added_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS broadcasts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                text        TEXT    NOT NULL,
                hours       TEXT    NOT NULL,
                created_by  INTEGER NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                is_active   INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS send_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                broadcast_id    INTEGER NOT NULL,
                broadcast_name  TEXT    NOT NULL,
                created_by      INTEGER NOT NULL,
                sent_at         TEXT    NOT NULL DEFAULT (datetime('now')),
                groups_count    INTEGER NOT NULL DEFAULT 0,
                status          TEXT    NOT NULL DEFAULT 'ok'
            );

            CREATE TABLE IF NOT EXISTS delete_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                broadcast_name  TEXT    NOT NULL,
                deleted_by      INTEGER NOT NULL,
                deleted_at      TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)
        await db.commit()


# ─── OWNERS ────────────────────────────────────────────────────────────────

async def add_owner(user_id: int, username: str | None, added_by: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO owners (user_id, username, added_by) VALUES (?, ?, ?)",
            (user_id, username, added_by),
        )
        await db.commit()


async def remove_owner(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM owners WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_owners() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM owners ORDER BY added_at") as cur:
            return [dict(r) for r in await cur.fetchall()]


async def is_owner(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM owners WHERE user_id = ?", (user_id,)
        ) as cur:
            return await cur.fetchone() is not None


# ─── GROUPS ────────────────────────────────────────────────────────────────

async def add_group(group_id: int, title: str, added_by: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO groups (group_id, title, added_by) VALUES (?, ?, ?)",
            (group_id, title, added_by),
        )
        await db.commit()


async def remove_group(group_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
        await db.commit()


async def get_groups() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM groups ORDER BY added_at") as cur:
            return [dict(r) for r in await cur.fetchall()]


async def is_group_whitelisted(group_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM groups WHERE group_id = ?", (group_id,)
        ) as cur:
            return await cur.fetchone() is not None


# ─── BROADCASTS ────────────────────────────────────────────────────────────

async def create_broadcast(name: str, text: str, hours: str, created_by: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO broadcasts (name, text, hours, created_by) VALUES (?, ?, ?, ?)",
            (name, text, hours, created_by),
        )
        await db.commit()
        return cur.lastrowid


async def get_broadcasts(user_id: int | None = None) -> list[dict]:
    """Return active broadcasts. If user_id given — only that user's."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if user_id is None:
            async with db.execute(
                "SELECT * FROM broadcasts WHERE is_active = 1 ORDER BY created_at"
            ) as cur:
                return [dict(r) for r in await cur.fetchall()]
        else:
            async with db.execute(
                "SELECT * FROM broadcasts WHERE is_active = 1 AND created_by = ? ORDER BY created_at",
                (user_id,),
            ) as cur:
                return [dict(r) for r in await cur.fetchall()]


async def get_broadcast(broadcast_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM broadcasts WHERE id = ?", (broadcast_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def update_broadcast(broadcast_id: int, name: str, text: str, hours: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE broadcasts SET name = ?, text = ?, hours = ? WHERE id = ?",
            (name, text, hours, broadcast_id),
        )
        await db.commit()


async def delete_broadcast(broadcast_id: int, deleted_by: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT name FROM broadcasts WHERE id = ?", (broadcast_id,)
        ) as cur:
            row = await cur.fetchone()
        if row:
            await db.execute(
                "UPDATE broadcasts SET is_active = 0 WHERE id = ?", (broadcast_id,)
            )
            await db.execute(
                "INSERT INTO delete_logs (broadcast_name, deleted_by) VALUES (?, ?)",
                (row["name"], deleted_by),
            )
            await db.commit()


# ─── LOGS ──────────────────────────────────────────────────────────────────

async def log_send(
    broadcast_id: int,
    broadcast_name: str,
    created_by: int,
    groups_count: int,
    status: str = "ok",
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO send_logs
               (broadcast_id, broadcast_name, created_by, groups_count, status)
               VALUES (?, ?, ?, ?, ?)""",
            (broadcast_id, broadcast_name, created_by, groups_count, status),
        )
        await db.commit()


async def get_send_logs(limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM send_logs ORDER BY sent_at DESC LIMIT ?", (limit,)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_delete_logs(limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM delete_logs ORDER BY deleted_at DESC LIMIT ?", (limit,)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]
