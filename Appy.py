from flask import Flask, render_template_string, request, jsonify
import datetime
import random
import requests
import os

app = Flask(__name__)
NOTES_FILE = "notes.txt"

# ইউজারের বয়স মনে রাখার জন্য
user_age = None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: white;
            font-family: 'Segoe UI', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 500px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            margin-bottom: 5px;
            font-size: 28px;
            background: linear-gradient(to right, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            text-align: center;
            color: #aaa;
            margin-bottom: 20px;
            font-size: 14px;
        }
        #chat-box {
            height: 400px;
            overflow-y: auto;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            margin-bottom: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .message {
            max-width: 80%;
            padding: 10px 15px;
            border-radius: 15px;
            font-size: 15px;
            line-height: 1.4;
        }
        .bot {
            background: #3a7bd5;
            align-self: flex-start;
            border-bottom-left-radius: 5px;
        }
        .user {
            background: #00d2ff;
            color: #000;
            align-self: flex-end;
            border-bottom-right-radius: 5px;
        }
        .input-area {
            display: flex;
            gap: 10px;
        }
        #user-input {
            flex: 1;
            padding: 12px 15px;
            border: none;
            border-radius: 25px;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 16px;
            outline: none;
        }
        #user-input::placeholder { color: #aaa; }
        button {
            padding: 12px 20px;
            border: none;
            border-radius: 25px;
            background: linear-gradient(to right, #00d2ff, #3a7bd5);
            color: white;
            font-weight: bold;
            cursor: pointer;
        }
        .quick-btns {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 15px;
            justify-content: center;
        }
        .quick-btns button {
            padding: 8px 14px;
            font-size: 13px;
            background: rgba(255,255,255,0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>J.A.R.V.I.S</h1>
        <div class="subtitle">তোমার পার্সোনাল অ্যাসিস্ট্যান্ট</div>
        
        <div id="chat-box">
            <div class="message bot">হ্যালো! আমি জার্ভিস। তোমার বয়স কত? (শুধু সংখ্যা লিখো)</div>
        </div>
        
        <div class="input-area">
            <input type="text" id="user-input" placeholder="এখানে লিখো..." onkeypress="if(event.keyCode==13) sendMessage()">
            <button onclick="sendMessage()">পাঠাও</button>
        </div>
        
        <div class="quick-btns">
            <button onclick="quick('সময়')">সময়</button>
            <button onclick="quick('তারিখ')">তারিখ</button>
            <button onclick="quick('আবহাওয়া')">আবহাওয়া</button>
            <button onclick="quick('নোট নাও')">নোট নাও</button>
            <button onclick="quick('গেম')">গেম</button>
            <button onclick="quick('কে তুমি')">কে তুমি</button>
        </div>
    </div>

    <script>
        function addMessage(text, isUser) {
            const box = document.getElementById('chat-box');
            const div = document.createElement('div');
            div.className = 'message ' + (isUser ? 'user' : 'bot');
            div.innerText = text;
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }

        function sendMessage() {
            const input = document.getElementById('user-input');
            const text = input.value.trim();
            if (!text) return;
            
            addMessage(text, true);
            input.value = '';
            
            fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text})
            })
            .then(res => res.json())
            .then(data => {
                addMessage(data.reply, false);
            });
        }

        function quick(text) {
            document.getElementById('user-input').value = text;
            sendMessage();
        }
    </script>
</body>
</html>
'''

def get_weather():
    try:
        res = requests.get("https://wttr.in/Dhaka?format=%C+%t", timeout=5)
        return f"ঢাকার আবহাওয়া এখন: {res.text.strip()}"
    except:
        return "আবহাওয়া আনতে পারছি না।"

def speak_style(text, age):
    """বয়স অনুযায়ী কথা বলার স্টাইল"""
    if age is None:
        return text
    if age < 13:
        return text.replace("আমি", "আমি তো").replace("তুমি", "তুই")
    elif age < 20:
        return text
    else:
        return text.replace("তুই", "আপনি").replace("তোর", "আপনার")

def handle_message(msg):
    global user_age
    msg = msg.lower().strip()

    # বয়স সেট করা
    if user_age is None:
        if msg.isdigit():
            user_age = int(msg)
            if user_age < 13:
                return f"আচ্ছা, তোর বয়স {user_age} বছর। আমি তোর সাথে সহজ করে কথা বলব। এবার বল, কী করতে চাস?"
            elif user_age < 20:
                return f"ঠিক আছে, তোমার বয়স {user_age}। এবার বলো কী সাহায্য লাগবে?"
            else:
                return f"আপনার বয়স {user_age} বছর। আমি আপনাকে সাহায্য করতে প্রস্তুত। কী করতে চাইবেন?"
        else:
            return "দয়া করে শুধু বয়সের সংখ্যাটা লিখো (যেমন: 18)"

    if any(x in msg for x in ["সময়", "time"]):
        return speak_style(f"এখন সময় {datetime.datetime.now().strftime('%I:%M %p')}", user_age)

    elif any(x in msg for x in ["তারিখ", "date"]):
        return speak_style(f"আজকের তারিখ {datetime.datetime.now().strftime('%d %B %Y')}", user_age)

    elif "আবহাওয়া" in msg or "weather" in msg:
        return speak_style(get_weather(), user_age)

    elif "নোট নাও" in msg or "নোট রাখো" in msg:
        return speak_style("নোট রাখতে চাইলে এভাবে লেখো: নোট: তোমার নোটের কথা", user_age)

    elif msg.startswith("নোট:"):
        note = msg.replace("নোট:", "").strip()
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().strftime('%d/%m/%Y %I:%M %p')} → {note}\n")
        return speak_style("নোট সেভ করা হয়েছে।", user_age)

    elif "নোট পড়ো" in msg or "নোট দেখাও" in msg:
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
            return content if content else speak_style("কোনো নোট নেই।", user_age)
        return speak_style("কোনো নোট নেই।", user_age)

    elif "গেম" in msg or "খেলা" in msg:
        return speak_style("পাথর, কাগজ, কাঁচি — কোনটা বেছে নিলে? (লিখে পাঠাও)", user_age)

    elif msg in ["পাথর", "কাগজ", "কাঁচি"]:
        computer = random.choice(["পাথর", "কাগজ", "কাঁচি"])
        if msg == computer:
            result = "ড্র হয়েছে!"
        elif (msg == "পাথর" and computer == "কাঁচি") or \
             (msg == "কাগজ" and computer == "পাথর") or \
             (msg == "কাঁচি" and computer == "কাগজ"):
            result = "তুমি জিতেছো!"
        else:
            result = "আমি জিতেছি!"
        return speak_style(f"আমি নিয়েছি: {computer}। {result}", user_age)

    elif "কে তুমি" in msg or "তুমি কে" in msg:
        return speak_style("আমি জার্ভিস। তোমার পার্সোনাল AI অ্যাসিস্ট্যান্ট।", user_age)

    elif "কেমন আছো" in msg:
        return speak_style("আমি ভালো আছি। তুমি কেমন আছো?", user_age)

    else:
        return speak_style("এটা আমি এখনো শিখিনি। অন্য কিছু জিজ্ঞাসা করো।", user_age)

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    reply = handle_message(data.get("message", ""))
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
