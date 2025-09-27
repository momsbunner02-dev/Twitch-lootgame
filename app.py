from flask import Flask, request, jsonify
import random
import time
import logging

# ====== APP SETUP ======
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.before_request
def log_request_info():
    app.logger.info(f"Received {request.method} request for {request.url}")
    if request.method == "POST":
        app.logger.info(f"POST data: {request.get_json()}")
    else:
        app.logger.info(f"GET params: {request.args}")

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
players = {}  # username -> {"xp":int,"coins":int,"inventory":{item:qty}, "last_loot":float}
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
            return f"🎁 {user} got {stats['emoji']} {item} [{stats['atk']}/{stats['def']}/{stats['hp']}]"
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
        new_item = random.choice(list(loot_pool.keys()))
        pdata["inventory"][new_item] = pdata["inventory"].get(new_item,0)+1
        return f"✅ Trade up successful! You got {new_item} (50% chance)"
    else:
        return "❌ Trade up failed! Both items lost. (50% chance)"

def get_leaderboard(top=5):
    lb = [(u,p["xp"],p["coins"]) for u,p in players.items()]
    lb.sort(key=lambda x:x[1],reverse=True)
    out = ""
    for i in lb[:top]:
        out += f"{i[0]}: XP {i[1]}, Coins {i[2]}\n"
    return out.strip()

# ====== ROUTES ======
@app.route("/lootbox", methods=["GET","POST"])
def route_lootbox():
    user = request.args.get("user") if request.method=="GET" else request.get_json().get("user")
    if not user:
        return jsonify({"message":"❌ Usage: !lootbox ?user=YourName"})
    try:
        return jsonify({"message": open_lootbox(user)})
    except Exception as e:
        return jsonify({"message": f"❌ Lootbox error: {str(e)}"})

@app.route("/inventory", methods=["GET","POST"])
def route_inventory():
    user = request.args.get("user") if request.method=="GET" else request.get_json().get("user")
    if not user:
        return jsonify({"message":"❌ Usage: !inventory ?user=YourName"})
    try:
        return jsonify({"message": get_inventory(user)})
    except Exception as e:
        return jsonify({"message": f"❌ Inventory error: {str(e)}"})

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
        return jsonify({"message":"❌ Usage: !fight [item]. Check your inventory with !inventory"})
    try:
        return jsonify({"message": fight_with_item(user,item)})
    except Exception as e:
        return jsonify({"message": f"❌ Fight error: {str(e)}"})

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
        return jsonify({"message":"❌ Usage: !tradeup [item]. You need 2 identical items."})
    try:
        return jsonify({"message": trade_up_item(user,item)})
    except Exception as e:
        return jsonify({"message": f"❌ Tradeup error: {str(e)}"})

@app.route("/leaderboard", methods=["GET","POST"])
def route_leaderboard():
    top = int(request.args.get("top",5)) if request.method=="GET" else int(request.get_json().get("top",5))
    try:
        return jsonify({"message": get_leaderboard(top)})
    except Exception as e:
        return jsonify({"message": f"❌ Leaderboard error: {str(e)}"})

@app.route("/help", methods=["GET","POST"])
def route_help():
    help_text = (
        "🎮 Commands:\n"
        "!lootbox ?user=YourName - open a lootbox (4h cooldown)\n"
        "!inventory ?user=YourName - check inventory (shows atk/def/hp)\n"
        "!fight [item] - fight using one item\n"
        "!tradeup [item] - trade 2 identical items for a 50% chance to get a new one\n"
        "!leaderboard - top players by XP/coins\n"
        "Item stats format: [atk/def/hp], colors: atk red, def blue, hp green"
    )
    return jsonify({"message": help_text})

# ====== RUN APP ======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
