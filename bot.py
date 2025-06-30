import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# DeepSeek 接入
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Flask 保活服务
app = Flask('')

@app.route('/')
def home():
    return "ZSY bot via DeepSeek is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask).start()

# 处理 Telegram 消息
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": user_msg}]
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"出错啦：{e}")

app_bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app_bot.run_polling()
