import os
import re
import sqlite3
import secrets
import hashlib
from typing import Optional

DB_PATH = os.path.join("data", "agent3000.db")

ROLES = ["admin", "desarrollador", "analista", "financiero", "general"]

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()

def _make_salt() -> str:
    return secrets.token_hex(16)

def init_auth():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "t_users" (
                "id" TEXT PRIMARY KEY,
                "username" TEXT UNIQUE NOT NULL,
                "password_hash" TEXT NOT NULL,
                "salt" TEXT NOT NULL,
                "role" TEXT NOT NULL,
                "nombre" TEXT,
                "email" TEXT,
                "activo" INTEGER DEFAULT 1,
                "created_at" TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    finally:
        conn.close()

def register_user(username: str, password: str, role: str, nombre: str = "", email: str = "") -> tuple[bool, str]:
    if not username.strip() or not password.strip():
        return False, "Usuario y contraseña son requeridos."
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    if role not in ROLES:
        return False, f"Rol inválido. Roles disponibles: {', '.join(ROLES)}"

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM "t_users" WHERE username = ?', (username,))
        if cur.fetchone():
            return False, "El usuario ya existe."

        user_id = "u_" + secrets.token_hex(8)
        salt = _make_salt()
        password_hash = _hash_password(password, salt)

        cur.execute(
            'INSERT INTO "t_users" ("id", "username", "password_hash", "salt", "role", "nombre", "email") VALUES (?, ?, ?, ?, ?, ?, ?)',
            (user_id, username, password_hash, salt, role, nombre, email)
        )
        conn.commit()
        return True, f"Usuario '{username}' creado con rol '{role}'."
    except Exception as e:
        return False, f"Error al crear usuario: {e}"
    finally:
        conn.close()

def verify_user(username: str, password: str) -> tuple[bool, dict]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT id, username, password_hash, salt, role, nombre, email, activo FROM "t_users" WHERE username = ?',
            (username,)
        )
        row = cur.fetchone()
        if not row:
            return False, {}
        user_id, username_db, stored_hash, salt, role, nombre, email, activo = row
        if not activo:
            return False, {}
        if stored_hash != _hash_password(password, salt):
            return False, {}
        return True, {
            "id": user_id,
            "username": username_db,
            "role": role,
            "nombre": nombre or username_db,
            "email": email or "",
        }
    finally:
        conn.close()

def get_all_users() -> list[dict]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, username, role, nombre, email, activo, created_at FROM "t_users" ORDER BY created_at DESC')
        rows = cur.fetchall()
        return [
            {"id": r[0], "username": r[1], "role": r[2], "nombre": r[3], "email": r[4], "activo": bool(r[5]), "created_at": r[6]}
            for r in rows
        ]
    finally:
        conn.close()

def toggle_user(user_id: str, activo: bool) -> bool:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute('UPDATE "t_users" SET activo = ? WHERE id = ?', (int(activo), user_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def delete_user(user_id: str) -> bool:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "t_users" WHERE id = ?', (user_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def update_user_role(user_id: str, new_role: str) -> bool:
    if new_role not in ROLES:
        return False
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute('UPDATE "t_users" SET role = ? WHERE id = ?', (new_role, user_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

init_auth()

# Create default admin on first run
conn = get_conn()
try:
    cur = conn.cursor()
    cur.execute('SELECT id FROM "t_users" WHERE role = "admin" LIMIT 1')
    if not cur.fetchone():
        user_id = "u_admin001"
        salt = _make_salt()
        password_hash = _hash_password("admin123", salt)
        cur.execute(
            'INSERT INTO "t_users" ("id", "username", "password_hash", "salt", "role", "nombre", "email") VALUES (?, ?, ?, ?, ?, ?, ?)',
            (user_id, "admin", password_hash, salt, "admin", "Administrador", "admin@agent3000.local")
        )
        conn.commit()
finally:
    conn.close()
