import sqlite3
import os

# Android Compatibility: Store database in internal files directory
try:
    from com.chaquo.python import Python
    context = Python.getPlatform().getApplication()
    DB_DIR = str(context.getFilesDir())
except ImportError:
    DB_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(DB_DIR, "finextract.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        filepath TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS extracted_kpis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        kpi_name TEXT,
        kpi_value_raw TEXT,
        kpi_value_numeric REAL,
        fiscal_year TEXT,
        page_number INTEGER,
        source_text TEXT,
        confidence INTEGER,
        is_custom INTEGER DEFAULT 0,
        FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

def add_document(filename, filepath):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO documents (filename, filepath) VALUES (?, ?)", (filename, filepath))
        doc_id = cursor.lastrowid
        conn.commit()
        return doc_id
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM documents WHERE filename = ?", (filename,))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def get_documents():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, filepath, uploaded_at FROM documents ORDER BY uploaded_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_document(doc_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, filepath, uploaded_at FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_document(doc_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    if row:
        filepath = row["filepath"]
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    cursor.execute("DELETE FROM extracted_kpis WHERE document_id = ?", (doc_id,))
    conn.commit()
    conn.close()

def save_extracted_kpi(doc_id, kpi_name, value_raw, value_numeric, year, page, source_text, confidence, is_custom=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM extracted_kpis
        WHERE document_id = ? AND kpi_name = ? AND fiscal_year = ? AND page_number = ?
    """, (doc_id, kpi_name, year, page))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("""
            UPDATE extracted_kpis
            SET kpi_value_raw = ?, kpi_value_numeric = ?, source_text = ?, confidence = ?, is_custom = ?
            WHERE id = ?
        """, (value_raw, value_numeric, source_text, confidence, is_custom, existing["id"]))
    else:
        cursor.execute("""
            INSERT INTO extracted_kpis
            (document_id, kpi_name, kpi_value_raw, kpi_value_numeric, fiscal_year, page_number, source_text, confidence, is_custom)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, kpi_name, value_raw, value_numeric, year, page, source_text, confidence, is_custom))
    conn.commit()
    conn.close()

def get_extracted_kpis(doc_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, document_id, kpi_name, kpi_value_raw, kpi_value_numeric, fiscal_year, page_number, source_text, confidence, is_custom
        FROM extracted_kpis
        WHERE document_id = ?
        ORDER BY kpi_name, fiscal_year DESC
    """, (doc_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_kpis_for_document(doc_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM extracted_kpis WHERE document_id = ?", (doc_id,))
    conn.commit()
    conn.close()
