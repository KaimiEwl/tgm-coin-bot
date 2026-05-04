import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
import random
from typing import Any, Optional, Tuple


SOURCE_CHAT_MESSAGE = "CHAT_MESSAGE"
SOURCE_SUPER_PRIZE = "SUPER_PRIZE"
SOURCE_OWNER_TRIBUTE = "OWNER_TRIBUTE"
SOURCE_CHAT_FIREWORK = "CHAT_FIREWORK"
SOURCE_TRANSFER_OUT = "TRANSFER_OUT"
SOURCE_TRANSFER_IN = "TRANSFER_IN"
SOURCE_REFERRAL_BONUS = "REFERRAL_BONUS"
SOURCE_REFERRAL_COMMISSION = "REFERRAL_COMMISSION"
RELIABILITY_EVENT_FLAGGED = "FLAGGED_UNTRUSTED"
LANGUAGE_RU = "ru"
LANGUAGE_EN = "en"

FEATURE_SEND_COINS = "send_coins"
FEATURE_SUPER_PRIZE = "super_prize"
FEATURE_FIREWORKS = "fireworks"
FEATURE_OWNER_TRIBUTE = "owner_tribute"
FEATURE_TEST_MODE = "test_mode"
FEATURE_REFERRALS = "referrals"
FEATURE_BROADCASTS = "broadcasts"
FEATURE_WEBAPP = "webapp"
FEATURE_FREE_BOOSTS = "free_boosts"
FEATURE_PAID_BOOSTS = "paid_boosts"
FEATURE_SECURITY_MONITORING = "security_monitoring"


class Storage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def _ensure_reliability_row(conn: sqlite3.Connection, user_id: int) -> None:
        conn.execute(
            """
            INSERT INTO user_reliability (user_id, is_trusted)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                updated_at=CURRENT_TIMESTAMP
            """,
            (user_id,),
        )

    @staticmethod
    def _ensure_user_settings_row(conn: sqlite3.Connection, user_id: int) -> None:
        conn.execute(
            """
            INSERT INTO user_settings (user_id, language_code)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                updated_at=CURRENT_TIMESTAMP
            """,
            (user_id, LANGUAGE_RU),
        )

    @staticmethod
    def _seed_feature_flags(conn: sqlite3.Connection) -> None:
        defaults = [
            (FEATURE_SEND_COINS, 0, "Enable /send coin transfers"),
            (FEATURE_SUPER_PRIZE, 1, "Enable super prize mechanics"),
            (FEATURE_FIREWORKS, 1, "Enable chat firework mechanics"),
            (FEATURE_OWNER_TRIBUTE, 1, "Enable 10% owner tribute"),
            (FEATURE_REFERRALS, 1, "Enable referral mechanics"),
            (FEATURE_BROADCASTS, 1, "Enable admin broadcasts"),
            (FEATURE_WEBAPP, 1, "Enable mini web app"),
            (FEATURE_FREE_BOOSTS, 0, "Enable free boosts"),
            (FEATURE_PAID_BOOSTS, 0, "Enable paid boosts (TON/USDT)"),
            (FEATURE_SECURITY_MONITORING, 1, "Enable security monitoring widgets"),
            (FEATURE_TEST_MODE, 0, "Enable test mode scenarios"),
        ]
        for key, enabled, description in defaults:
            conn.execute(
                """
                INSERT INTO feature_flags (key, enabled, description)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    description=excluded.description
                """,
                (key, enabled, description),
            )

    @staticmethod
    def _current_firework_period() -> tuple[str, str]:
        now = datetime.now()
        hour = now.hour
        if 6 <= hour < 12:
            code = "morning"
        elif 12 <= hour < 18:
            code = "day"
        elif 18 <= hour < 24:
            code = "evening"
        else:
            code = "night"
        return code, f"{now.strftime('%Y-%m-%d')}:{code}"

    @staticmethod
    def _period_code_from_key(key: str) -> str:
        if ":" in key:
            return key.split(":", 1)[1]
        return ""

    def init_db(self) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    coins INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coin_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER,
                    message_id INTEGER,
                    source TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS super_prize_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    trigger_chat_id INTEGER NOT NULL,
                    trigger_message_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    reward INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    claimed_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_super_prize_pending_user
                ON super_prize_tasks(user_id)
                WHERE status = 'PENDING'
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_coin_events_user_created
                ON coin_events(user_id, created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_tax_state (
                    chat_id INTEGER PRIMARY KEY,
                    owner_user_id INTEGER NOT NULL,
                    remainder_percent INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_reliability (
                    user_id INTEGER PRIMARY KEY,
                    is_trusted INTEGER NOT NULL DEFAULT 1,
                    flagged_at TEXT,
                    note TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reliability_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event TEXT NOT NULL,
                    streak_seconds INTEGER NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_reliability_logs_user_created
                ON reliability_logs(user_id, created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY,
                    chat_type TEXT,
                    chat_title TEXT,
                    fireworks_enabled INTEGER NOT NULL DEFAULT 0,
                    progress_points INTEGER NOT NULL DEFAULT 0,
                    progress_goal INTEGER NOT NULL DEFAULT 100,
                    progress_anchor_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    fireworks_daily_count INTEGER NOT NULL DEFAULT 0,
                    fireworks_day_key TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    language_code TEXT NOT NULL DEFAULT 'ru',
                    broadcast_enabled INTEGER NOT NULL DEFAULT 0,
                    activated_at TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS referrals (
                    referred_user_id INTEGER PRIMARY KEY,
                    referrer_user_id INTEGER NOT NULL,
                    bonus_awarded INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(referred_user_id) REFERENCES users(user_id),
                    FOREIGN KEY(referrer_user_id) REFERENCES users(user_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_referrals_referrer
                ON referrals(referrer_user_id)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS referral_commission_state (
                    referred_user_id INTEGER PRIMARY KEY,
                    referrer_user_id INTEGER NOT NULL,
                    remainder_percent INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(referred_user_id) REFERENCES users(user_id),
                    FOREIGN KEY(referrer_user_id) REFERENCES users(user_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    activated_only INTEGER NOT NULL DEFAULT 1,
                    sent_count INTEGER NOT NULL DEFAULT 0,
                    failed_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feature_flags (
                    key TEXT PRIMARY KEY,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    description TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._seed_feature_flags(conn)
            user_settings_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(user_settings)").fetchall()
            }
            if "broadcast_enabled" not in user_settings_columns:
                conn.execute(
                    """
                    ALTER TABLE user_settings
                    ADD COLUMN broadcast_enabled INTEGER NOT NULL DEFAULT 0
                    """
                )
            if "activated_at" not in user_settings_columns:
                conn.execute(
                    """
                    ALTER TABLE user_settings
                    ADD COLUMN activated_at TEXT
                    """
                )
            chat_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(chats)").fetchall()
            }
            if "fireworks_daily_count" not in chat_columns:
                conn.execute(
                    """
                    ALTER TABLE chats
                    ADD COLUMN fireworks_daily_count INTEGER NOT NULL DEFAULT 0
                    """
                )
            if "fireworks_day_key" not in chat_columns:
                conn.execute(
                    """
                    ALTER TABLE chats
                    ADD COLUMN fireworks_day_key TEXT
                    """
                )
            if "progress_anchor_at" not in chat_columns:
                conn.execute(
                    """
                    ALTER TABLE chats
                    ADD COLUMN progress_anchor_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    """
                )
            conn.commit()

    def ensure_user(self, user_id: int, username: str, first_name: str) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, coins)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, username, first_name),
            )
            self._ensure_reliability_row(conn, user_id)
            self._ensure_user_settings_row(conn, user_id)
            conn.commit()

    def add_coins(
        self,
        user_id: int,
        username: str,
        first_name: str,
        amount: int,
        source: str,
        chat_id: int,
        message_id: int,
    ) -> int:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, coins)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, username, first_name),
            )
            self._ensure_reliability_row(conn, user_id)
            self._ensure_user_settings_row(conn, user_id)
            conn.execute(
                """
                UPDATE users
                SET coins = coins + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (amount, user_id),
            )
            conn.execute(
                """
                INSERT INTO coin_events (user_id, chat_id, message_id, source, amount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, chat_id, message_id, source, amount),
            )
            row = conn.execute(
                "SELECT coins FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            conn.commit()
        return int(row[0]) if row else amount

    def add_chat_reward_with_cooldown(
        self,
        user_id: int,
        username: str,
        first_name: str,
        amount: int,
        chat_id: int,
        message_id: int,
        cooldown_seconds: int,
    ) -> Tuple[bool, int, int]:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, coins)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, username, first_name),
            )
            self._ensure_reliability_row(conn, user_id)
            self._ensure_user_settings_row(conn, user_id)

            row = conn.execute(
                """
                SELECT CAST((strftime('%s', 'now') - strftime('%s', created_at)) AS INTEGER)
                FROM coin_events
                WHERE user_id = ? AND chat_id = ? AND source = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id, chat_id, SOURCE_CHAT_MESSAGE),
            ).fetchone()

            if row is not None:
                elapsed = int(row[0]) if row[0] is not None else cooldown_seconds
                if elapsed < cooldown_seconds:
                    total_row = conn.execute(
                        "SELECT coins FROM users WHERE user_id = ?",
                        (user_id,),
                    ).fetchone()
                    conn.commit()
                    total = int(total_row[0]) if total_row else 0
                    return False, total, cooldown_seconds - elapsed

            conn.execute(
                """
                UPDATE users
                SET coins = coins + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (amount, user_id),
            )
            conn.execute(
                """
                INSERT INTO coin_events (user_id, chat_id, message_id, source, amount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, chat_id, message_id, SOURCE_CHAT_MESSAGE, amount),
            )
            total_row = conn.execute(
                "SELECT coins FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            conn.commit()

        total = int(total_row[0]) if total_row else amount
        return True, total, 0

    def has_chat_reward_today(self, user_id: int) -> bool:
        """True if user has at least one chat-message reward today (localtime)."""
        safe_user_id = int(user_id)
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM coin_events
                WHERE user_id = ?
                  AND source = ?
                  AND date(created_at, 'localtime') = date('now', 'localtime')
                LIMIT 1
                """,
                (safe_user_id, SOURCE_CHAT_MESSAGE),
            ).fetchone()
        return row is not None

    def get_coins(self, user_id: int) -> int:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT coins FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return int(row[0]) if row else 0

    def get_total_coins(self) -> int:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(CASE WHEN coins > 0 THEN coins ELSE 0 END), 0)
                FROM users
                """
            ).fetchone()
        return int(row[0]) if row else 0

    def get_user_overview(self, user_id: int) -> dict[str, Any]:
        safe_user_id = int(user_id)
        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            totals_row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_users,
                    COALESCE(SUM(CASE WHEN coins > 0 THEN coins ELSE 0 END), 0) AS total_coins
                FROM users
                """
            ).fetchone()

            user_row = conn.execute(
                """
                SELECT user_id, username, first_name, coins
                FROM users
                WHERE user_id = ?
                """,
                (safe_user_id,),
            ).fetchone()

            if user_row is None:
                coins = 0
                username = ""
                first_name = ""
                rank = None
            else:
                coins = int(user_row["coins"] or 0)
                username = user_row["username"] or ""
                first_name = user_row["first_name"] or ""
                rank_row = conn.execute(
                    """
                    SELECT COUNT(*) + 1
                    FROM users
                    WHERE coins > ?
                       OR (coins = ? AND user_id < ?)
                    """,
                    (coins, coins, safe_user_id),
                ).fetchone()
                rank = int(rank_row[0]) if rank_row else None

            ref_totals = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_referrals,
                    COALESCE(SUM(CASE WHEN bonus_awarded = 1 THEN 1 ELSE 0 END), 0) AS rewarded_referrals
                FROM referrals
                WHERE referrer_user_id = ?
                """,
                (safe_user_id,),
            ).fetchone()
            commission_row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM coin_events
                WHERE user_id = ? AND source = ?
                """,
                (safe_user_id, SOURCE_REFERRAL_COMMISSION),
            ).fetchone()

            today_income_row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM coin_events
                WHERE user_id = ?
                  AND amount > 0
                  AND created_at >= datetime('now', 'start of day')
                """,
                (safe_user_id,),
            ).fetchone()
            week_income_row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM coin_events
                WHERE user_id = ?
                  AND amount > 0
                  AND created_at >= datetime('now', '-7 days')
                """,
                (safe_user_id,),
            ).fetchone()
            active_days_7d_row = conn.execute(
                """
                SELECT COUNT(DISTINCT substr(created_at, 1, 10))
                FROM coin_events
                WHERE user_id = ?
                  AND source = ?
                  AND amount > 0
                  AND created_at >= datetime('now', '-7 days')
                """,
                (safe_user_id, SOURCE_CHAT_MESSAGE),
            ).fetchone()
            streak_days_rows = conn.execute(
                """
                SELECT substr(created_at, 1, 10) AS day
                FROM coin_events
                WHERE user_id = ?
                  AND source = ?
                  AND amount > 0
                GROUP BY day
                ORDER BY day DESC
                LIMIT 60
                """,
                (safe_user_id, SOURCE_CHAT_MESSAGE),
            ).fetchall()

            last_chat_reward_row = conn.execute(
                """
                SELECT created_at
                FROM coin_events
                WHERE user_id = ?
                  AND source = ?
                  AND amount > 0
                ORDER BY id DESC
                LIMIT 1
                """,
                (safe_user_id, SOURCE_CHAT_MESSAGE),
            ).fetchone()

        # Daily streak based on having at least one rewarded chat message per UTC day.
        day_set = set()
        for row in streak_days_rows or []:
            if not row:
                continue
            try:
                day_set.add(datetime.strptime(str(row["day"]), "%Y-%m-%d").date())
            except Exception:
                continue
        streak_days = 0
        cursor = datetime.utcnow().date()
        while cursor in day_set:
            streak_days += 1
            cursor -= timedelta(days=1)

        next_reward_seconds = 0
        if last_chat_reward_row and last_chat_reward_row[0]:
            try:
                last_dt = datetime.strptime(str(last_chat_reward_row[0]), "%Y-%m-%d %H:%M:%S")
                elapsed = max(0, int((datetime.utcnow() - last_dt).total_seconds()))
                next_reward_seconds = max(0, 60 - elapsed)
            except Exception:
                next_reward_seconds = 0

        return {
            "user_id": safe_user_id,
            "username": username,
            "first_name": first_name,
            "coins": coins,
            "rank": rank,
            "total_users": int(totals_row["total_users"] or 0) if totals_row else 0,
            "total_coins": int(totals_row["total_coins"] or 0) if totals_row else 0,
            "referrals_total": int(ref_totals["total_referrals"] or 0) if ref_totals else 0,
            "rewarded_referrals": int(ref_totals["rewarded_referrals"] or 0) if ref_totals else 0,
            "commission_total": int(commission_row[0] or 0) if commission_row else 0,
            "today_income": int(today_income_row[0] or 0) if today_income_row else 0,
            "week_income": int(week_income_row[0] or 0) if week_income_row else 0,
            "active_days_7d": int(active_days_7d_row[0] or 0) if active_days_7d_row else 0,
            "streak_days": int(streak_days),
            "next_reward_seconds": int(next_reward_seconds),
        }

    def get_user_reliability(self, user_id: int) -> bool:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT is_trusted
                FROM user_reliability
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return True
        return bool(int(row[0]))

    def has_pending_super_prize(self, user_id: int) -> bool:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT id
                FROM super_prize_tasks
                WHERE user_id = ? AND status = 'PENDING'
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        return row is not None

    def create_super_prize_task(
        self,
        user_id: int,
        username: str,
        first_name: str,
        trigger_chat_id: int,
        trigger_message_id: int,
    ) -> bool:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, coins)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, username, first_name),
            )
            self._ensure_reliability_row(conn, user_id)
            self._ensure_user_settings_row(conn, user_id)
            try:
                conn.execute(
                    """
                    INSERT INTO super_prize_tasks (user_id, trigger_chat_id, trigger_message_id)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, trigger_chat_id, trigger_message_id),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                conn.rollback()
                return False

    def claim_super_prize(
        self,
        user_id: int,
        username: str,
        first_name: str,
        reward: int,
        chat_id: int,
        message_id: int,
    ) -> Optional[Tuple[int, int]]:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT id
                FROM super_prize_tasks
                WHERE user_id = ? AND status = 'PENDING'
                ORDER BY id ASC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if row is None:
                return None

            task_id = int(row[0])
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, coins)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, username, first_name),
            )
            self._ensure_reliability_row(conn, user_id)
            self._ensure_user_settings_row(conn, user_id)
            conn.execute(
                """
                UPDATE users
                SET coins = coins + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (reward, user_id),
            )
            conn.execute(
                """
                INSERT INTO coin_events (user_id, chat_id, message_id, source, amount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, chat_id, message_id, SOURCE_SUPER_PRIZE, reward),
            )
            conn.execute(
                """
                UPDATE super_prize_tasks
                SET status = 'CLAIMED', reward = ?, claimed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (reward, task_id),
            )
            total_row = conn.execute(
                "SELECT coins FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            conn.commit()

        total = int(total_row[0]) if total_row else reward
        return reward, total

    def add_owner_tribute(
        self,
        chat_id: int,
        owner_user_id: int,
        amount_from_user_reward: int,
        message_id: int,
    ) -> Tuple[int, int]:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, coins)
                VALUES (?, '', '', 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    updated_at=CURRENT_TIMESTAMP
                """,
                (owner_user_id,),
            )
            self._ensure_reliability_row(conn, owner_user_id)
            self._ensure_user_settings_row(conn, owner_user_id)

            state_row = conn.execute(
                """
                SELECT owner_user_id, remainder_percent
                FROM chat_tax_state
                WHERE chat_id = ?
                """,
                (chat_id,),
            ).fetchone()

            remainder = 0
            if state_row is not None:
                stored_owner_user_id = int(state_row[0])
                if stored_owner_user_id == owner_user_id:
                    remainder = int(state_row[1])

            percent_units = amount_from_user_reward * 10 + remainder
            tribute_amount = percent_units // 100
            new_remainder = percent_units % 100

            conn.execute(
                """
                INSERT INTO chat_tax_state (chat_id, owner_user_id, remainder_percent)
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    owner_user_id=excluded.owner_user_id,
                    remainder_percent=excluded.remainder_percent,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (chat_id, owner_user_id, new_remainder),
            )

            if tribute_amount > 0:
                conn.execute(
                    """
                    UPDATE users
                    SET coins = coins + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (tribute_amount, owner_user_id),
                )
                conn.execute(
                    """
                    INSERT INTO coin_events (user_id, chat_id, message_id, source, amount)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        owner_user_id,
                        chat_id,
                        message_id,
                        SOURCE_OWNER_TRIBUTE,
                        tribute_amount,
                    ),
                )

            total_row = conn.execute(
                "SELECT coins FROM users WHERE user_id = ?",
                (owner_user_id,),
            ).fetchone()
            conn.commit()

        owner_total = int(total_row[0]) if total_row else 0
        return tribute_amount, owner_total

    def evaluate_user_reliability(
        self,
        user_id: int,
        threshold_seconds: int,
        max_gap_seconds: int,
    ) -> Tuple[bool, int]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT created_at
                FROM coin_events
                WHERE user_id = ? AND source = ?
                ORDER BY id DESC
                LIMIT 20000
                """,
                (user_id, SOURCE_CHAT_MESSAGE),
            ).fetchall()

            self._ensure_reliability_row(conn, user_id)
            if not rows:
                conn.commit()
                return False, 0

            time_format = "%Y-%m-%d %H:%M:%S"
            latest_at = datetime.strptime(rows[0][0], time_format)
            streak_start = latest_at
            prev = latest_at

            for row in rows[1:]:
                current = datetime.strptime(row[0], time_format)
                gap_seconds = int((prev - current).total_seconds())
                if gap_seconds <= max_gap_seconds:
                    streak_start = current
                    prev = current
                    continue
                break

            streak_seconds = int((latest_at - streak_start).total_seconds())
            rel_row = conn.execute(
                """
                SELECT is_trusted
                FROM user_reliability
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
            is_trusted = True if rel_row is None else bool(int(rel_row[0]))

            if streak_seconds >= threshold_seconds and is_trusted:
                note = (
                    "Auto-flagged: continuous collection streak exceeded "
                    f"{threshold_seconds} seconds."
                )
                conn.execute(
                    """
                    UPDATE user_reliability
                    SET is_trusted = 0,
                        flagged_at = CURRENT_TIMESTAMP,
                        note = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (note, user_id),
                )
                conn.execute(
                    """
                    INSERT INTO reliability_logs (user_id, event, streak_seconds, details)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, RELIABILITY_EVENT_FLAGGED, streak_seconds, note),
                )
                conn.commit()
                return True, streak_seconds

            conn.execute(
                """
                UPDATE user_reliability
                SET updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (user_id,),
            )
            conn.commit()
            return False, streak_seconds

    def upsert_chat(self, chat_id: int, chat_type: str, chat_title: str) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO chats (chat_id, chat_type, chat_title)
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    chat_type=excluded.chat_type,
                    chat_title=excluded.chat_title,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (chat_id, chat_type, chat_title),
            )
            conn.commit()

    def set_chat_fireworks_enabled(self, chat_id: int, enabled: bool) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO chats (chat_id, chat_type, chat_title, fireworks_enabled)
                VALUES (?, '', '', ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    fireworks_enabled=excluded.fireworks_enabled,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (chat_id, 1 if enabled else 0),
            )
            conn.commit()

    def list_chats(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str = "",
    ) -> list[dict[str, Any]]:
        where_sql = ""
        params: list[Any] = []
        if search:
            where_sql = """
                WHERE
                    CAST(chat_id AS TEXT) LIKE ?
                    OR chat_title LIKE ?
                    OR chat_type LIKE ?
            """
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])

        query = f"""
            SELECT
                chat_id,
                chat_type,
                chat_title,
                fireworks_enabled,
                progress_points,
                progress_goal,
                fireworks_daily_count,
                fireworks_day_key,
                updated_at
            FROM chats
            {where_sql}
            ORDER BY updated_at DESC, chat_id DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            goal = int(row["progress_goal"]) if row["progress_goal"] else 100
            points_raw = float(row["progress_points"]) if row["progress_points"] is not None else 0.0
            points = int(points_raw)
            progress_percent = 0 if goal <= 0 else min(100, int((points * 100) / goal))
            period_key = row["fireworks_day_key"] or ""
            period_code = self._period_code_from_key(period_key)
            period_count = int(row["fireworks_daily_count"] or 0)
            items.append(
                {
                    "chat_id": int(row["chat_id"]),
                    "chat_type": row["chat_type"] or "",
                    "chat_title": row["chat_title"] or "",
                    "fireworks_enabled": bool(int(row["fireworks_enabled"])),
                    "progress_points": points,
                    "progress_goal": goal,
                    "progress_percent": progress_percent,
                    "fireworks_period_count": period_count,
                    "fireworks_period_key": period_key,
                    "fireworks_period_code": period_code,
                    "updated_at": row["updated_at"] or "",
                }
            )
        return items

    def count_chats(self, search: str = "") -> int:
        where_sql = ""
        params: list[Any] = []
        if search:
            where_sql = """
                WHERE
                    CAST(chat_id AS TEXT) LIKE ?
                    OR chat_title LIKE ?
                    OR chat_type LIKE ?
            """
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])

        query = f"""
            SELECT COUNT(*)
            FROM chats
            {where_sql}
        """
        with self.connection() as conn:
            row = conn.execute(query, params).fetchone()
        return int(row[0]) if row else 0

    def apply_chat_fireworks_progress(
        self,
        chat_id: int,
        chat_type: str,
        chat_title: str,
        message_id: int,
        winners_limit: int,
        reward_min: int,
        reward_max: int,
        max_triggers_per_period: int,
        base_daily_points: float,
        max_activity_bonus_points: float,
        activity_window_hours: int,
    ) -> dict[str, Any]:
        max_triggers_per_period = max(1, max_triggers_per_period)
        window_hours = max(1, int(activity_window_hours))
        base_daily_points = max(1.0, float(base_daily_points))
        max_activity_bonus_points = max(0.0, float(max_activity_bonus_points))

        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO chats (chat_id, chat_type, chat_title)
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    chat_type=excluded.chat_type,
                    chat_title=excluded.chat_title,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (chat_id, chat_type, chat_title),
            )

            enabled_row = conn.execute(
                """
                SELECT
                    fireworks_enabled,
                    progress_points,
                    progress_goal,
                    progress_anchor_at,
                    COALESCE(fireworks_daily_count, 0),
                    COALESCE(fireworks_day_key, '')
                FROM chats
                WHERE chat_id = ?
                """,
                (chat_id,),
            ).fetchone()
            if enabled_row is None:
                conn.commit()
                return {
                    "enabled": False,
                    "triggered": False,
                    "progress_percent": 0,
                    "progress_points": 0,
                    "progress_goal": 100,
                    "period_code": self._current_firework_period()[0],
                    "period_count": 0,
                    "period_max": max_triggers_per_period,
                    "period_limit_reached": False,
                    "target_daily_points": round(base_daily_points, 2),
                    "winners": [],
                }

            enabled = bool(int(enabled_row[0]))
            current_points = float(enabled_row[1]) if enabled_row[1] is not None else 0.0
            goal = int(enabled_row[2]) if enabled_row[2] else 100
            anchor_raw = enabled_row[3] or ""
            period_count = int(enabled_row[4]) if enabled_row[4] is not None else 0
            period_key = enabled_row[5] or ""
            if goal <= 0:
                goal = 100

            now_dt = datetime.now()
            anchor_dt = now_dt
            if anchor_raw:
                try:
                    anchor_dt = datetime.strptime(anchor_raw, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    anchor_dt = now_dt
            elapsed_seconds = max(0.0, (now_dt - anchor_dt).total_seconds())

            activity_row = conn.execute(
                """
                SELECT
                    COUNT(*) AS msg_count,
                    COUNT(DISTINCT user_id) AS uniq_users
                FROM coin_events
                WHERE chat_id = ?
                  AND source = ?
                  AND created_at >= datetime('now', ?)
                """,
                (chat_id, SOURCE_CHAT_MESSAGE, f"-{window_hours} hours"),
            ).fetchone()
            msg_count = int(activity_row[0]) if activity_row and activity_row[0] is not None else 0
            uniq_users = int(activity_row[1]) if activity_row and activity_row[1] is not None else 0
            msg_rate_hour = msg_count / float(window_hours)
            msg_ratio = min(1.0, msg_rate_hour / 25.0)
            uniq_ratio = min(1.0, uniq_users / 20.0)
            activity_ratio = msg_ratio * 0.6 + uniq_ratio * 0.4
            target_daily_points = base_daily_points + max_activity_bonus_points * activity_ratio
            delta_points = elapsed_seconds * target_daily_points / 86400.0

            current_period_code, current_period_key = self._current_firework_period()
            if period_key != current_period_key:
                period_count = 0
                period_key = current_period_key

            if not enabled:
                progress_percent = min(100, int((current_points * 100) / goal))
                conn.execute(
                    """
                    UPDATE chats
                    SET fireworks_daily_count = ?,
                        fireworks_day_key = ?,
                        progress_anchor_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                    """,
                    (period_count, period_key, chat_id),
                )
                conn.commit()
                return {
                    "enabled": False,
                    "triggered": False,
                    "progress_percent": progress_percent,
                    "progress_points": int(current_points),
                    "progress_goal": goal,
                    "period_code": current_period_code,
                    "period_count": period_count,
                    "period_max": max_triggers_per_period,
                    "period_limit_reached": False,
                    "target_daily_points": round(target_daily_points, 2),
                    "winners": [],
                }

            new_points = current_points + max(delta_points, 0.0)
            if period_count >= max_triggers_per_period:
                capped_points = min(new_points, float(max(goal - 1, 0)))
                conn.execute(
                    """
                    UPDATE chats
                    SET progress_points = ?,
                        fireworks_daily_count = ?,
                        fireworks_day_key = ?,
                        progress_anchor_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                    """,
                    (capped_points, period_count, period_key, chat_id),
                )
                conn.commit()
                return {
                    "enabled": True,
                    "triggered": False,
                    "progress_percent": min(100, int((int(capped_points) * 100) / goal)),
                    "progress_points": int(capped_points),
                    "progress_goal": goal,
                    "period_code": current_period_code,
                    "period_count": period_count,
                    "period_max": max_triggers_per_period,
                    "period_limit_reached": True,
                    "target_daily_points": round(target_daily_points, 2),
                    "winners": [],
                }

            if new_points < goal:
                conn.execute(
                    """
                    UPDATE chats
                    SET progress_points = ?,
                        fireworks_daily_count = ?,
                        fireworks_day_key = ?,
                        progress_anchor_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                    """,
                    (new_points, period_count, period_key, chat_id),
                )
                conn.commit()
                return {
                    "enabled": True,
                    "triggered": False,
                    "progress_percent": min(100, int((int(new_points) * 100) / goal)),
                    "progress_points": int(new_points),
                    "progress_goal": goal,
                    "period_code": current_period_code,
                    "period_count": period_count,
                    "period_max": max_triggers_per_period,
                    "period_limit_reached": False,
                    "target_daily_points": round(target_daily_points, 2),
                    "winners": [],
                }

            remainder = min(new_points - goal, float(max(goal - 1, 0)))
            period_count += 1
            conn.execute(
                """
                UPDATE chats
                SET progress_points = ?,
                    fireworks_daily_count = ?,
                    fireworks_day_key = ?,
                    progress_anchor_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ?
                """,
                (remainder, period_count, period_key, chat_id),
            )

            rows = conn.execute(
                """
                SELECT user_id
                FROM coin_events
                WHERE chat_id = ? AND source = ?
                ORDER BY id DESC
                LIMIT 500
                """,
                (chat_id, SOURCE_CHAT_MESSAGE),
            ).fetchall()

            recent_users: list[int] = []
            seen: set[int] = set()
            for row in rows:
                user_id = int(row[0])
                if user_id in seen:
                    continue
                seen.add(user_id)
                recent_users.append(user_id)
                if len(recent_users) >= winners_limit:
                    break

            winners: list[dict[str, Any]] = []
            for winner_user_id in recent_users:
                amount = random.randint(reward_min, reward_max)
                conn.execute(
                    """
                    INSERT INTO users (user_id, username, first_name, coins)
                    VALUES (?, '', '', 0)
                    ON CONFLICT(user_id) DO UPDATE SET
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (winner_user_id,),
                )
                self._ensure_reliability_row(conn, winner_user_id)
                self._ensure_user_settings_row(conn, winner_user_id)
                conn.execute(
                    """
                    UPDATE users
                    SET coins = coins + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (amount, winner_user_id),
                )
                conn.execute(
                    """
                    INSERT INTO coin_events (user_id, chat_id, message_id, source, amount)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (winner_user_id, chat_id, message_id, SOURCE_CHAT_FIREWORK, amount),
                )
                user_row = conn.execute(
                    """
                    SELECT username, first_name
                    FROM users
                    WHERE user_id = ?
                    """,
                    (winner_user_id,),
                ).fetchone()
                winners.append(
                    {
                        "user_id": winner_user_id,
                        "username": user_row[0] if user_row and user_row[0] else "",
                        "first_name": user_row[1] if user_row and user_row[1] else "",
                        "amount": amount,
                    }
                )

            conn.commit()
            return {
                "enabled": True,
                "triggered": True,
                "progress_percent": min(100, int((int(remainder) * 100) / goal)),
                "progress_points": int(remainder),
                "progress_goal": goal,
                "period_code": current_period_code,
                "period_count": period_count,
                "period_max": max_triggers_per_period,
                "period_limit_reached": period_count >= max_triggers_per_period,
                "target_daily_points": round(target_daily_points, 2),
                "winners": winners,
            }

    def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str = "",
        sort: str = "coins_desc",
    ) -> list[dict[str, Any]]:
        allowed_sorts = {
            "coins_desc": "u.coins DESC, u.user_id DESC",
            "coins_asc": "u.coins ASC, u.user_id ASC",
            "id_desc": "u.user_id DESC",
            "id_asc": "u.user_id ASC",
            "updated_desc": "u.updated_at DESC, u.user_id DESC",
        }
        order_by = allowed_sorts.get(sort, allowed_sorts["coins_desc"])

        where_sql = ""
        params: list[Any] = []
        if search:
            where_sql = """
                WHERE
                    CAST(u.user_id AS TEXT) LIKE ?
                    OR u.username LIKE ?
                    OR u.first_name LIKE ?
            """
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])

        query = f"""
            SELECT
                u.user_id,
                u.username,
                u.first_name,
                u.coins,
                u.updated_at,
                COALESCE(ur.is_trusted, 1) AS is_trusted,
                COALESCE(us.broadcast_enabled, 0) AS broadcast_enabled,
                us.activated_at AS activated_at
            FROM users u
            LEFT JOIN user_reliability ur ON ur.user_id = u.user_id
            LEFT JOIN user_settings us ON us.user_id = u.user_id
            {where_sql}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            items.append(
                {
                    "user_id": int(row["user_id"]),
                    "username": row["username"] or "",
                    "first_name": row["first_name"] or "",
                    "coins": int(row["coins"]),
                    "updated_at": row["updated_at"] or "",
                    "is_trusted": bool(int(row["is_trusted"])),
                    "broadcast_enabled": bool(int(row["broadcast_enabled"])),
                    "activated_at": row["activated_at"] or "",
                }
            )
        return items

    def count_users(self, search: str = "") -> int:
        where_sql = ""
        params: list[Any] = []
        if search:
            where_sql = """
                WHERE
                    CAST(user_id AS TEXT) LIKE ?
                    OR username LIKE ?
                    OR first_name LIKE ?
            """
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])

        query = f"""
            SELECT COUNT(*)
            FROM users
            {where_sql}
        """
        with self.connection() as conn:
            row = conn.execute(query, params).fetchone()
        return int(row[0]) if row else 0

    def get_user_language(self, user_id: int) -> str:
        with self.connection() as conn:
            self._ensure_user_settings_row(conn, user_id)
            row = conn.execute(
                """
                SELECT language_code
                FROM user_settings
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
            conn.commit()
        if row is None:
            return LANGUAGE_RU
        code = (row[0] or LANGUAGE_RU).lower()
        return code if code in {LANGUAGE_RU, LANGUAGE_EN} else LANGUAGE_RU

    def set_user_language(self, user_id: int, language_code: str) -> str:
        code = (language_code or "").lower()
        if code not in {LANGUAGE_RU, LANGUAGE_EN}:
            code = LANGUAGE_RU
        with self.connection() as conn:
            self._ensure_user_settings_row(conn, user_id)
            conn.execute(
                """
                UPDATE user_settings
                SET language_code = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (code, user_id),
            )
            conn.commit()
        return code

    def set_user_activated(self, user_id: int, enabled: bool = True) -> None:
        with self.connection() as conn:
            self._ensure_user_settings_row(conn, user_id)
            if enabled:
                conn.execute(
                    """
                    UPDATE user_settings
                    SET broadcast_enabled = 1,
                        activated_at = COALESCE(activated_at, CURRENT_TIMESTAMP),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (user_id,),
                )
            else:
                conn.execute(
                    """
                    UPDATE user_settings
                    SET broadcast_enabled = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (user_id,),
                )
            conn.commit()

    def list_broadcast_targets(self, activated_only: bool = True, limit: int = 50000) -> list[int]:
        where_sql = ""
        params: list[Any] = []
        if activated_only:
            where_sql = "WHERE us.broadcast_enabled = 1"

        query = f"""
            SELECT us.user_id
            FROM user_settings us
            {where_sql}
            ORDER BY us.user_id ASC
            LIMIT ?
        """
        params.append(max(1, int(limit)))
        with self.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [int(row[0]) for row in rows]

    def log_broadcast(
        self,
        text: str,
        activated_only: bool,
        sent_count: int,
        failed_count: int,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO broadcasts (text, activated_only, sent_count, failed_count)
                VALUES (?, ?, ?, ?)
                """,
                (text, 1 if activated_only else 0, sent_count, failed_count),
            )
            conn.commit()

    def list_broadcast_logs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, text, activated_only, sent_count, failed_count, created_at
                FROM broadcasts
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "text": row["text"] or "",
                "activated_only": bool(int(row["activated_only"])),
                "sent_count": int(row["sent_count"]),
                "failed_count": int(row["failed_count"]),
                "created_at": row["created_at"] or "",
            }
            for row in rows
        ]

    def set_referrer(
        self,
        referred_user_id: int,
        referrer_user_id: int,
        referral_bonus_amount: int,
        referral_bonus_limit: int,
    ) -> dict[str, Any]:
        if referred_user_id == referrer_user_id:
            return {"assigned": False, "bonus_awarded": False, "reason": "SELF"}
        if referral_bonus_amount < 0:
            referral_bonus_amount = 0
        referral_bonus_limit = max(0, referral_bonus_limit)

        with self.connection() as conn:
            existing = conn.execute(
                """
                SELECT referrer_user_id
                FROM referrals
                WHERE referred_user_id = ?
                """,
                (referred_user_id,),
            ).fetchone()
            if existing is not None:
                return {"assigned": False, "bonus_awarded": False, "reason": "ALREADY_SET"}

            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, coins)
                VALUES (?, '', '', 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    updated_at=CURRENT_TIMESTAMP
                """,
                (referrer_user_id,),
            )
            self._ensure_reliability_row(conn, referrer_user_id)
            self._ensure_user_settings_row(conn, referrer_user_id)

            conn.execute(
                """
                INSERT INTO referrals (referred_user_id, referrer_user_id, bonus_awarded)
                VALUES (?, ?, 0)
                """,
                (referred_user_id, referrer_user_id),
            )
            conn.execute(
                """
                INSERT INTO referral_commission_state (referred_user_id, referrer_user_id, remainder_percent)
                VALUES (?, ?, 0)
                ON CONFLICT(referred_user_id) DO UPDATE SET
                    referrer_user_id=excluded.referrer_user_id,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (referred_user_id, referrer_user_id),
            )

            count_row = conn.execute(
                """
                SELECT COUNT(*)
                FROM referrals
                WHERE referrer_user_id = ? AND bonus_awarded = 1
                """,
                (referrer_user_id,),
            ).fetchone()
            rewarded_count = int(count_row[0]) if count_row else 0
            bonus_awarded = False
            referrer_balance = 0
            if rewarded_count < referral_bonus_limit and referral_bonus_amount > 0:
                conn.execute(
                    """
                    UPDATE referrals
                    SET bonus_awarded = 1
                    WHERE referred_user_id = ?
                    """,
                    (referred_user_id,),
                )
                conn.execute(
                    """
                    UPDATE users
                    SET coins = coins + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (referral_bonus_amount, referrer_user_id),
                )
                conn.execute(
                    """
                    INSERT INTO coin_events (user_id, chat_id, message_id, source, amount)
                    VALUES (?, NULL, NULL, ?, ?)
                    """,
                    (referrer_user_id, SOURCE_REFERRAL_BONUS, referral_bonus_amount),
                )
                bonus_awarded = True

            balance_row = conn.execute(
                """
                SELECT coins
                FROM users
                WHERE user_id = ?
                """,
                (referrer_user_id,),
            ).fetchone()
            referrer_balance = int(balance_row[0]) if balance_row else 0
            conn.commit()

        return {
            "assigned": True,
            "bonus_awarded": bonus_awarded,
            "referrer_balance": referrer_balance,
            "reason": "OK",
        }

    def get_referral_summary(self, user_id: int) -> dict[str, Any]:
        with self.connection() as conn:
            total_row = conn.execute(
                """
                SELECT COUNT(*)
                FROM referrals
                WHERE referrer_user_id = ?
                """,
                (user_id,),
            ).fetchone()
            rewarded_row = conn.execute(
                """
                SELECT COUNT(*)
                FROM referrals
                WHERE referrer_user_id = ? AND bonus_awarded = 1
                """,
                (user_id,),
            ).fetchone()
            commission_row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM coin_events
                WHERE user_id = ? AND source = ?
                """,
                (user_id, SOURCE_REFERRAL_COMMISSION),
            ).fetchone()
        return {
            "total_referrals": int(total_row[0]) if total_row else 0,
            "rewarded_referrals": int(rewarded_row[0]) if rewarded_row else 0,
            "commission_total": int(commission_row[0]) if commission_row else 0,
        }

    def add_referral_commission(
        self,
        referred_user_id: int,
        referred_reward_amount: int,
        chat_id: int,
        message_id: int,
        percent: int = 10,
    ) -> tuple[int, Optional[int]]:
        if referred_reward_amount <= 0 or percent <= 0:
            return 0, None
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT referrer_user_id, remainder_percent
                FROM referral_commission_state
                WHERE referred_user_id = ?
                """,
                (referred_user_id,),
            ).fetchone()
            if row is None:
                return 0, None
            referrer_user_id = int(row[0])
            remainder = int(row[1]) if row[1] is not None else 0
            percent_units = referred_reward_amount * percent + remainder
            commission_amount = percent_units // 100
            new_remainder = percent_units % 100

            conn.execute(
                """
                UPDATE referral_commission_state
                SET remainder_percent = ?, updated_at = CURRENT_TIMESTAMP
                WHERE referred_user_id = ?
                """,
                (new_remainder, referred_user_id),
            )
            if commission_amount <= 0:
                conn.commit()
                return 0, referrer_user_id

            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, coins)
                VALUES (?, '', '', 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    updated_at=CURRENT_TIMESTAMP
                """,
                (referrer_user_id,),
            )
            self._ensure_reliability_row(conn, referrer_user_id)
            self._ensure_user_settings_row(conn, referrer_user_id)
            conn.execute(
                """
                UPDATE users
                SET coins = coins + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (commission_amount, referrer_user_id),
            )
            conn.execute(
                """
                INSERT INTO coin_events (user_id, chat_id, message_id, source, amount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    referrer_user_id,
                    chat_id,
                    message_id,
                    SOURCE_REFERRAL_COMMISSION,
                    commission_amount,
                ),
            )
            conn.commit()
        return commission_amount, referrer_user_id

    def is_feature_enabled(self, key: str, default: bool = False) -> bool:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT enabled
                FROM feature_flags
                WHERE key = ?
                """,
                (key,),
            ).fetchone()
        if row is None:
            return default
        return bool(int(row[0]))

    def set_feature_flag(self, key: str, enabled: bool) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO feature_flags (key, enabled, description, updated_at)
                VALUES (?, ?, '', CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    enabled=excluded.enabled,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (key, 1 if enabled else 0),
            )
            conn.commit()

    def list_feature_flags(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT key, enabled, description, updated_at
                FROM feature_flags
                ORDER BY key ASC
                """
            ).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            items.append(
                {
                    "key": row["key"],
                    "enabled": bool(int(row["enabled"])),
                    "description": row["description"] or "",
                    "updated_at": row["updated_at"] or "",
                }
            )
        return items

    def top_users(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT user_id, username, first_name, coins
                FROM users
                ORDER BY coins DESC, user_id ASC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return [
            {
                "user_id": int(row["user_id"]),
                "username": row["username"] or "",
                "first_name": row["first_name"] or "",
                "coins": int(row["coins"]),
            }
            for row in rows
        ]

    def top_admins(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.first_name,
                    COALESCE(SUM(e.amount), 0) AS tribute_total
                FROM users u
                JOIN coin_events e ON e.user_id = u.user_id
                WHERE e.source = ?
                GROUP BY u.user_id, u.username, u.first_name
                ORDER BY tribute_total DESC, u.user_id ASC
                LIMIT ?
                """,
                (SOURCE_OWNER_TRIBUTE, max(1, int(limit))),
            ).fetchall()
        return [
            {
                "user_id": int(row["user_id"]),
                "username": row["username"] or "",
                "first_name": row["first_name"] or "",
                "tribute_total": int(row["tribute_total"]),
            }
            for row in rows
        ]

    def top_referrers(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.first_name,
                    COUNT(r.referred_user_id) AS referrals_total,
                    COALESCE(SUM(CASE WHEN r.bonus_awarded = 1 THEN 1 ELSE 0 END), 0) AS rewarded_referrals,
                    COALESCE((
                        SELECT SUM(e.amount)
                        FROM coin_events e
                        WHERE e.user_id = u.user_id
                          AND e.source = ?
                    ), 0) AS commission_total
                FROM users u
                JOIN referrals r ON r.referrer_user_id = u.user_id
                GROUP BY u.user_id, u.username, u.first_name
                ORDER BY referrals_total DESC, commission_total DESC, u.user_id ASC
                LIMIT ?
                """,
                (SOURCE_REFERRAL_COMMISSION, max(1, int(limit))),
            ).fetchall()
        return [
            {
                "user_id": int(row["user_id"]),
                "username": row["username"] or "",
                "first_name": row["first_name"] or "",
                "referrals_total": int(row["referrals_total"]),
                "rewarded_referrals": int(row["rewarded_referrals"]),
                "commission_total": int(row["commission_total"]),
            }
            for row in rows
        ]

    def top_income_last_days(self, days: int = 5, limit: int = 50) -> list[dict[str, Any]]:
        safe_days = max(1, int(days))
        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.first_name,
                    COALESCE(SUM(CASE WHEN e.amount > 0 THEN e.amount ELSE 0 END), 0) AS income_total,
                    COALESCE(SUM(CASE WHEN e.source = ? THEN ABS(e.amount) ELSE 0 END), 0) AS transfer_out_total
                FROM users u
                JOIN coin_events e ON e.user_id = u.user_id
                WHERE e.created_at >= datetime('now', ?)
                GROUP BY u.user_id, u.username, u.first_name
                ORDER BY income_total DESC, u.user_id ASC
                LIMIT ?
                """,
                (
                    SOURCE_TRANSFER_OUT,
                    f"-{safe_days} days",
                    max(1, int(limit)),
                ),
            ).fetchall()
        return [
            {
                "user_id": int(row["user_id"]),
                "username": row["username"] or "",
                "first_name": row["first_name"] or "",
                "income_total": int(row["income_total"]),
                "transfer_out_total": int(row["transfer_out_total"]),
            }
            for row in rows
        ]

    def suspicious_users_report(
        self,
        days: int = 5,
        min_income: int = 5000,
        min_transfer_out: int = 3000,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        safe_days = max(1, int(days))
        safe_income = max(1, int(min_income))
        safe_transfer_out = max(1, int(min_transfer_out))
        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.first_name,
                    COALESCE(SUM(CASE WHEN e.amount > 0 THEN e.amount ELSE 0 END), 0) AS income_total,
                    COALESCE(SUM(CASE WHEN e.source = ? THEN ABS(e.amount) ELSE 0 END), 0) AS transfer_out_total,
                    COUNT(*) AS events_count
                FROM users u
                JOIN coin_events e ON e.user_id = u.user_id
                WHERE e.created_at >= datetime('now', ?)
                GROUP BY u.user_id, u.username, u.first_name
                HAVING income_total >= ? OR transfer_out_total >= ?
                ORDER BY income_total DESC, transfer_out_total DESC, u.user_id ASC
                LIMIT ?
                """,
                (
                    SOURCE_TRANSFER_OUT,
                    f"-{safe_days} days",
                    safe_income,
                    safe_transfer_out,
                    max(1, int(limit)),
                ),
            ).fetchall()
        return [
            {
                "user_id": int(row["user_id"]),
                "username": row["username"] or "",
                "first_name": row["first_name"] or "",
                "income_total": int(row["income_total"]),
                "transfer_out_total": int(row["transfer_out_total"]),
                "events_count": int(row["events_count"]),
            }
            for row in rows
        ]

    def income_timeline(self, days: int = 7) -> list[dict[str, Any]]:
        safe_days = min(max(1, int(days)), 60)
        with self.connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    date(created_at) AS day,
                    COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) AS income_total,
                    COALESCE(SUM(CASE WHEN source = ? THEN ABS(amount) ELSE 0 END), 0) AS transfer_out_total
                FROM coin_events
                WHERE created_at >= datetime('now', ?)
                GROUP BY date(created_at)
                ORDER BY day ASC
                """,
                (
                    SOURCE_TRANSFER_OUT,
                    f"-{safe_days} days",
                ),
            ).fetchall()

        by_day: dict[str, tuple[int, int]] = {}
        for row in rows:
            day = row["day"] or ""
            by_day[day] = (
                int(row["income_total"]),
                int(row["transfer_out_total"]),
            )

        today = datetime.now().date()
        start_day = today - timedelta(days=safe_days - 1)
        items: list[dict[str, Any]] = []
        for idx in range(safe_days):
            day_value = start_day + timedelta(days=idx)
            key = day_value.strftime("%Y-%m-%d")
            income_total, transfer_out_total = by_day.get(key, (0, 0))
            items.append(
                {
                    "day": key,
                    "income_total": income_total,
                    "transfer_out_total": transfer_out_total,
                }
            )
        return items

    def transfer_coins(
        self,
        sender_id: int,
        sender_username: str,
        sender_first_name: str,
        recipient_id: int,
        recipient_username: str,
        recipient_first_name: str,
        amount: int,
        chat_id: int,
        message_id: int,
    ) -> tuple[bool, int, int, str]:
        if amount <= 0:
            return False, 0, 0, "INVALID_AMOUNT"
        if sender_id == recipient_id:
            return False, 0, 0, "SELF_TRANSFER"

        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, coins)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (sender_id, sender_username, sender_first_name),
            )
            self._ensure_reliability_row(conn, sender_id)
            self._ensure_user_settings_row(conn, sender_id)

            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, coins)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (recipient_id, recipient_username, recipient_first_name),
            )
            self._ensure_reliability_row(conn, recipient_id)
            self._ensure_user_settings_row(conn, recipient_id)

            sender_row = conn.execute(
                """
                SELECT coins
                FROM users
                WHERE user_id = ?
                """,
                (sender_id,),
            ).fetchone()
            sender_balance = int(sender_row[0]) if sender_row else 0
            if sender_balance < amount:
                recipient_row = conn.execute(
                    """
                    SELECT coins
                    FROM users
                    WHERE user_id = ?
                    """,
                    (recipient_id,),
                ).fetchone()
                recipient_balance = int(recipient_row[0]) if recipient_row else 0
                conn.commit()
                return False, sender_balance, recipient_balance, "INSUFFICIENT_FUNDS"

            conn.execute(
                """
                UPDATE users
                SET coins = coins - ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (amount, sender_id),
            )
            conn.execute(
                """
                UPDATE users
                SET coins = coins + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (amount, recipient_id),
            )
            conn.execute(
                """
                INSERT INTO coin_events (user_id, chat_id, message_id, source, amount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sender_id, chat_id, message_id, SOURCE_TRANSFER_OUT, -amount),
            )
            conn.execute(
                """
                INSERT INTO coin_events (user_id, chat_id, message_id, source, amount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (recipient_id, chat_id, message_id, SOURCE_TRANSFER_IN, amount),
            )

            new_sender_row = conn.execute(
                """
                SELECT coins
                FROM users
                WHERE user_id = ?
                """,
                (sender_id,),
            ).fetchone()
            new_recipient_row = conn.execute(
                """
                SELECT coins
                FROM users
                WHERE user_id = ?
                """,
                (recipient_id,),
            ).fetchone()
            conn.commit()

        new_sender_balance = int(new_sender_row[0]) if new_sender_row else 0
        new_recipient_balance = int(new_recipient_row[0]) if new_recipient_row else 0
        return True, new_sender_balance, new_recipient_balance, "OK"
