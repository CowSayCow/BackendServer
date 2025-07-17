import csv
import os
import sqlite3

DB_PATH = "congestion.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 人数カウント保存テーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS people_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            count INTEGER NOT NULL
        );
    """)

    # 施設マスタテーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            camera_id TEXT PRIMARY KEY,
            location_name TEXT NOT NULL,
            capacity INTEGER NOT NULL
        );
    """)

    conn.commit()
    conn.close()

def import_locations_from_csv(csv_path="locations.csv"):
    """
    locations.csv の内容を locations テーブルに反映する。
    CSV形式: camera_id,location_name,capacity
    """
    if not os.path.exists(csv_path):
        print(f"[WARN] {csv_path} not found. Skipping import.")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            camera_id = row['camera_id']
            location_name = row['location_name']
            capacity = int(row['capacity'])
            cur.execute("""
                INSERT INTO locations (camera_id, location_name, capacity)
                VALUES (?, ?, ?)
                ON CONFLICT(camera_id) DO UPDATE SET
                  location_name=excluded.location_name,
                  capacity=excluded.capacity
            """, (camera_id, location_name, capacity))
    conn.commit()
    conn.close()

def save_count(camera_id: str, timestamp: str, count: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO people_counts (camera_id, timestamp, count)
        VALUES (?, ?, ?)
    """, (camera_id, timestamp, count))
    conn.commit()
    conn.close()

def camera_id_exists(camera_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM locations WHERE camera_id = ?", (camera_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def get_all_latest():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # camera_idごとに最新のtimestampのcountと施設情報を正確に取得
    cur.execute("""
        SELECT pc.camera_id, pc.timestamp, pc.count, loc.location_name, loc.capacity
        FROM people_counts pc
        LEFT JOIN locations loc ON pc.camera_id = loc.camera_id
        INNER JOIN (
            SELECT camera_id, MAX(timestamp) AS max_timestamp
            FROM people_counts
            GROUP BY camera_id
        ) latest
        ON pc.camera_id = latest.camera_id AND pc.timestamp = latest.max_timestamp
    """)
    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        camera_id, _, count, location_name, capacity = row
        if capacity is None:
            capacity = 100  # デフォルトの上限
        usage = int((count / capacity) * 100)
        if usage <= 50:
            level = "low"
        elif usage <= 80:
            level = "medium"
        else:
            level = "high"

        results.append({
            "location_name": location_name if location_name else camera_id,
            "camera_id": camera_id,
            "current": count,
            "capacity": capacity,
            "level": level,
        })
    return results