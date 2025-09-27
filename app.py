from flask import Flask, request
import random
import time
import os

app = Flask(__name__)

# ==== CONFIG ====
LOOTBOX_COOLDOWN = 4 * 60 * 60  # 4 hours in seconds
LEVEL_XP = [0, 100, 250, 500, 1000]  # XP thresholds for levels

# Loot pool: item -> emoji
loot_emojis = {
    "Glorpshake":"🥤","GuangGuang Bible":"📖","alienboogie":"👽","glorpwork":"🛠️","welcome":"👋","xglorp":"❌",
    "Glorpscheme":"📜","glorpshiz":"💩","glorppray":"🙏","glorppop":"🎉","glorpwiggle":"💃","angryglorpshake":"😡🥤",
    "soul sword":"⚔️","glorp glasses":"🕶️","glorp gun":"🔫","glorpstrong":"💪","glorpsnail":"🐌","glorpcheer":"🎊","glorpstare":"👀",
    "glorptwerk":"🍑","glorp griddy":"🕺","glorp rainbow":"🌈","glorp car":"🚗","glorp jiggy":"🎵","glorp group":"👥","glorp ufo":"🛸",
    "GLORIOUS GLORP":"🌟","glorp miku":"🎤","glorp doobie":"💨","bewowow":"🐶","RAGEEEEE":"😡"
}

# Rarity stats: attack/defense/hp
rarity_stats = {
    "common": (2, 2, 5),
    "uncommon": (4, 3, 7),
    "rare": (6, 5, 10),
    "epic": (10, 8, 15),
    "legendary": (15, 10, 20)
}

# Loot pools by rarity
loot_pools = {
    "common":["Glorpshake","GuangGuang Bible","alienboogie","glorpwork","welcome","xglorp"],
    "uncommon":["Glorpscheme","glorpshiz","glorppray","glorppop","glorpwiggle","angryglorpshake"],
    "rare":["soul sword","glorp glasses","glorp gun","glorpstrong","glorpsnail","glorpcheer","glorpstare"],
    "epic":["glorptwerk","glorp griddy","glorp rainbow","glorp car","glorp jiggy","glorp group","glorp ufo"],
    "legendary":["GLORIOUS GLORP","glorp miku","glorp doobie","bewowow","RAGEEEEE"]
}

rarity_chances = [
    {"rarity":"common","chance":50},
    {"rarity":"uncommon","chance":25},
    {"rarity":"rare","chance":15},
    {"rarity":"epic","chance":7},
    {"rarity":"legendary","chance":3}
]

# ==== DATA STORAGE (in-memory) ====
users = {}  # user -> {"items":{item:qty}, "xp":0, "coins":0, "last_loot":0}

# =================== HELPERS ===================
def choose_loot():
    roll = random.randint(1,100)
    cum = 0
    for r in rarity_chances:
        cum += r["chance"]
        if roll <= cum:
            pool = loot_pools[r["rarity"]]
            item = random.choice(pool)
            atk, deff, hp = rarity_stats[r["rarity"]]
            return {"item":item,"rarity":r["rarity"],"atk":atk,"def":deff,"hp":hp,"emoji":loot_emojis[item]}
    item = "xglorp"
    return {"item":item,"rarity":"common","atk":2,"def":2,"hp":5,"emoji":loot_emojis[item]}

def get_level(xp):
    lvl = 0
    for threshold in LEVEL_XP:
        if xp >= threshold:
            lvl += 1
    return lvl

def get_xp_needed(lvl):
    if lvl >= len(LEVEL_XP):
        return LEVEL_XP[-1]
    return LEVEL_XP[lvl]

# =================== ROUTE ===================
@app.route("/command")
def command():
    user = request.args.get("user")
    action = request.args.get("action","").lower()
    if not user or not action:
        return "⚠️ Missing parameters"

    # init user
    if user not in users:
        users[user] = {"items":{}, "xp":0, "coins":0, "last_loot":0}

    udata = users[user]

    # ===== LOOTBOX =====
    if action=="lootbox":
        now = time.time()
        if now - udata["last_loot"] < LOOTBOX_COOLDOWN:
            remaining = LOOTBOX_COOLDOWN - (now - udata["last_loot"])
            h = int(remaining//3600)
            m = int((remaining%3600)//60)
            s = int(remaining%60)
            return f"⏱️ {user}, wait {h}h {m}m {s}s before opening another lootbox."
        loot = choose_loot()
        udata["last_loot"] = now
        udata["items"][loot["item"]] = udata["items"].get(loot["item"],0)+1
        udata["xp"] += 10
        udata["coins"] += 100
        lvl = get_level(udata["xp"])
        xp_needed = get_xp_needed(lvl)
        return f"🎁 {user} opened a lootbox and got {loot['item']} {loot['emoji']} 🔴{loot['atk']}/🔵{loot['def']}/🟢{loot['hp']} | +💰100 | XP {udata['xp']}/{xp_needed} (Level {lvl})"

    # ===== INVENTORY =====
    elif action=="inventory":
        if not udata["items"]:
            return f"📦 {user}, your inventory is empty. Use !lootbox to get items."
        lvl = get_level(udata["xp"])
        xp_needed = get_xp_needed(lvl)
        inv = []
        for item,qty in udata["items"].items():
            rarity = None
            for r, pool in loot_pools.items():
                if item in pool:
                    rarity = r
                    break
            atk,deff,hp = rarity_stats.get(rarity,(0,0,0))
            inv.append(f"{item} {loot_emojis[item]} 🔴{atk}/🔵{deff}/🟢{hp} x{qty}")
        return f"📦 {user}'s Inventory (Level {lvl} | XP {udata['xp']}/{xp_needed} | 💰{udata['coins']}): " + ", ".join(inv)

    # ===== FIGHT =====
    elif action=="fight":
        target = request.args.get("target")
        item_name = request.args.get("item")
        if not target or not item_name:
            return "⚠️ Usage: !fight @username item_name"
        if item_name not in udata["items"]:
            return f"⚠️ {user}, you do not have {item_name}. Use !inventory to check your items."
        if target not in users:
            return f"⚠️ {target} has no inventory. Ask them to use !lootbox first."
        tdata = users[target]
        if not tdata["items"]:
            return f"⚠️ {target} has no items to fight with."
        t_item_name = random.choice(list(tdata["items"].keys()))
        def get_stats(name):
            rarity=None
            for r,pool in loot_pools.items():
                if name in pool:
                    rarity=r
                    break
            return rarity_stats.get(rarity,(0,0,0))
        atk1,deff1,hp1 = get_stats(item_name)
        atk2,deff2,hp2 = get_stats(t_item_name)
        score1 = atk1 + deff1 + hp1 + random.randint(0,5)
        score2 = atk2 + deff2 + hp2 + random.randint(0,5)
        lvl1 = get_level(udata["xp"])
        lvl2 = get_level(tdata["xp"])
        if score1>score2:
            udata["xp"] += 20
            udata["coins"] += 100
            tdata["coins"] = max(0,tdata["coins"]-100)
            result = f"⚔️ {user} wins! (+20 XP, 💰+100) | {target} loses! (💰-100)"
        elif score2>score1:
            tdata["xp"] +=20
            tdata["coins"] +=100
            udata["coins"]=max(0,udata["coins"]-100)
            result = f"⚔️ {target} wins! (+20 XP, 💰+100) | {user} loses! (💰-100)"
        else:
            udata["xp"] +=10
            udata["coins"] +=100
            tdata["xp"] +=10
            tdata["coins"] +=100
            result = f"🤝 Tie! Both gain +10 XP and 💰+100"
        return f"🎮 Fight {user}({item_name}) vs {target}({t_item_name}): {result}"

    # ===== TRADEUP =====
    elif action=="tradeup":
        item_name = request.args.get("item")
        if not item_name:
            return "⚠️ Usage: !tradeup item_name"
        qty = udata["items"].get(item_name,0)
        if qty<2:
            return f"⚠️ {user}, you need 2 of {item_name} to attempt trade-up."
        # remove both
        udata["items"][item_name]-=2
        if udata["items"][item_name]==0:
            del udata["items"][item_name]
        # 50% chance
        next_rarity=None
        for idx,r in enumerate(["common","uncommon","rare","epic","legendary"]):
            if item_name in loot_pools[r]:
                if idx+1<len(loot_pools):
                    next_rarity=["common","uncommon","rare","epic","legendary"][idx+1]
                break
        success = random.random()<0.5
        if success and next_rarity:
            new_item = random.choice(loot_pools[next_rarity])
            udata["items"][new_item] = udata["items"].get(new_item,0)+1
            return f"🎉 Trade-up SUCCESS! {item_name} -> {new_item} {loot_emojis[new_item]}"
        else:
            return f"❌ Trade-up FAILED. You lost both {item_name}."

    # ===== HELP =====
    elif action=="help":
        return (
            "📜 Commands: !lootbox, !inventory, !fight @user item, !tradeup item, !helploot\n"
            "💡 Lootbox: 4h cooldown, +10 XP, +100 coins\n"
            "💪 Fight: use 1 item, winner gets +20 XP/+100 coins, loser -100 coins, tie +10 XP/+100 coins each\n"
            "🎲 Trade-up: need 2 same items, 50% chance to upgrade to next rarity\n"
            "🔢 Stats: displayed as 🔴Attack/🔵Defense/🟢HP"
        )

    else:
        return f"⚠️ Unknown action: {action}. Use !helploot for help."

# =================== RUN ===================
if __name__=="__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
