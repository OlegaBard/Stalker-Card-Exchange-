from __future__ import annotations

import time
from pathlib import Path

import aiosqlite

from bot.config import TOTAL_CARDS, TRADE_EXPIRE_HOURS


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._migrate()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if not self._conn:
            raise RuntimeError("Database not connected")
        return self._conn

    async def _migrate(self) -> None:
        await self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                discord_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                super_weapon_claimed INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_cards (
                user_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, card_id),
                FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE,
                CHECK (card_id >= 1 AND card_id <= 48),
                CHECK (quantity >= 0)
            );

            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offerer_id INTEGER NOT NULL,
                give_card_id INTEGER NOT NULL,
                want_card_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                message_id INTEGER,
                channel_id INTEGER,
                FOREIGN KEY (offerer_id) REFERENCES users(discord_id)
            );

            CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
            """
        )
        await self.conn.commit()

    async def ensure_user(self, discord_id: int, username: str) -> None:
        await self.conn.execute(
            """
            INSERT INTO users (discord_id, username, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET username = excluded.username
            """,
            (discord_id, username, time.time()),
        )
        await self.conn.commit()

    async def set_card_quantity(
        self, user_id: int, card_id: int, quantity: int
    ) -> None:
        qty = max(0, quantity)
        if qty == 0:
            await self.conn.execute(
                "DELETE FROM user_cards WHERE user_id = ? AND card_id = ?",
                (user_id, card_id),
            )
        else:
            await self.conn.execute(
                """
                INSERT INTO user_cards (user_id, card_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, card_id) DO UPDATE SET quantity = excluded.quantity
                """,
                (user_id, card_id, qty),
            )
        await self.conn.commit()

    async def add_card(self, user_id: int, card_id: int, delta: int = 1) -> int:
        row = await self.conn.execute_fetchall(
            "SELECT quantity FROM user_cards WHERE user_id = ? AND card_id = ?",
            (user_id, card_id),
        )
        current = row[0][0] if row else 0
        new_qty = max(0, current + delta)
        await self.set_card_quantity(user_id, card_id, new_qty)
        return new_qty

    async def get_quantities(self, user_id: int) -> dict[int, int]:
        rows = await self.conn.execute_fetchall(
            "SELECT card_id, quantity FROM user_cards WHERE user_id = ?",
            (user_id,),
        )
        return {int(r["card_id"]): int(r["quantity"]) for r in rows}

    async def get_collection_stats(self, user_id: int) -> tuple[int, int, int]:
        qty = await self.get_quantities(user_id)
        collected = sum(1 for c in range(1, TOTAL_CARDS + 1) if qty.get(c, 0) > 0)
        duplicates = sum(max(0, qty.get(c, 0) - 1) for c in range(1, TOTAL_CARDS + 1))
        missing = TOTAL_CARDS - collected
        return collected, duplicates, missing

    async def get_duplicates(self, user_id: int) -> list[tuple[int, int]]:
        rows = await self.conn.execute_fetchall(
            """
            SELECT card_id, quantity FROM user_cards
            WHERE user_id = ? AND quantity > 1
            ORDER BY card_id
            """,
            (user_id,),
        )
        return [(int(r["card_id"]), int(r["quantity"])) for r in rows]

    async def get_missing_ids(self, user_id: int) -> list[int]:
        qty = await self.get_quantities(user_id)
        return [c for c in range(1, TOTAL_CARDS + 1) if qty.get(c, 0) == 0]

    async def has_card(self, user_id: int, card_id: int, min_qty: int = 1) -> bool:
        rows = await self.conn.execute_fetchall(
            "SELECT quantity FROM user_cards WHERE user_id = ? AND card_id = ?",
            (user_id, card_id),
        )
        return bool(rows and rows[0][0] >= min_qty)

    async def create_trade(
        self,
        offerer_id: int,
        give_card_id: int,
        want_card_id: int,
        message_id: int | None = None,
        channel_id: int | None = None,
    ) -> int:
        now = time.time()
        expires = now + TRADE_EXPIRE_HOURS * 3600
        cur = await self.conn.execute(
            """
            INSERT INTO trades (
                offerer_id, give_card_id, want_card_id,
                status, created_at, expires_at, message_id, channel_id
            ) VALUES (?, ?, ?, 'open', ?, ?, ?, ?)
            """,
            (
                offerer_id,
                give_card_id,
                want_card_id,
                now,
                expires,
                message_id,
                channel_id,
            ),
        )
        await self.conn.commit()
        return int(cur.lastrowid)

    async def get_trade(self, trade_id: int) -> dict | None:
        rows = await self.conn.execute_fetchall(
            "SELECT * FROM trades WHERE id = ?",
            (trade_id,),
        )
        if not rows:
            return None
        return dict(rows[0])

    async def update_trade_message(
        self, trade_id: int, message_id: int, channel_id: int
    ) -> None:
        await self.conn.execute(
            "UPDATE trades SET message_id = ?, channel_id = ? WHERE id = ?",
            (message_id, channel_id, trade_id),
        )
        await self.conn.commit()

    async def close_trade(self, trade_id: int, status: str) -> None:
        await self.conn.execute(
            "UPDATE trades SET status = ? WHERE id = ?",
            (status, trade_id),
        )
        await self.conn.commit()

    async def execute_swap(
        self,
        offerer_id: int,
        acceptor_id: int,
        give_card_id: int,
        want_card_id: int,
    ) -> None:
        """Offerer gives give_card, acceptor gives want_card."""
        async with self.conn.execute("BEGIN"):
            for uid, card_id, delta in (
                (offerer_id, give_card_id, -1),
                (offerer_id, want_card_id, 1),
                (acceptor_id, want_card_id, -1),
                (acceptor_id, give_card_id, 1),
            ):
                rows = await self.conn.execute_fetchall(
                    "SELECT quantity FROM user_cards WHERE user_id = ? AND card_id = ?",
                    (uid, card_id),
                )
                current = rows[0][0] if rows else 0
                new_q = current + delta
                if new_q < 0:
                    raise ValueError("Insufficient cards")
                if new_q == 0:
                    await self.conn.execute(
                        "DELETE FROM user_cards WHERE user_id = ? AND card_id = ?",
                        (uid, card_id),
                    )
                else:
                    await self.conn.execute(
                        """
                        INSERT INTO user_cards (user_id, card_id, quantity)
                        VALUES (?, ?, ?)
                        ON CONFLICT(user_id, card_id) DO UPDATE SET quantity = excluded.quantity
                        """,
                        (uid, card_id, new_q),
                    )
        await self.conn.commit()

    async def is_super_weapon_claimed(self, user_id: int) -> bool:
        rows = await self.conn.execute_fetchall(
            "SELECT super_weapon_claimed FROM users WHERE discord_id = ?",
            (user_id,),
        )
        return bool(rows and rows[0][0])

    async def claim_super_weapon(self, user_id: int) -> None:
        await self.conn.execute(
            "UPDATE users SET super_weapon_claimed = 1 WHERE discord_id = ?",
            (user_id,),
        )
        await self.conn.commit()

    async def count_open_trades(self, offerer_id: int) -> int:
        rows = await self.conn.execute_fetchall(
            """
            SELECT COUNT(*) FROM trades
            WHERE offerer_id = ? AND status = 'open' AND expires_at > ?
            """,
            (offerer_id, time.time()),
        )
        return int(rows[0][0]) if rows else 0
