import sqlite3
import datetime
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "support_bot.db")


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # User table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_auto_reply TIMESTAMP
        )
    """)

    # Message mapping table: links admin forwarded message IDs to customer IDs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_mappings (
            admin_msg_id INTEGER PRIMARY KEY,
            customer_chat_id INTEGER NOT NULL,
            customer_msg_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Default settings
    default_settings = {
        "auto_reply_enabled": "true",
        "welcome_message": """👋 𝐇𝐞𝐥𝐥𝐨 𝐃𝐞𝐚𝐫 𝐁𝐨𝐧𝐠 👋 𝐰𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 
𝐏𝐑𝐎 𝐒𝐄𝐑𝐕𝐈𝐂𝐄 𝐏𝐑𝐄𝐌𝐈𝐔𝐌

សូមផ្ញើសារនៅទីនេះ ក្រុមការងារនឹងឆ្លើយតបបងអូនឱ្យបានលឿនបំផុត 

⚡️Instead Delivery ⚡️ ⏰ Support Hours:9AM–10PM
2~10 minutes during working hours, no later than 12 hours.
📎Website: proservicepremium.site.je""",
        "auto_reply_message": """👋 𝐇𝐞𝐥𝐥𝐨 𝐃𝐞𝐚𝐫 𝐁𝐨𝐧𝐠 👋 𝐰𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 
𝐏𝐑𝐎 𝐒𝐄𝐑𝐕𝐈𝐂𝐄 𝐏𝐑𝐄𝐌𝐈𝐔𝐌

សូមផ្ញើសារនៅទីនេះ ក្រុមការងារនឹងឆ្លើយតបបងអូនឱ្យបានលឿនបំផុត 

⚡️Instead Delivery ⚡️ ⏰ Support Hours:9AM–10PM
2~10 minutes during working hours, no later than 12 hours.
📎Website: proservicepremium.site.je"""
    }

    for key, val in default_settings.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, val))

    conn.commit()
    conn.close()


def save_or_update_user(user_id: int, first_name: str, last_name: str, username: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO users (user_id, first_name, last_name, username, joined_at, last_active)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            first_name=excluded.first_name,
            last_name=excluded.last_name,
            username=excluded.username,
            last_active=excluded.last_active
    """, (user_id, first_name or "", last_name or "", username or "", now, now))
    conn.commit()
    conn.close()


def should_send_autoreply(user_id: int, cooldown_minutes: int = 15) -> bool:
    if get_setting("auto_reply_enabled", "true").lower() != "true":
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_auto_reply FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["last_auto_reply"]:
        return True

    try:
        last_time = datetime.datetime.fromisoformat(row["last_auto_reply"])
        diff = (datetime.datetime.utcnow() - last_time).total_seconds() / 60
        return diff >= cooldown_minutes
    except Exception:
        return True


def record_autoreply(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cursor.execute("UPDATE users SET last_auto_reply = ? WHERE user_id = ?", (now, user_id))
    conn.commit()
    conn.close()


def save_message_mapping(admin_msg_id: int, customer_chat_id: int, customer_msg_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO message_mappings (admin_msg_id, customer_chat_id, customer_msg_id)
        VALUES (?, ?, ?)
    """, (admin_msg_id, customer_chat_id, customer_msg_id))
    conn.commit()
    conn.close()


def get_customer_by_admin_msg(admin_msg_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT customer_chat_id, customer_msg_id FROM message_mappings WHERE admin_msg_id = ?", (admin_msg_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["customer_chat_id"], row["customer_msg_id"]
    return None, None


def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get_user_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS cnt FROM users")
    cnt = cursor.fetchone()["cnt"]
    conn.close()
    return cnt


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, first_name, last_name, username, last_active FROM users ORDER BY last_active DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

