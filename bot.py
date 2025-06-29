import os
from dotenv import load_dotenv
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 加载环境变量
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# 初始化 DeepSeek 客户端
client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# 用户聊天上下文存储
user_histories = {}
MAX_HISTORY = 10

# /start 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        print("⚠️ /start 被触发但没有 message")
        return
    await update.message.reply_text("你好，我是基于 DeepSeek 的 AI 聊天机器人，有记忆能力哟 🧠✨")

# /clear 命令
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = getattr(getattr(update, "effective_user", None), "id", None)
    if user_id is None or not update.message:
        print("⚠️ /clear 无法获取用户信息")
        return
    user_histories.pop(user_id, None)
    await update.message.reply_text("🧽 记忆已清除，我们重新认识一下吧～")

# 主聊天函数
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not hasattr(update, "message") or not update.message:
        print("⚠️ update 或 message 不存在")
        return

    message_text = getattr(update.message, "text", None)
    if not message_text:
        print("⚠️ message.text 不存在，非文本消息")
        return

    user_id = getattr(getattr(update, "effective_user", None), "id", None)
    if user_id is None:
        print("⚠️ chat() 无法获取用户 ID")
        return

    user_input = message_text.strip()
    history = user_histories.get(user_id, [])
    history.append({"role": "user", "content": user_input})
    history = history[-MAX_HISTORY:]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个温柔、有幽默感、会说中文、有记忆力的 AI 助手。"}
            ] + history
        )
        reply = response.choices[0].message.content.strip()
        history.append({"role": "assistant", "content": reply})
        user_histories[user_id] = history

        await update.message.reply_text(reply)
    except Exception as e:
        print("❌ DeepSeek 报错：", e)
        await update.message.reply_text("⚠️ 出错啦，可能是 API 错误或网络问题，请稍后再试～")

# 启动 bot
if TELEGRAM_TOKEN:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()
else:
    print("❌ 未设置 TELEGRAM_TOKEN，无法启动机器人")
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 ZSY Bot is running on Render!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# 启动 Flask 监听端口的线程
Thread(target=run_flask).start()
