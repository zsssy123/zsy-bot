import os
from dotenv import load_dotenv
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 加载 .env 文件中的环境变量
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# 初始化 DeepSeek 客户端
client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# 会话记忆，基于 user_id 存储上下文
user_histories = {}

# 最大记忆轮数
MAX_HISTORY = 10

# /start 命令处理
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好，我是基于 DeepSeek 的 AI 聊天机器人，我有记忆哟，咱们聊聊吧！🧠✨")

# /clear 命令：清除记忆
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories.pop(user_id, None)
    await update.message.reply_text("记忆已清除 🧽，我们从头开始吧！")

# 主聊天逻辑
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = update.effective_user.id

    # 获取历史记录，没有则新建
    history = user_histories.get(user_id, [])
    history.append({"role": "user", "content": user_input})
    history = history[-MAX_HISTORY:]  # 限制上下文长度

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": "你是一个记忆力强、风趣、会说中文的 AI 助手。"}] + history
        )
        reply = response.choices[0].message.content

        # 加入 AI 回复到历史中
        history.append({"role": "assistant", "content": reply})
        user_histories[user_id] = history

        await update.message.reply_text(reply)
    except Exception as e:
        print("❌ DeepSeek 报错：", e)
        await update.message.reply_text("⚠️ 出错啦，可能是余额不足或网络问题，请稍后再试试～")

# 创建 Telegram 应用
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# 启动机器人
app.run_polling()
