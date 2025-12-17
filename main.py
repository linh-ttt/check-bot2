import os
import pytz
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Biến môi trường
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8443))  # Railway tự cấp PORT
RAILWAY_URL = os.getenv("RAILWAY_STATIC_URL")  # Ví dụ: my-app.up.railway.app

# File lưu users (đơn giản, tạm thời)
USERS_FILE = "users.txt"
tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN chưa được set")

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
    # Lưu chat_id để broadcast
    save_user(update.effective_chat.id)
    await update.message.reply_text(
        "✅ Bạn đã đăng ký nhận nhắc chấm công.\n"
        "⏰ Bot nhắc từ Thứ 2 đến Thứ 7."
    )

async def broadcast(application, message):
    for user_id in get_users():
        try:
            await application.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"Lỗi gửi tin nhắn đến {user_id}: {e}")

async def check_time(application):
    now = datetime.now(tz_vn)
    time_now = now.strftime("%H:%M")
    weekday = now.weekday()  # Thứ 2=0 ... Chủ nhật=6

    # Chỉ chạy từ Thứ 2 đến Thứ 7
    if weekday > 5:
        return

    messages = {
        "07:55": "⏰ Sắp đến giờ làm việc rồi bạn ơi! Nhớ chấm công đầy đủ trên máy chấm công trước 8:00 bạn nhé!",
        "12:00": "🍱 Đến giờ nghỉ trưa rồi bạn ơi! Quẳng nỗi lo đi mà vui sống!",
        "13:00": "⏰ Tạm biệt Nghỉ trưa! Quay lại làm việc thôi bạn ơi!",
        "17:00": "📤 Đến giờ tan làm rồi bạn ơi! Nhớ chấm công đầy đủ trước khi ra về bạn nhé!"
    }

    if time_now in messages:
        await broadcast(application, messages[time_now])

def main():
    # Khởi tạo app
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Scheduler định kỳ 1 phút để kiểm tra giờ gửi
    scheduler = AsyncIOScheduler(timezone=tz_vn)
    scheduler.add_job(check_time, "interval", minutes=1, args=[application])
    scheduler.start()

    # Chạy webhook (không dùng polling)
    if not RAILWAY_URL:
        raise RuntimeError("RAILWAY_STATIC_URL chưa được set")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"https://{RAILWAY_URL}/webhook"
    )

if __name__ == "__main__":
    main()
