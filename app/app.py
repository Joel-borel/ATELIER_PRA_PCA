import os
import sqlite3
import time
from datetime import datetime
from flask import Flask, jsonify, request

# Configuration des cheminss
DB_PATH = os.getenv("DB_PATH", "/data/app.db")
BACKUP_DIR = "/backup"

app = Flask(__name__)

# ---------- Helpers Base de Données ----------
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Crée la table si elle n'existe pas"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------- Routes de l'Application ----------

@app.get("/")
def hello():
    return jsonify(status="Bonjour tout le monde !", version="1.3")

@app.get("/health")
def health():
    return jsonify(status="ok")

@app.get("/status")
def status():
    """Route demandée pour l'Atelier 1"""
    init_db()
    # 1. Count des événements en base
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    n = cur.fetchone()[0]
    conn.close()

    # 2. Infos sur le dernier backup dans /backup
    last_backup_file = None
    backup_age_seconds = None

    try:
        if os.path.exists(BACKUP_DIR):
            files = sorted(
                [f for f in os.listdir(BACKUP_DIR) if os.path.isfile(os.path.join(BACKUP_DIR, f))],
                key=lambda f: os.path.getmtime(os.path.join(BACKUP_DIR, f))
            )
            if files:
                last_backup_file = files[-1]
                mtime = os.path.getmtime(os.path.join(BACKUP_DIR, last_backup_file))
                backup_age_seconds = int(time.time() - mtime)
    except Exception as e:
        print(f"Erreur backup: {e}")

    return jsonify(
        count=n,
        last_backup_file=last_backup_file,
        backup_age_seconds=backup_age_seconds
    )

@app.get("/add")
def add():
    """Ajoute un message en base"""
    init_db()
    msg = request.args.get("message", "hello")
    ts = datetime.utcnow().isoformat() + "Z"
    conn = get_conn()
    conn.execute("INSERT INTO events (ts, message) VALUES (?, ?)", (ts, msg))
    conn.commit()
    conn.close()
    return jsonify(status="added", timestamp=ts, message=msg)

@app.get("/consultation")
def consultation():
    """Liste les derniers messages"""
    init_db()
    conn = get_conn()
    cur = conn.execute("SELECT id, ts, message FROM events ORDER BY id DESC LIMIT 50")
    rows = [{"id": r[0], "timestamp": r[1], "message": r[2]} for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

# ---------- Lancement ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)