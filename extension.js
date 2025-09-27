const API_URL = "https://twitch-lootgame.onrender.com"; // Replace with your server IP/URL

function outputMessage(msg){
    document.getElementById("output").innerText = msg;
}

async function lootbox(){
    const user = document.getElementById("username").value.trim();
    if(!user) return outputMessage("❌ Enter your Twitch username!");
    const res = await fetch(`${API_URL}/lootbox`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({user})
    });
    const data = await res.json();
    outputMessage(data.message);
}

async function showInventory(){
    const user = document.getElementById("username").value.trim();
    if(!user) return outputMessage("❌ Enter your Twitch username!");
    const res = await fetch(`${API_URL}/inventory`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({user})
    });
    const data = await res.json();
    outputMessage(data.message || JSON.stringify(data));
}
