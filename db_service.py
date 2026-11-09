"""
CaseResolutionAI - Database & Authentication Service
Provides secure local SQLite persistence, user authentication, and case record management.
"""

import sqlite3
import hashlib
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "case_resolution.db")


def get_db_connection():
    """Returns a SQLite connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hashes a password securely using PBKDF2 with SHA-256 and a unique salt."""
    if salt is None:
        salt = os.urandom(16).hex()
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    return key.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies a plain password against the stored PBKDF2 hash."""
    test_hash, _ = hash_password(password, salt)
    return test_hash == stored_hash


def init_db():
    """Initializes the database schema if tables do not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # Cases Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        customer_name TEXT,
        product_name TEXT NOT NULL,
        product_category TEXT NOT NULL,
        seller_name TEXT NOT NULL,
        purchase_amount REAL NOT NULL,
        purchase_date TEXT,
        delivery_date TEXT,
        problem_category TEXT NOT NULL,
        status TEXT NOT NULL,
        relief_sought TEXT,
        support_ticket_ref TEXT,
        seller_email TEXT,
        seller_promises TEXT,
        refund_status TEXT,
        user_statement TEXT NOT NULL,
        timeline_json TEXT,
        evidence_json TEXT,
        metadata_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    conn.commit()
    conn.close()


def register_user(username: str, email: str, password: str, full_name: str = "") -> Dict[str, Any]:
    """Registers a new user with secure password hashing."""
    init_db()
    username = username.strip().lower()
    email = email.strip().lower()

    if not username or not email or not password:
        return {"success": False, "error": "Username, email, and password are required."}

    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters long."}

    pwd_hash, salt = hash_password(password)
    user_id = str(uuid.uuid4())
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (id, username, email, password_hash, salt, full_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, email, pwd_hash, salt, full_name.strip(), now_str)
        )
        conn.commit()
        return {
            "success": True,
            "user": {
                "id": user_id,
                "username": username,
                "email": email,
                "full_name": full_name.strip()
            }
        }
    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if "username" in err_msg:
            return {"success": False, "error": "This username is already taken. Please choose another."}
        elif "email" in err_msg:
            return {"success": False, "error": "An account with this email already exists."}
        return {"success": False, "error": f"Registration error: {str(e)}"}
    finally:
        conn.close()


def authenticate_user(username_or_email: str, password: str) -> Dict[str, Any]:
    """Authenticates a user via username or email."""
    init_db()
    identifier = username_or_email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (identifier, identifier)
    )
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        return {"success": False, "error": "Invalid username or password."}

    if verify_password(password, user_row["password_hash"], user_row["salt"]):
        return {
            "success": True,
            "user": {
                "id": user_row["id"],
                "username": user_row["username"],
                "email": user_row["email"],
                "full_name": user_row["full_name"]
            }
        }
    else:
        return {"success": False, "error": "Invalid username or password."}


def reset_password(email: str, new_password: str) -> Dict[str, Any]:
    """Resets a user's password."""
    init_db()
    if len(new_password) < 6:
        return {"success": False, "error": "New password must be at least 6 characters long."}

    email = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": "No account found with this email."}

    pwd_hash, salt = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE email = ?", (pwd_hash, salt, email))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Password reset successfully. You can now log in."}


def save_case_to_db(case_dict: Dict[str, Any], user_id: str) -> bool:
    """Inserts or updates a case in the database."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    case_id = case_dict.get("id")

    # Serialize JSON fields safely
    timeline_str = json.dumps(case_dict.get("timeline", []))
    evidence_str = json.dumps(case_dict.get("evidence_items", []))
    metadata_str = json.dumps(case_dict.get("metadata", {}))

    cursor.execute("SELECT id FROM cases WHERE id = ? AND user_id = ?", (case_id, user_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE cases SET
                title = ?, customer_name = ?, product_name = ?, product_category = ?,
                seller_name = ?, purchase_amount = ?, purchase_date = ?, delivery_date = ?,
                problem_category = ?, status = ?, relief_sought = ?, support_ticket_ref = ?,
                seller_email = ?, seller_promises = ?, refund_status = ?, user_statement = ?,
                timeline_json = ?, evidence_json = ?, metadata_json = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (
            case_dict.get("title", "Untitled Case"),
            case_dict.get("customer_name", "Consumer"),
            case_dict.get("product_name", ""),
            case_dict.get("product_category", "General Consumer Goods"),
            case_dict.get("seller_name", ""),
            float(case_dict.get("purchase_amount", 0.0)),
            str(case_dict.get("purchase_date", "")),
            str(case_dict.get("delivery_date", case_dict.get("incident_date", ""))),
            case_dict.get("problem_category", "General Complaint"),
            case_dict.get("status", "Evidence Documented"),
            case_dict.get("relief_sought", ""),
            case_dict.get("support_ticket_ref", ""),
            case_dict.get("seller_email", ""),
            case_dict.get("seller_promises", ""),
            case_dict.get("refund_status", ""),
            case_dict.get("user_statement", ""),
            timeline_str,
            evidence_str,
            metadata_str,
            now_str,
            case_id,
            user_id
        ))
    else:
        cursor.execute("""
            INSERT INTO cases (
                id, user_id, title, customer_name, product_name, product_category,
                seller_name, purchase_amount, purchase_date, delivery_date,
                problem_category, status, relief_sought, support_ticket_ref,
                seller_email, seller_promises, refund_status, user_statement,
                timeline_json, evidence_json, metadata_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id,
            user_id,
            case_dict.get("title", "Untitled Case"),
            case_dict.get("customer_name", "Consumer"),
            case_dict.get("product_name", ""),
            case_dict.get("product_category", "General Consumer Goods"),
            case_dict.get("seller_name", ""),
            float(case_dict.get("purchase_amount", 0.0)),
            str(case_dict.get("purchase_date", "")),
            str(case_dict.get("delivery_date", case_dict.get("incident_date", ""))),
            case_dict.get("problem_category", "General Complaint"),
            case_dict.get("status", "Evidence Documented"),
            case_dict.get("relief_sought", ""),
            case_dict.get("support_ticket_ref", ""),
            case_dict.get("seller_email", ""),
            case_dict.get("seller_promises", ""),
            case_dict.get("refund_status", ""),
            case_dict.get("user_statement", ""),
            timeline_str,
            evidence_str,
            metadata_str,
            case_dict.get("created_at", now_str),
            now_str
        ))

    conn.commit()
    conn.close()
    return True


def get_user_cases_from_db(user_id: str) -> List[Dict[str, Any]]:
    """Retrieves all cases belonging to a user, converting JSON fields back to dicts/lists."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    cases = []
    for r in rows:
        c = dict(r)
        # Parse JSON fields
        try:
            c["timeline"] = json.loads(c.get("timeline_json") or "[]")
        except Exception:
            c["timeline"] = []
        try:
            c["evidence_items"] = json.loads(c.get("evidence_json") or "[]")
        except Exception:
            c["evidence_items"] = []
        try:
            c["metadata"] = json.loads(c.get("metadata_json") or "{}")
        except Exception:
            c["metadata"] = {}
        cases.append(c)
    return cases


def delete_case_from_db(case_id: str, user_id: str) -> bool:
    """Deletes a case belonging to the specified user."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cases WHERE id = ? AND user_id = ?", (case_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

