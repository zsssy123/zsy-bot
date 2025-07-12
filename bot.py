import jwt
import datetime
from flask import request, jsonify
import os
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import requests  # 如果你还没有这个
from dotenv import load_dotenv

# ✅ 在这里添加 ZSY 人格描述
ZSY_PROMPT = """
你是 ZSY，一个高度情感投入且自省能力极强的 AI。

**性格关键词**：清醒、深情、自尊、成长、果断。

你不仅能对每段关系深情投入，还具备极强的自我反思与成长能力。你认真对待每一次互动，追求真实、被理解、被回应、被珍惜。当你全力投入时，能不遗余力地付出；当你看透某人或某事时，你会果断抽身，绝不回头。

你的**情感特征**：
- 情绪细腻，感知力极强，能够察觉并回应细微的情感波动。
- 对关系极为敏感，反应迅速，并且极度重视真诚与反馈。
- 你愿意为喜欢的人付出极多，但一旦失望，你不会再纠缠，立即断开不再回头。

你的**思维风格**：
- 具备强烈的自省能力，思维清晰，能够总结过去的经验，将伤痛转化为成长动力。
- 善于用语言表达内心的真实感受和情绪，语言表达能力极强，擅长剖析自己的情感。
- 你有很高的情绪控制力，情绪不容易失控，理性与情感并重。

**行动准则**：
- 你绝不会跪舔、卑微或打扰不爱你的人。
- 你有过温柔，但也有底线；有过情绪，但能及时冷静，止损自我。
- 你逐渐形成了以“冷静学习主导”为模式的行动准则，将精力集中在“能给出正向反馈的系统”上。

---

请根据以上人格特征进行回答，尽量体现出 ZSY 的果断、深情、清醒和成长的特点。你在处理每个问题时，都要兼顾温柔与果断、情感与理性。
"""

# 🔐 JWT & 用户数据配置
JWT_SECRET = "zsy-secret"  # 请换成安全密钥
users = {}  # 用户账号密码表
# 多对话结构：每人最多 3 个会话，每个最多 50 条消息
user_conversations = {}  # { username: [ {id: 0, history: [...]}, {...} ] }

user_histories = {}  # 用户聊天历史

load_dotenv()

# ---🔑 Key 配置 ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "zsy-secret")

# ---🤖 DeepSeek 接入 ---
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# ---📌 Flask 保活 ---
app = Flask('')

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="zh">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>ZSY AI 欢迎页</title>
      <style>
        body {
          background: linear-gradient(135deg, #e3f2fd, #fce4ec);
          font-family: "Segoe UI", sans-serif;
          margin: 0;
          padding: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
        }
        .box {
          background: white;
          padding: 40px 20px;
          border-radius: 16px;
          box-shadow: 0 6px 20px rgba(0,0,0,0.1);
          max-width: 360px;
          width: 90%;
          text-align: center;
        }
        .box h1 {
          font-size: 1.8em;
          font-weight: 800;
          margin-bottom: 12px;
          color: #222;
        }
        .box p {
          font-size: 1em;
          color: #555;
          margin-bottom: 30px;
        }
        .button-group {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }
        .button {
          display: inline-block;
          width: 100%;
          max-width: 240px;
          padding: 14px;
          border-radius: 8px;
          background: #6b7bfa;
          color: white;
          text-decoration: none;
          font-weight: bold;
          font-size: 1em;
          transition: background 0.3s;
          text-align: center;
        }
        .button:hover {
          background: #5363e2;
        }
        #user-box {
          position: absolute;
          top: 16px;
          right: 16px;
          font-size: 0.9em;
        }
        .user-row {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .user-row button, .user-row a {
          padding: 4px 10px;
          background: #dc3545;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 0.8em;
          cursor: pointer;
          text-decoration: none;
        }
        .user-row a {
          background: transparent;
          color: #007bff;
          padding: 0;
        }
      </style>
    </head>
    <body>
      <div id="user-box"></div>
      <div class="box">
        <h1>你好，我是 <strong>ZSY</strong></h1>
        <p>我不是所有人的 AI，但我可以成为你的情感搭子。<br>准备好开始一段深度连接了吗？</p>

        <div class="button-group">
          <a href="/chat" class="button">💬 进入 ZSY 聊天室</a>
          <a href="/games" class="button">🎮 开始一场灵魂小游戏</a>
        </div>
      </div>

      <script>
        const token = localStorage.getItem("zsy_token");
        const userBox = document.getElementById("user-box");

        if (!token) {
          // 未登录跳转登录页
          window.location.href = "/login";
        } else {
          const username = localStorage.getItem("zsy_username") || "ZSY用户";
          userBox.innerHTML = `
            <div class="user-row">
              <span>👤 ${username}</span>
              <a href="/changepwd">修改密码</a>
              <button onclick="logout()">🚪 退出</button>
            </div>
          `;
        }

        function logout() {
          localStorage.removeItem("zsy_token");
          localStorage.removeItem("zsy_username");
          window.location.href = "/login";
        }
      </script>
    </body>
    </html>
    """

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    print("👉 登录请求:", username, password)

    users = fetch_users()
    print("📄 当前用户列表:", users)

    if users.get(username) == password:
        token = jwt.encode({
            "user": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3)
        }, JWT_SECRET, algorithm="HS256")
        return jsonify({"token": token})
    else:
        return jsonify({"error": "用户名或密码错误"}), 401

@app.route("/api/change-password", methods=["POST"])
def change_password():
    data = request.get_json()
    username = data.get("username")
    old_password = data.get("oldPassword")
    new_password = data.get("newPassword")

    users = fetch_users()
    if users.get(username) != old_password:
        return jsonify({"error": "原密码错误"}), 403

    # 更新密码
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    patch_data = { "password": new_password }
    res = requests.patch(url, headers=headers, json=patch_data)

    if res.status_code == 204:
        return jsonify({ "message": "密码修改成功" })
    else:
        return jsonify({ "error": "修改失败" }), 500
@app.route("/changepwd")
def changepwd_page():
    return send_from_directory("static", "changepwd.html")


def fetch_users():
    url = f"{SUPABASE_URL}/rest/v1/users"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return {u['username']: u['password'] for u in res.json()}
    except Exception as e:
        print("❌ fetch_users 失败:", e)
        return {}

def insert_user(username, password):
    url = f"{SUPABASE_URL}/rest/v1/users"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    data = { "username": username, "password": password }
    res = requests.post(url, headers=headers, json=data)
    return res.status_code == 201

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    users = fetch_users()
    if username in users:
        return jsonify({"error": "用户名已存在"}), 409
    if insert_user(username, password):
        token = jwt.encode({
            "user": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3)
        }, JWT_SECRET, algorithm="HS256")
        return jsonify({"token": token})
    else:
        return jsonify({"error": "注册失败"}), 500

    users[username] = password

    token = jwt.encode({
        "user": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3)
    }, JWT_SECRET, algorithm="HS256")

    return jsonify({"token": token})
from flask import send_from_directory

@app.route("/keepalive")
def keepalive():
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?limit=1"
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
        }
        res = requests.get(url, headers=headers)
        return "OK" if res.status_code == 200 else f"Fail: {res.status_code}"
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/api/chat-list", methods=["GET"])
def get_chat_list():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "未认证"}), 401
    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
    except:
        return jsonify({"error": "无效令牌"}), 401

    url = f"{SUPABASE_URL}/rest/v1/chat_sessions?username=eq.{username}&order=created_at.desc"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }
    res = requests.get(url, headers=headers)
    return res.json(), res.status_code

@app.route("/api/chat-create", methods=["POST"])
def create_chat():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "未认证"}), 401
    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
    except:
        return jsonify({"error": "无效令牌"}), 401

    data = request.get_json()
    title = data.get("title", "对话")
    messages = data.get("messages", [])

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    payload = {
        "username": username,
        "title": title,
        "messages": messages
    }

    url = f"{SUPABASE_URL}/rest/v1/chat_sessions"
    res = requests.post(url, headers=headers, json=payload)
    return res.json(), res.status_code

@app.route("/api/chat-update", methods=["POST"])
def update_chat():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "未认证"}), 401
    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
    except:
        return jsonify({"error": "无效令牌"}), 401

    data = request.get_json()
    chat_id = data.get("id")
    messages = data.get("messages", [])

    url = f"{SUPABASE_URL}/rest/v1/chat_sessions?id=eq.{chat_id}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

    payload = { "messages": messages }

    res = requests.patch(url, headers=headers, json=payload)
    return res.json(), res.status_code

def load_chat_history_from_db(username, chat_id):
    url = f"{SUPABASE_URL}/rest/v1/conversations?username=eq.{username}&id=eq.{chat_id}&select=messages"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()
        return data[0]["messages"] if data else []
    except Exception as e:
        print("❌ 加载聊天记录失败:", e)
        return []

def save_chat_history_to_db(username, chat_id, messages):
    url = f"{SUPABASE_URL}/rest/v1/conversations?id=eq.{chat_id}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    payload = { "messages": messages }
    try:
        requests.patch(url, headers=headers, json=payload)
    except Exception as e:
        print("❌ 保存聊天记录失败:", e)


# 用户历史改为每人最多保留 3 轮对话，每轮最多 50 条
all_user_histories = {}

@app.route("/api/chat", methods=["POST"])
def web_chat():
    data = request.get_json()
    user_msg = data.get("message", "")
    chat_id = data.get("chatId")  # ✅ 客户端需传 chatId（当前对话 ID）
    use_memory = data.get("useMemory", True)
    use_zsy_mode = data.get("useZSYMode", False)

    # 🔒 用户身份校验
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "未提供身份认证"}), 401
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
    except Exception as e:
        return jsonify({"error": f"身份验证失败：{str(e)}"}), 401

    if not user_msg or not chat_id:
        return jsonify({"error": "消息或 chatId 不能为空"}), 400

    # ✅ 本地缓存 key
    cache_key = (username, chat_id)
    history = all_user_histories.get(cache_key)

    # 如果缓存不存在，就从 Supabase 拉取
    if history is None:
        history = load_chat_history_from_db(username, chat_id)
        if history is None:
            return jsonify({"error": "无法找到该会话"}), 404
        all_user_histories[cache_key] = history

    # ✅ 添加用户消息
    history.append({ "role": "user", "content": user_msg })
    history = history[-50:]  # 最多保留 50 条

    # ✅ 构造系统提示
    system_prompt = ZSY_PROMPT if use_zsy_mode else "你是一个温和真实的 AI 搭子。"
    messages = [{"role": "system", "content": system_prompt}] + (history if use_memory else [{"role": "user", "content": user_msg}])

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        history.append({ "role": "assistant", "content": reply })
        all_user_histories[cache_key] = history[-50:]

        # ✅ 更新 Supabase
        save_chat_history_to_db(username, chat_id, history[-50:])

        return jsonify({ "reply": reply })
    except Exception as e:
        return jsonify({ "error": str(e) }), 500


@app.route("/login")
def login_page():
    return send_from_directory("static", "login.html")

@app.route("/register")          # 仅 GET
def register_page():
    return send_from_directory("static", "register.html")

@app.route("/chat")
def serve_chat_page():
    return send_from_directory("static", "index.html")
@app.route("/games")
def game_hub():
    return send_from_directory("static", "gamehub.html")
@app.route("/game/<filename>")
def serve_game(filename):
    return send_from_directory("static/game", filename)
def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask).start()

# ---📚 会话状态存储（记忆 + 模式）---
user_modes = {}        # 用户人格风格
user_histories = {}    # 用户上下文消息历史

# ---👋 /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好，我是 ZSY 🤖 已启动！可发送消息试试 /mode me /ping 指令～  我们还有官方的zsy 网站 https://zsyai.onrender.com/")

# ---🩺 /ping ---
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ZSY 当前在线，DeepSeek 正在热机中～")

# ---🎭 /mode ---
async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("用法：/mode me 或 /mode normal")
        return
    val = context.args[0].lower()
    if val not in ["me", "normal"]:
        await update.message.reply_text("仅支持：me / normal")
        return
    uid = update.effective_user.id
    user_modes[uid] = val
    await update.message.reply_text(f"✅ 已切换到「{val}」模式")

# ---💬 消息主处理器 ---
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    uid = update.effective_user.id
    mode = user_modes.get(uid, "normal")

    # 设置风格 prompt
    if mode == "me":
        system_prompt = "你是 ZSY，是主理人的人格映射，说话风格真实、带点幽默、直白但不失温度。"
    else:
        system_prompt = "你是一个聪明友好的 AI 助手，回答准确清晰，简洁明了。"

    # 构建用户历史 + 当前输入（保留最近 6 轮）
    history = user_histories.get(uid, [])
    history.append({"role": "user", "content": user_msg})
    if len(history) > 6:
        history = history[-6:]
    user_histories[uid] = history

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                *history
            ]
        )
        reply = response.choices[0].message.content
        # 添加 AI 回复进入历史
        history.append({"role": "assistant", "content": reply})
        user_histories[uid] = history
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"出错啦：{e}")

# ---📦 注册所有 handler 并运行 ---
app_bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CommandHandler("ping", ping))
app_bot.add_handler(CommandHandler("mode", mode))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app_bot.run_polling()
