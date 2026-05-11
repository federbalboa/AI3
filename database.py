import os
import re
import sqlite3
import pandas as pd

DB_PATH = os.path.join("data", "agent3000.db")

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def _sanitize(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', name).strip('_').lower()

def _table_name(client_or_section: str, filename_stem: str) -> str:
    parts = []
    if client_or_section and client_or_section != "Chat General":
        parts.append(_sanitize(client_or_section))
    stem = _sanitize(filename_stem.replace('.csv', '').replace('.xlsx', ''))
    parts.append(stem)
    return 't_' + '_'.join(parts)

def ensure_table(table_name: str, headers: str = "ID,Cliente,Proyecto,Monto,Fecha") -> None:
    if not re.match(r'^t_[a-zA-Z0-9_]+$', table_name):
        table_name = 't_' + _sanitize(table_name)
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cur.fetchone():
            cols = ', '.join(f'"{h}" TEXT' for h in headers.split(','))
            cur.execute(f'CREATE TABLE "{table_name}" ({cols})')
            conn.commit()
    finally:
        conn.close()

def read_table(table_name: str) -> pd.DataFrame:
    conn = get_conn()
    try:
        df = pd.read_sql(f'SELECT * FROM "{table_name}"', conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def write_table(table_name: str, df: pd.DataFrame) -> None:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(f'DELETE FROM "{table_name}"')
        if not df.empty:
            records = []
            for _, row in df.iterrows():
                records.append(tuple(str(v) if not (isinstance(v, float) and pd.isna(v)) else "" for v in row))
            placeholders = ','.join(['?'] * len(df.columns))
            cur.executemany(f'INSERT INTO "{table_name}" VALUES ({placeholders})', records)
        conn.commit()
    finally:
        conn.close()

def list_tables(prefix: str = "") -> list[str]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?"
        cur.execute(sql, (prefix + '%',))
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def table_exists(table_name: str) -> bool:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cur.fetchone() is not None
    finally:
        conn.close()

def find_or_create_table(filename_stem: str, active_client: str = "Chat General", headers: str = "ID,Cliente,Proyecto,Monto,Fecha") -> str:
    stem = filename_stem.replace('.csv', '').replace('.xlsx', '')
    existing = list_tables()
    # Search by matching stem
    cand = _sanitize(stem)
    for t in existing:
        if t.endswith('_' + cand) or t == 't_' + cand or cand in t:
            return t
    # Not found → create
    table_name = _table_name(active_client, stem)
    ensure_table(table_name, headers)
    return table_name

def migrate_csv_to_sqlite(csv_path: str, table_name: str | None = None) -> str | None:
    if not os.path.exists(csv_path):
        return None
    try:
        df = pd.read_csv(csv_path)
        if table_name is None:
            stem = os.path.splitext(os.path.basename(csv_path))[0]
            parts = csv_path.replace('\\', '/').split('/')
            client = "Chat General"
            for i, p in enumerate(parts):
                if p == 'clientes' and i + 1 < len(parts):
                    client = parts[i + 1]
                    break
            table_name = _table_name(client, stem)
        # Create table with CSV's actual column headers (even if file is empty)
        headers = ','.join(df.columns) if not df.empty else "ID"
        ensure_table(table_name, headers)
        if not df.empty:
            write_table(table_name, df)
        return table_name
    except Exception as e:
        print(f"Error migrating {csv_path}: {e}")
        return None

def migrate_all_csvs() -> int:
    count = 0
    for root, dirs, files in os.walk("data"):
        for f in files:
            if f.endswith('.csv') and 'agent3000.db' not in root:
                fp = os.path.join(root, f)
                if migrate_csv_to_sqlite(fp):
                    try:
                        os.remove(fp)
                        count += 1
                    except Exception as e:
                        print(f"Could not delete {fp}: {e}")
    return count
