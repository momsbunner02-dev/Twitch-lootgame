from flask import Flask, request, jsonify
import sqlite3
import os
from loot_data import LOOT_POOLS, RARITY_STATS, generate_loot
from datetime import datetime, timedelta

app = Flask(__name__)
DB_PATH = os.path.join("/app/db", "database.db")
LOOTBOX_COOLDOWN = 4 * 60 * 60  # 4 hours

# Create persistent folder
os.makedirs("/app/db", exist_ok=True)

# Initialize database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    last_lootbox TIMESTAMP
)""")
c.execute("""CREATE TABLE IF NOT EXISTS inventory (
    user_id TEXT,
    item TEXT,
    rarity TEXT,
    quantity INTEGER DEFAULT 1,
    PRIMARY KEY(user_id, item)
)""")
conn.commit()
conn.close()

@app.route("/lootbox", methods=["POST"])
def lootbox():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT last_lootbox, xp FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    now = datetime.utcnow()

    last_loot = row[0] if row else None
    xp = row[1] if row else 0

    if last_loot:
        last_dt = datetime.fromisoformat(last_loot)
        remaining = (last_dt + timedelta(seconds=LOOTBOX_COOLDOWN) - now).total_seconds()
        if remaining > 0:
            conn.close()
            return jsonify({"error": "cooldown", "time_left": int(remaining)})

    item, rarity = generate_loot()
    c.execute("SELECT quantity FROM inventory WHERE user_id=? AND item=?", (user_id, item))
    inv_row = c.fetchone()
    if inv_row:
        c.execute("UPDATE inventory SET quantity=quantity+1 WHERE user_id=? AND item=?", (user_id, item))
    else:
        c.execute("INSERT INTO inventory (user_id, item, rarity) VALUES (?,?,?)", (user_id, item, rarity))

    xp += 50
    level = xp // 100 + 1

    c.execute("INSERT OR REPLACE INTO users (user_id, xp, level, last_lootbox) VALUES (?,?,?,?)",
              (user_id, xp, level, now.isoformat()))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "item": item,
        "rarity": rarity,
        "xp_gained": 50,
        "level": level
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
