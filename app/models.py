import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

def get_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str) -> None:
    with get_db(db_path) as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS smtp_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                host TEXT NOT NULL DEFAULT 'smtp.example.com',
                port INTEGER NOT NULL DEFAULT 587,
                username TEXT NOT NULL DEFAULT '',
                password TEXT NOT NULL DEFAULT '',
                use_tls INTEGER NOT NULL DEFAULT 1,
                use_ssl INTEGER NOT NULL DEFAULT 0,
                sender_name TEXT NOT NULL DEFAULT 'CleanMail Service',
                sender_email TEXT NOT NULL DEFAULT 'noreply@example.com',
                dry_run INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                body_preview TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                is_dry_run INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            INSERT OR IGNORE INTO smtp_settings (id, host, port, username, password, use_tls, use_ssl, sender_name, sender_email, dry_run)
            VALUES (1, 'smtp.example.com', 587, 'demo@example.com', 'demopass', 1, 0, 'CleanMail Demo', 'noreply@example.com', 1);
        ''')
        conn.commit()

def get_settings(db_path: str) -> Dict[str, Any]:
    with get_db(db_path) as conn:
        cur = conn.execute("SELECT * FROM smtp_settings WHERE id = 1")
        row = cur.fetchone()
        if row:
            return dict(row)
        return {}

def update_settings(db_path: str, data: Dict[str, Any]) -> None:
    with get_db(db_path) as conn:
        conn.execute('''
            UPDATE smtp_settings SET
                host = ?,
                port = ?,
                username = ?,
                password = ?,
                use_tls = ?,
                use_ssl = ?,
                sender_name = ?,
                sender_email = ?,
                dry_run = ?
            WHERE id = 1
        ''', (
            data.get("host", "smtp.example.com"),
            int(data.get("port", 587)),
            data.get("username", ""),
            data.get("password", ""),
            1 if data.get("use_tls") else 0,
            1 if data.get("use_ssl") else 0,
            data.get("sender_name", "CleanMail"),
            data.get("sender_email", "noreply@example.com"),
            1 if data.get("dry_run") else 0
        ))
        conn.commit()

def record_log(db_path: str, recipient: str, subject: str, body_preview: str, status: str, error: Optional[str], is_dry_run: bool) -> int:
    with get_db(db_path) as conn:
        cur = conn.execute('''
            INSERT INTO email_logs (recipient, subject, body_preview, status, error_message, is_dry_run)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (recipient, subject, body_preview[:150], status, error, 1 if is_dry_run else 0))
        conn.commit()
        return cur.lastrowid

def get_logs(db_path: str, limit: int = 50) -> List[Dict[str, Any]]:
    with get_db(db_path) as conn:
        cur = conn.execute("SELECT * FROM email_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]
