"""
Additive schema changes for existing databases (no Alembic).

Safe to run on every application startup; steps are idempotent where possible.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from app.core.database import engine

logger = logging.getLogger(__name__)


def _has_column(table: str, column: str) -> bool:
    insp = inspect(engine)
    if not insp.has_table(table):
        return False
    return any(c["name"] == column for c in insp.get_columns(table))


def _execute(sql: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql))


def _user_count() -> int:
    insp = inspect(engine)
    if not insp.has_table("users"):
        return 0
    with engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0


def _backfill_user_id(table: str) -> None:
    n = _user_count()
    if n == 0:
        _execute(f"DELETE FROM {table}")
        return
    if n == 1:
        _execute(
            f"""
            UPDATE {table} SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1)
            WHERE user_id IS NULL
            """
        )
    else:
        _execute(f"DELETE FROM {table} WHERE user_id IS NULL")


def _add_user_id_column(table: str) -> None:
    if _has_column(table, "user_id"):
        return
    dialect = engine.dialect.name
    if dialect == "postgresql":
        _execute(
            f"ALTER TABLE {table} ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"
        )
    else:
        # SQLite: skip inline REFERENCES on ADD COLUMN (not universally supported)
        _execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")
    _backfill_user_id(table)
    if dialect == "postgresql":
        try:
            _execute(f"ALTER TABLE {table} ALTER COLUMN user_id SET NOT NULL")
        except Exception:
            logger.warning("Could not set NOT NULL on %s.user_id", table)


def _migrate_incomes_recurrence() -> None:
    if not _has_column("incomes", "recurrence_frequency"):
        dialect = engine.dialect.name
        if dialect == "postgresql":
            _execute(
                "ALTER TABLE incomes ADD COLUMN recurrence_frequency VARCHAR(20) NOT NULL DEFAULT 'monthly'"
            )
        else:
            _execute("ALTER TABLE incomes ADD COLUMN recurrence_frequency VARCHAR(20) DEFAULT 'monthly'")
        if _has_column("incomes", "is_recurring"):
            _execute(
                """
                UPDATE incomes SET recurrence_frequency = CASE
                    WHEN is_recurring = 1 OR is_recurring = true OR is_recurring = 'true' THEN 'fortnightly'
                    ELSE 'monthly'
                END
                """
            )
        if not _has_column("incomes", "recurrence_note"):
            _execute("ALTER TABLE incomes ADD COLUMN recurrence_note VARCHAR(255)")
        if _has_column("incomes", "recurrence_detail"):
            _execute(
                "UPDATE incomes SET recurrence_note = COALESCE(recurrence_note, recurrence_detail) "
                "WHERE recurrence_detail IS NOT NULL"
            )
    elif not _has_column("incomes", "recurrence_note"):
        _execute("ALTER TABLE incomes ADD COLUMN recurrence_note VARCHAR(255)")


def _migrate_expenses_recurrence() -> None:
    if not _has_column("expenses", "recurrence_frequency"):
        _execute(
            "ALTER TABLE expenses ADD COLUMN recurrence_frequency VARCHAR(20) DEFAULT 'monthly'"
        )
        _execute("UPDATE expenses SET recurrence_frequency = 'monthly' WHERE recurrence_frequency IS NULL")
        if engine.dialect.name == "postgresql":
            try:
                _execute(
                    "ALTER TABLE expenses ALTER COLUMN recurrence_frequency SET NOT NULL"
                )
            except Exception:
                pass
    if not _has_column("expenses", "recurrence_note"):
        _execute("ALTER TABLE expenses ADD COLUMN recurrence_note VARCHAR(255)")


def _migrate_users_google_sub() -> None:
    """Add nullable google_sub for Google Sign-In linking."""
    if _has_column("users", "google_sub"):
        return
    _execute("ALTER TABLE users ADD COLUMN google_sub VARCHAR(255)")
    try:
        _execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_sub_unique "
            "ON users (google_sub) WHERE google_sub IS NOT NULL"
        )
    except Exception:
        logger.warning("Could not create partial unique index on users.google_sub", exc_info=True)


def _migrate_debt_payments() -> None:
    if not _has_column("debts", "payment_amount"):
        amt_type = "DOUBLE PRECISION" if engine.dialect.name == "postgresql" else "REAL"
        _execute(f"ALTER TABLE debts ADD COLUMN payment_amount {amt_type}")
    if not _has_column("debts", "payment_frequency"):
        _execute("ALTER TABLE debts ADD COLUMN payment_frequency VARCHAR(20)")
    if not _has_column("debts", "payment_note"):
        _execute("ALTER TABLE debts ADD COLUMN payment_note VARCHAR(255)")


def _drop_legacy_admin_login_challenges_table() -> None:
    """Remove obsolete admin_login_challenges table from older deployments."""
    insp = inspect(engine)
    if not insp.has_table("admin_login_challenges"):
        return
    try:
        _execute("DROP TABLE IF EXISTS admin_login_challenges")
        logger.info("Dropped legacy admin_login_challenges table.")
    except Exception:
        logger.warning("Could not drop admin_login_challenges", exc_info=True)


def apply_schema_migrations() -> None:
    try:
        insp = inspect(engine)
        if not insp.has_table("users"):
            return

        for tbl in ("incomes", "expenses", "assets", "debts", "stock_holdings"):
            if insp.has_table(tbl):
                _add_user_id_column(tbl)
                insp = inspect(engine)

        _migrate_incomes_recurrence()
        _migrate_expenses_recurrence()
        _migrate_debt_payments()
        _migrate_users_google_sub()
        _drop_legacy_admin_login_challenges_table()

        logger.info("Schema migrations check completed.")
    except Exception:
        logger.exception("Schema migration failed (non-fatal).")
