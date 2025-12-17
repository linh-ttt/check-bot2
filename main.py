import os
import pytz
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Cấu hình logging để Railway in log ra ngoài
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Biến môi trường
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8443))  # Railway cấp PORT tự động
RAILWAY_URL = os.getenv("RAILWAY_STATIC_URL")  # Ví dụ: check-bot-production.up.railway.app

USERS_FILE = "users.txt"
tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")

if not BOT_TOKEN or not RAILWAY_URL:
    raise RuntimeError("Thiếu BOT_TOKEN hoặc RAILWAY_STATIC_URL")

def get_users():
    if not os.path.exists(USERS_FILE):
        return set()
    with open(USERS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_user(user_id):
    users = get_users()
    users.add(str(user_id))
    with open(USERS_FILE, "w") as f:
        f.write("\n".join(sorted(users)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    await update.message.reply_text(
        "✅ Bạn đã đăng ký nhận nhắc chấm công.\n⏰ Bot nhắc từ Thứ 2 đến Thứ 7."
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE): remove_user(update.effective_chat.id) await update.message.reply_text("❌ Bạn đã hủy đăng ký nhận thông báo.")

async def broadcast(application, message):
    for user_id in get_users():
        try:
            await application.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logger.error(f"Lỗi gửi tin nhắn đến {user_id}: {e}")

async def check_time(application):
    now = datetime.now(tz_vn)
    time_now = now.strftime("%H:%M")
    weekday = now.weekday()  # Thứ 2=0 ... Chủ nhật=6

    if weekday > 5:
        return

    messages = {
        "07:55": "⏰ Sắp đến giờ làm việc rồi bạn ơi! Nhớ chấm công đầy đủ trước 8:00 nhé!",
        "12:00": "🍱 Đến giờ nghỉ trưa rồi bạn ơi!",
        "13:00": "⏰ Tạm biệt nghỉ trưa! Quay lại làm việc thôi!",
        "17:00": "📤 Đến giờ tan làm rồi bạn ơi! Nhớ chấm công trước khi ra về nhé!",
        "00:31": "Test lan 3",
        "00:29": "Test lan 1",
        "00:30": "Test lan 2"
    }

    if time_now in messages:
        await broadcast(application, messages[time_now])

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler(timezone=tz_vn)
    scheduler.add_job(check_time, "interval", minutes=1, args=[application])
    scheduler.start()

    # webhook đúng cách: url_path = BOT_TOKEN
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{RAILWAY_URL}/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
