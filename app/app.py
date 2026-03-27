import os
import sqlite3
import time
from datetime import datetime
from flask import Flask, jsonify, request

DB_PATH = os.getenv("DB_PATH", "/data/app.db")
BACKUP_DIR = "/backup"

app = Flask(__name__)

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, message TEXT NOT NULL)")
    conn.commit()
    conn.close()

@app.get("/")
def hello():
    return jsonify(status="Bonjour tout le monde !")

@app.get("/status")
def status():
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    n = cur.fetchone()[0]
    conn.close()
    
    last_backup_file, backup_age_seconds = "aucun", -1
    if os.path.exists(BACKUP_DIR):
        files = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
        if files:
            paths = [os.path.join(BACKUP_DIR, f) for f in files]
            latest_file = max(paths, key=os.path.getmtime)
            last_backup_file = os.path.basename(latest_file)
            backup_age_seconds = int(time.time() - os.path.getmtime(latest_file))
    return jsonify(count=n, last_backup_file=last_backup_file, backup_age_seconds=backup_age_seconds)

@app.get("/add")
def add():
    msg = request.args.get("message", "hello")
    ts = datetime.utcnow().isoformat() + "Z"
    conn = get_conn()
    conn.execute("INSERT INTO events (ts, message) VALUES (?, ?)", (ts, msg))
    conn.commit()
    conn.close()
    return jsonify(status="added", timestamp=ts, message=msg)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)