use anyhow::Result;
use rusqlite::{Connection, params};
use std::path::Path;
use crate::models::Transaction;

pub fn init_db(path: &Path) -> Result<()> {
    let conn = Connection::open(path)?;
    conn.execute_batch("
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            merchant_name TEXT NOT NULL,
            merchant_logo_url TEXT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            running_balance REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            account_id TEXT NOT NULL,
            account_name TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '[]',
            is_anomaly INTEGER NOT NULL DEFAULT 0,
            anomaly_reason TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_txns_date     ON transactions(date DESC);
        CREATE INDEX IF NOT EXISTS idx_txns_category ON transactions(category);
        CREATE INDEX IF NOT EXISTS idx_txns_account  ON transactions(account_id);

        CREATE TABLE IF NOT EXISTS holdings (
            ticker           TEXT PRIMARY KEY,
            name             TEXT NOT NULL,
            units            REAL NOT NULL,
            avg_cost_basis   REAL NOT NULL,
            current_price    REAL NOT NULL,
            previous_close   REAL NOT NULL,
            updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            id           TEXT PRIMARY KEY,
            title        TEXT NOT NULL,
            body         TEXT NOT NULL,
            confidence   REAL NOT NULL,
            category     TEXT NOT NULL,
            priority     TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'pending',
            generated_at TEXT NOT NULL,
            mcp_calls    TEXT NOT NULL DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id         TEXT PRIMARY KEY,
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            mcp_calls  TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    ")?;
    Ok(())
}

pub fn get_connection(db_path: &Path) -> Result<Connection> {
    let conn = Connection::open(db_path)?;
    conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")?;
    Ok(conn)
}

// ── Transactions ──────────────────────────────────────────────────────────────

pub fn insert_transaction(conn: &Connection, tx: &Transaction) -> Result<()> {
    let tags_json = serde_json::to_string(&tx.tags)?;
    conn.execute(
        "INSERT OR REPLACE INTO transactions
            (id, date, merchant_name, merchant_logo_url, description, amount,
             running_balance, category, subcategory, account_id, account_name,
             tags, is_anomaly, anomaly_reason)
         VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14)",
        params![
            tx.id,
            tx.date.to_rfc3339(),
            tx.merchant_name,
            tx.merchant_logo_url,
            tx.description,
            tx.amount,
            tx.running_balance,
            tx.category,
            tx.subcategory,
            tx.account_id,
            tx.account_name,
            tags_json,
            tx.is_anomaly as i64,
            tx.anomaly_reason,
        ],
    )?;
    Ok(())
}

pub struct TxQuery<'a> {
    pub limit: i64,
    pub offset: i64,
    pub category: Option<&'a str>,
    pub date_from: Option<&'a str>,
    pub date_to: Option<&'a str>,
    pub account_id: Option<&'a str>,
}

pub fn query_transactions(conn: &Connection, q: &TxQuery) -> Result<Vec<Transaction>> {
    let mut where_clauses = vec!["1=1"];
    if q.category.is_some() { where_clauses.push("category = ?3"); }
    if q.date_from.is_some() { where_clauses.push("date >= ?4"); }
    if q.date_to.is_some()   { where_clauses.push("date <= ?5"); }
    if q.account_id.is_some(){ where_clauses.push("account_id = ?6"); }

    let sql = format!(
        "SELECT id,date,merchant_name,merchant_logo_url,description,amount,
                running_balance,category,subcategory,account_id,account_name,
                tags,is_anomaly,anomaly_reason
         FROM transactions
         WHERE {}
         ORDER BY date DESC
         LIMIT ?1 OFFSET ?2",
        where_clauses.join(" AND ")
    );

    let mut stmt = conn.prepare(&sql)?;
    let rows = stmt.query_map(
        params![
            q.limit,
            q.offset,
            q.category.unwrap_or(""),
            q.date_from.unwrap_or(""),
            q.date_to.unwrap_or(""),
            q.account_id.unwrap_or(""),
        ],
        row_to_transaction,
    )?;

    let mut txns = Vec::new();
    for row in rows {
        txns.push(row?);
    }
    Ok(txns)
}

fn row_to_transaction(row: &rusqlite::Row) -> rusqlite::Result<Transaction> {
    use chrono::DateTime;
    let date_str: String = row.get(1)?;
    let tags_json: String = row.get(11)?;
    Ok(Transaction {
        id: row.get(0)?,
        date: DateTime::parse_from_rfc3339(&date_str)
            .map(|d| d.with_timezone(&chrono::Utc))
            .unwrap_or_default(),
        merchant_name: row.get(2)?,
        merchant_logo_url: row.get(3)?,
        description: row.get(4)?,
        amount: row.get(5)?,
        running_balance: row.get(6)?,
        category: row.get(7)?,
        subcategory: row.get(8)?,
        account_id: row.get(9)?,
        account_name: row.get(10)?,
        tags: serde_json::from_str(&tags_json).unwrap_or_default(),
        is_anomaly: row.get::<_, i64>(12)? != 0,
        anomaly_reason: row.get(13)?,
    })
}

// ── Aggregate helpers ─────────────────────────────────────────────────────────

pub struct AggregateResult {
    pub sum: f64,
    pub avg: f64,
    pub min: f64,
    pub max: f64,
    pub count: i64,
}

pub fn aggregate_transactions(
    conn: &Connection,
    category: Option<&str>,
    date_from: &str,
    date_to: &str,
) -> Result<AggregateResult> {
    let (cat_clause, cat_param): (&str, &str) = if category.is_some() {
        ("AND category = ?3", category.unwrap())
    } else {
        ("", "")
    };

    let sql = format!(
        "SELECT
            COALESCE(SUM(ABS(amount)), 0),
            COALESCE(AVG(ABS(amount)), 0),
            COALESCE(MIN(ABS(amount)), 0),
            COALESCE(MAX(ABS(amount)), 0),
            COUNT(*)
         FROM transactions
         WHERE amount < 0
           AND date >= ?1
           AND date <= ?2
           {}",
        cat_clause
    );

    let row = conn.query_row(
        &sql,
        params![date_from, date_to, cat_param],
        |row| Ok(AggregateResult {
            sum: row.get(0)?,
            avg: row.get(1)?,
            min: row.get(2)?,
            max: row.get(3)?,
            count: row.get(4)?,
        }),
    )?;
    Ok(row)
}

pub fn get_monthly_cashflow(conn: &Connection, months_back: i64) -> Result<Vec<(String, f64, f64)>> {
    let sql = "
        SELECT
            strftime('%Y-%m', date) as month,
            COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as income,
            COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as expenses
        FROM transactions
        WHERE date >= date('now', ?1 || ' months')
        GROUP BY month
        ORDER BY month ASC";

    let offset = format!("-{}", months_back);
    let mut stmt = conn.prepare(sql)?;
    let rows = stmt.query_map(params![offset], |row| {
        Ok((row.get::<_, String>(0)?, row.get(1)?, row.get(2)?))
    })?;

    let mut result = Vec::new();
    for row in rows {
        result.push(row?);
    }
    Ok(result)
}

// ── Settings ──────────────────────────────────────────────────────────────────

pub fn get_setting(conn: &Connection, key: &str) -> Result<Option<String>> {
    let result = conn.query_row(
        "SELECT value FROM settings WHERE key = ?1",
        params![key],
        |row| row.get(0),
    );
    match result {
        Ok(v) => Ok(Some(v)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

pub fn set_setting(conn: &Connection, key: &str, value: &str) -> Result<()> {
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?1, ?2)",
        params![key, value],
    )?;
    Ok(())
}

// ── Data wipe ─────────────────────────────────────────────────────────────────

pub fn wipe_all_data(conn: &Connection) -> Result<()> {
    conn.execute_batch("
        DELETE FROM transactions;
        DELETE FROM holdings;
        DELETE FROM recommendations;
        DELETE FROM chat_messages;
        DELETE FROM settings;
    ")?;
    Ok(())
}
