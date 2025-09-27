from flask import Flask, request, jsonify
import random
import time

app = Flask(__name__)

# ====== LOOT POOL ======
loot_pool = {
    "Glorpshake": {"emoji":"🥤","atk":2,"def":1,"hp":5},
    "GuangGuang Bible": {"emoji":"📖","atk":1,"def":2,"hp":4},
    "alienboogie": {"emoji":"👽","atk":2,"def":2,"hp":3},
    "glorpwork": {"emoji":"🛠️","atk":3,"def":1,"hp":2},
    "welcome": {"emoji":"👋","atk":1,"def":1,"hp":3},
    "xglorp": {"emoji":"❌","atk":1,"def":1,"hp":1},
    "Glorpscheme": {"emoji":"📜","atk":3,"def":2,"hp":3},
    "glorpshiz": {"emoji":"💩","atk":2,"def":3,"hp":2},
    "glorppray": {"emoji":"🙏","atk":1,"def":3,"hp":4},
    "glorppop": {"emoji":"🎉","atk":2,"def":1,"hp":4},
    "glorpwiggle": {"emoji":"💃","atk":2,"def":2,"hp":2},
    "angryglorpshake": {"emoji":"😡🥤","atk":3,"def":1,"hp":3},
    "soul sword": {"emoji":"⚔️","atk":5,"def":1,"hp":3},
    "glorp glasses": {"emoji":"🕶️","atk":2,"def":4,"hp":2},
    "glorp gun": {"emoji":"🔫","atk":4,"def":1,"hp":3},
    "glorpstrong": {"emoji":"💪","atk":3,"def":3,"hp":4},
    "glorpsnail": {"emoji":"🐌","atk":1,"def":5,"hp":2},
    "glorpcheer": {"emoji":"🎊","atk":2,"def":2,"hp":5},
    "glorpstare": {"emoji":"👀","atk":2,"def":3,"hp":3},
    "glorptwerk": {"emoji":"🍑","atk":4,"def":2,"hp":3},
    "glorp griddy": {"emoji":"🕺","atk":3,"def":3,"hp":3},
    "glorp rainbow": {"emoji":"🌈","atk":3,"def":2,"hp":4},
    "glorp car": {"emoji":"🚗","atk":4,"def":1,"hp":4},
    "glorp jiggy": {"emoji":"🎵","atk":2,"def":2,"hp":5},
    "glorp group": {"emoji":"👥","atk":3,"def":3,"hp":3},
    "glorp ufo": {"emoji":"🛸","atk":4,"def":2,"hp":3},
    "GLORIOUS GLORP": {"emoji":"🌟","atk":5,"def":5,"hp":5},
    "glorp miku": {"emoji":"🎤","atk":4,"def":3,"hp":4},
    "glorp doobie": {"emoji":"💨","atk":3,"def":3,"hp":4},
    "bewowow": {"emoji":"🐶","atk":2,"def":2,"hp":5},
    "RAGEEEEE": {"emoji":"😡","atk":5,"def":2,"hp":3}
}

rarity_chances = [
    {"rarity":"common","chance":50},
    {"rarity":"uncommon","chance":25},
    {"rarity":"rare","chance":15},
    {"rarity":"epic","chance":7},
    {"rarity":"legendary","chance":3}
]

# ====== PLAYER DATA ======
# This is temporary storage; in production you would use a database
players = {}  # username -> {"xp":int,"coins":int,"inventory":{item:qty}}

LOOTBOX_COOLDOWN = 4*60*60  # seconds

# ====== HELPERS ======

def open_lootbox(user):
    now = time.time()
    pdata = players.setdefault(user, {"xp":0,"coins":0,"inventory":{}, "last_loot":0})
    
    remaining = pdata["last_loot"] + LOOTBOX_COOLDOWN - now
    if remaining > 0:
        h = int(remaining//3600)
        m = int((remaining%3600)//60)
        s = int(remaining%60)
        return f"⏱️ {user}, wait {h}h {m}m {s}s before opening another lootbox."
    
    roll = random.randint(1,100)
    cum = 0
    for r in rarity_chances:
        cum += r["chance"]
        if roll <= cum:
            item = random.choice(list(loot_pool.keys()))
            pdata["inventory"][item] = pdata["inventory"].get(item,0)+1
            pdata["xp"] += 10
            pdata["coins"] += 100
            pdata["last_loot"] = now
            stats = loot_pool[item]
            return f"🎁 {user} got {loot_pool[item]['emoji']} {item} [{stats['atk']}/{stats['def']}/{stats['hp']}]"
    return "❌ nothing"

def get_inventory(user):
    pdata = players.get(user)
    if not pdata or not pdata["inventory"]:
        return "📦 You have nothing. Use !lootbox to get items."
    out = []
    for i,qty in pdata["inventory"].items():
        stats = loot_pool[i]
        out.append(f"{i} x{qty} [{stats['atk']}/{stats['def']}/{stats['hp']}]")
    return ", ".join(out)

def fight_with_item(user,item):
    pdata = players.get(user)
    if not pdata or item not in pdata["inventory"]:
        return "❌ Item not found. Use !inventory to check your items."
    # For simplicity, fight vs random AI
    ai_item = random.choice(list(loot_pool.keys()))
    ai_stats = loot_pool[ai_item]
    user_stats = loot_pool[item]
    
    user_power = user_stats["atk"] + user_stats["def"] + user_stats["hp"]
    ai_power = ai_stats["atk"] + ai_stats["def"] + ai_stats["hp"]
    
    if user_power > ai_power:
        pdata["xp"] += 20
        pdata["coins"] += 100
        return f"⚔️ {user} won using {item}! XP +20, Coins +100"
    elif user_power < ai_power:
        pdata["xp"] += 0
        pdata["coins"] -= 100
        return f"⚔️ {user} lost using {item}! Coins -100"
    else:
        pdata["xp"] += 10
        pdata["coins"] += 100
        return f"🤝 {user} tied against {ai_item}! XP +10, Coins +100"

def trade_up_item(user,item):
    pdata = players.get(user)
    if not pdata or pdata["inventory"].get(item,0)<2:
        return "❌ You need 2 of the same item to trade up."
    success = random.random() < 0.5
    pdata["inventory"][item] -= 2
    if pdata["inventory"][item]==0:
        del pdata["inventory"][item]
    if success:
        # Give random next-tier item
        new_item = random.choice(list(loot_pool.keys()))
        pdata["inventory"][new_item] = pdata["inventory"].get(new_item,0)+1
        return f"✅ Trade up successful! You got {new_item}"
    else:
        return "❌ Trade up failed! Both items lost."

def get_leaderboard(top=5):
    lb = []
    for u,p in players.items():
        lb.append((u,p["xp"],p["coins"]))
    lb.sort(key=lambda x:x[1],reverse=True)
    out = ""
    for i in lb[:top]:
        out += f"{i[0]}: XP {i[1]}, Coins {i[2]}\n"
    return out.strip()

# ====== ROUTES ======
@app.route("/lootbox", methods=["GET","POST"])
def route_lootbox():
    if request.method=="POST":
        data = request.get_json()
        user = data.get("user")
    else:
        user = request.args.get("user")
    if not user:
        return jsonify({"message":"❌ Usage: !lootbox ?user=YourName"})
    return jsonify({"message": open_lootbox(user)})

@app.route("/inventory", methods=["GET","POST"])
def route_inventory():
    if request.method=="POST":
        data = request.get_json()
        user = data.get("user")
    else:
        user = request.args.get("user")
    if not user:
        return jsonify({"message":"❌ Usage: !inventory ?user=YourName"})
    return jsonify({"message": get_inventory(user)})

@app.route("/fight", methods=["GET","POST"])
def route_fight():
    if request.method=="POST":
        data = request.get_json()
        user = data.get("user")
        item = data.get("item")
    else:
        user = request.args.get("user")
        item = request.args.get("item")
    if not user or not item:
        return jsonify({"message":"❌ Usage: !fight [item]. Use !inventory to check your items."})
    return jsonify({"message": fight_with_item(user,item)})

@app.route("/tradeup", methods=["GET","POST"])
def route_tradeup():
    if request.method=="POST":
        data = request.get_json()
        user = data.get("user")
        item = data.get("item")
    else:
        user = request.args.get("user")
        item = request.args.get("item")
    if not user or not item:
        return jsonify({"message":"❌ Usage: !tradeup [item]. Need 2 identical items."})
    return jsonify({"message": trade_up_item(user,item)})

@app.route("/leaderboard", methods=["GET","POST"])
def route_leaderboard():
    if request.method=="POST":
        data = request.get_json()
        top = int(data.get("top",5))
    else:
        top = int(request.args.get("top",5))
    return jsonify({"message": get_leaderboard(top)})

@app.route("/help")
def route_help():
    msg = (
        "🎮 Commands:\n"
        "!lootbox - Open a lootbox (every 4h cooldown)\n"
        "!inventory - Show your items with stats [Atk/Def/HP]\n"
        "!fight [item] - Fight AI with one item\n"
        "!tradeup [item] - Trade 2 identical items for 50% chance to upgrade\n"
        "!leaderboard - View top players with XP & coins"
    )
    return jsonify({"message": msg})

# ====== RUN APP ======
if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
