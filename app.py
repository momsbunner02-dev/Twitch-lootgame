from flask import Flask, request, jsonify
import sqlite3, random, os, time

app = Flask(__name__)
DB_PATH = "db/database.db"
LOOTBOX_COOLDOWN = 4*60*60  # 4 hours in seconds

# --- Loot pool with Twitch-friendly emojis ---
loot_pool = {
    "Glorpshake":"🥤","GuangGuang Bible":"📖","alienboogie":"👽","glorpwork":"🛠️","welcome":"👋","xglorp":"❌",
    "Glorpscheme":"📜","glorpshiz":"💩","glorppray":"🙏","glorppop":"🎉","glorpwiggle":"💃","angryglorpshake":"😡🥤",
    "soul sword":"⚔️","glorp glasses":"🕶️","glorp gun":"🔫","glorpstrong":"💪","glorpsnail":"🐌","glorpcheer":"🎊","glorpstare":"👀",
    "glorptwerk":"🍑","glorp griddy":"🕺","glorp rainbow":"🌈","glorp car":"🚗","glorp jiggy":"🎵","glorp group":"👥","glorp ufo":"🛸",
    "GLORIOUS GLORP":"🌟","glorp miku":"🎤","glorp doobie":"💨","bewowow":"🐶","RAGEEEEE":"😡"
}

# --- Rarities and stats ---
rarity_data = {
    "common":{"chance":50,"attack":1,"defense":1,"hp":5},
    "uncommon":{"chance":25,"attack":2,"defense":2,"hp":10},
    "rare":{"chance":15,"attack":4,"defense":3,"hp":15},
    "epic":{"chance":7,"attack":6,"defense":5,"hp":25},
    "legendary":{"chance":3,"attack":10,"defense":8,"hp":50}
}

# Map item to rarity
item_rarity = {}
for rarity,data_r in rarity_data.items():
    for item in loot_pool:
        if item.lower().startswith(rarity[0]):
            item_rarity[item] = rarity
for i in loot_pool:
    if i not in item_rarity:
        item_rarity[i] = "common"

# --- Database ---
def init_db():
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    username TEXT,
                    item TEXT,
                    rarity TEXT,
                    qty INTEGER,
                    attack INTEGER,
                    defense INTEGER,
                    hp INTEGER,
                    last_lootbox REAL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS xp_coins (
                    username TEXT,
                    xp INTEGER,
                    coins INTEGER
                )''')
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_PATH)

# --- User stats ---
def get_user_stats(user):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT xp, coins FROM xp_coins WHERE username=?",(user,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO xp_coins (username,xp,coins) VALUES (?,?,?)",(user,0,0))
        conn.commit()
        xp, coins = 0,0
    else:
        xp, coins = row
    conn.close()
    return xp, coins

def update_user_stats(user, xp_delta=0, coins_delta=0):
    xp, coins = get_user_stats(user)
    xp += xp_delta
    coins += coins_delta
    conn = get_conn()
    c = conn.cursor()
    c.execute("REPLACE INTO xp_coins (username,xp,coins) VALUES (?,?,?)",(user,xp,coins))
    conn.commit()
    conn.close()

# --- Lootbox endpoint ---
@app.route("/lootbox", methods=["POST"])
def lootbox():
    data = request.get_json()
    user = data.get("user")
    if not user:
        return jsonify({"error":"Missing user"}),400

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT last_lootbox FROM inventory WHERE username=? ORDER BY last_lootbox DESC LIMIT 1",(user,))
    row = c.fetchone()
    now = time.time()
    if row and row[0] and now - row[0] < LOOTBOX_COOLDOWN:
        remaining = int(LOOTBOX_COOLDOWN - (now - row[0]))
        return jsonify({"message":f"⏱️ {user}, wait {remaining//3600}h {(remaining%3600)//60}m {(remaining%60)}s before opening another lootbox."})

    roll = random.uniform(0,100)
    cum = 0
    selected_rarity = "common"
    for rarity,data_r in rarity_data.items():
        cum += data_r["chance"]
        if roll <= cum:
            selected_rarity = rarity
            break

    possible = [i for i,r in item_rarity.items() if r==selected_rarity]
    item = random.choice(possible)
    stats = rarity_data[selected_rarity]
    attack, defense, hp = stats["attack"], stats["defense"], stats["hp"]

    c.execute("SELECT qty FROM inventory WHERE username=? AND item=?",(user,item))
    row = c.fetchone()
    if row:
        qty = row[0]+1
        c.execute("UPDATE inventory SET qty=?, last_lootbox=? WHERE username=? AND item=?",(qty,now,user,item))
    else:
        c.execute("INSERT INTO inventory (username,item,rarity,qty,attack,defense,hp,last_lootbox) VALUES (?,?,?,?,?,?,?,?)",
                  (user,item,selected_rarity,1,attack,defense,hp,now))
    conn.commit()
    conn.close()

    update_user_stats(user,xp_delta=stats["hp"], coins_delta=stats["attack"]*10)
    return jsonify({"message":f"🎁 {user} opened a lootbox and got {loot_pool[item]} {item} | Stats: {attack}/{defense}/{hp}"})

# --- Inventory ---
@app.route("/inventory", methods=["POST"])
def inventory():
    data = request.get_json()
    user = data.get("user")
    if not user:
        return jsonify({"error":"Missing user"}),400
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT item,rarity,qty,attack,defense,hp FROM inventory WHERE username=?",(user,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        return jsonify({"message":f"📦 {user} has no items. Use !lootbox to get items!"})
    inv_list = [f"{loot_pool[item]} {item} [{attack}/{defense}/{hp}] x{qty}" for item,rarity,qty,attack,defense,hp in rows]
    return jsonify({"message": "\n".join(inv_list)})

# --- Fight ---
@app.route("/fight", methods=["POST"])
def fight():
    data = request.get_json()
    user = data.get("user")
    item = data.get("item")
    if not user or not item:
        return jsonify({"message":"❌ Usage: !fight [item]. Check inventory with !inventory"})
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT attack,defense,hp FROM inventory WHERE username=? AND item=?",(user,item))
    row = c.fetchone()
    if not row:
        return jsonify({"message":f"❌ {user} does not have {item}. Use !lootbox!"})
    attack_u, defense_u, hp_u = row

    opponent = "Bot_" + str(random.randint(1,100))
    c.execute("SELECT item,attack,defense,hp FROM inventory ORDER BY RANDOM() LIMIT 1")
    bot_row = c.fetchone()
    if bot_row:
        item_bot, attack_b, defense_b, hp_b = bot_row
    else:
        item_bot = "Glorpshake"
        attack_b, defense_b, hp_b = 1,1,5

    score_user = attack_u + hp_u - defense_b
    score_bot = attack_b + hp_b - defense_u

    if score_user > score_bot:
        update_user_stats(user, xp_delta=10, coins_delta=100)
        update_user_stats(opponent, coins_delta=-100)
        result = f"🏆 {user} wins against {opponent}!"
    elif score_user < score_bot:
        update_user_stats(user, coins_delta=-100)
        update_user_stats(opponent, xp_delta=10, coins_delta=100)
        result = f"💀 {user} loses to {opponent}!"
    else:
        update_user_stats(user, xp_delta=10, coins_delta=100)
        update_user_stats(opponent, xp_delta=10, coins_delta=100)
        result = f"🤝 {user} ties with {opponent}!"

    conn.close()
    return jsonify({"message":f"{result}\n{user}'s item: {item} [{attack_u}/{defense_u}/{hp_u}]\n{opponent}'s item: {item_bot} [{attack_b}/{defense_b}/{hp_b}]"})

# --- Trade Up ---
@app.route("/tradeup", methods=["POST"])
def tradeup():
    data = request.get_json()
    user = data.get("user")
    item = data.get("item")
    if not user or not item:
        return jsonify({"message":"❌ Usage: !tradeup [item]. Need 2 identical items."})
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT qty,rarity FROM inventory WHERE username=? AND item=?",(user,item))
    row = c.fetchone()
    if not row or row[0]<2:
        return jsonify({"message":"❌ Need at least 2 of the same item!"})
    qty, rarity = row
    rarities = ["common","uncommon","rare","epic","legendary"]
    try:
        next_rarity = rarities[rarities.index(rarity)+1]
    except IndexError:
        return jsonify({"message":"❌ Item is already legendary!"})
    if random.random()<0.5:
        c.execute("UPDATE inventory SET qty=qty-2 WHERE username=? AND item=?",(user,item))
        c.execute("DELETE FROM inventory WHERE username=? AND item=? AND qty<=0",(user,item))
        next_items = [i for i,r in item_rarity.items() if r==next_rarity]
        new_item = random.choice(next_items)
        stats = rarity_data[next_rarity]
        c.execute("INSERT INTO inventory (username,item,rarity,qty,attack,defense,hp,last_lootbox) VALUES (?,?,?,?,?,?,?,?)",
                  (user,new_item,next_rarity,1,stats["attack"],stats["defense"],stats["hp"],0))
        conn.commit()
        conn.close()
        return jsonify({"message":f"🎉 Trade up successful! {item} -> {new_item} [{stats['attack']}/{stats['defense']}/{stats['hp']}]"})
    else:
        c.execute("UPDATE inventory SET qty=qty-2 WHERE username=? AND item=?",(user,item))
        c.execute("DELETE FROM inventory WHERE username=? AND item=? AND qty<=0",(user,item))
        conn.commit()
        conn.close()
        return jsonify({"message":"💀 Trade up failed! Both items lost."})

# --- Leaderboard ---
@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT username,xp,coins FROM xp_coins ORDER BY xp DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    out = "🏆 Leaderboard:\n"
    for u,xp,coins in rows:
        out += f"{u}: XP {xp}, Coins {coins}\n"
    return jsonify({"message": out})

if __name__=="__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
