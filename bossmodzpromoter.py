# Promoter Bot - Telebot + SQLite
# Run:
#   pip install pyTelegramBotAPI
#   python main.py
#
# Edit BOT_TOKEN and ADMIN_IDS before running.

import sqlite3
import time
from datetime import datetime, timedelta

import telebot
from telebot import types

BOT_TOKEN = "8787325568:AAGiUr3H4II_AveoMddF52XjIDw01P570Hs"

# Add your Telegram numeric admin IDs here
ADMIN_IDS = [8756340925, 2006252443, 8263525850]

SUPPORT_USERNAME = "@KINGSELLERTOP"
BOT_NAME = "Boss Modz Promoters"
DB_NAME = "promoter_bot.db"

PACKAGES = ["1", "3", "7", "15", "30"]

def get_package_by_views(views: int):
    if views >= 20000:
        return "30"
    if views >= 10000:
        return "15"
    if views >= 5000:
        return "7"
    if views >= 2000:
        return "3"
    if views >= 500:
        return "1"
    return None

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

user_steps = {}
admin_steps = {}


# ---------------- DATABASE ----------------

def db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def setup_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        package TEXT NOT NULL,
        key_value TEXT NOT NULL,
        status TEXT DEFAULT 'available',
        added_by INTEGER,
        added_at TEXT,
        used_by INTEGER,
        used_at TEXT,
        request_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        promo_text TEXT NOT NULL,
        views INTEGER NOT NULL,
        package TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        key_value TEXT,
        created_at TEXT,
        approved_by INTEGER,
        approved_at TEXT,
        reject_reason TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        rating INTEGER NOT NULL,
        created_at TEXT
    )
    """)

    con.commit()
    con.close()


def save_user(message):
    con = db()
    cur = con.cursor()
    cur.execute("""
    INSERT OR IGNORE INTO users(user_id, username, first_name, joined_at)
    VALUES (?, ?, ?, ?)
    """, (
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name or "",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    con.commit()
    con.close()


def is_admin(user_id):
    return user_id in ADMIN_IDS


def is_youtube_link(text):
    text = (text or "").strip().lower()
    if not text.startswith(("http://", "https://")):
        return False
    blocked = ["t.me/", "telegram.me/", "telegram.dog/"]
    if any(x in text for x in blocked):
        return False
    allowed = ["youtube.com/watch", "youtu.be/", "youtube.com/shorts/", "m.youtube.com/watch"]
    return any(x in text for x in allowed)


def ending_text():
    return (
        "\n\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ <b>Thank You For Using</b>\n"
        "🔥 <b>Boss Modz Promoters</b> 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 Fast  |  🛡 Secure  |  ⭐ Trusted"
    )


def get_rating_cooldown(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT created_at FROM ratings WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    con.close()

    if not row or not row[0]:
        return None

    try:
        last_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

    next_time = last_time + timedelta(hours=24)
    now = datetime.now()
    if now >= next_time:
        return None

    remaining = next_time - now
    total_seconds = int(remaining.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d} Hours {minutes:02d} Minutes {seconds:02d} Seconds"


# ---------------- KEYBOARDS ----------------

def main_keyboard(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📢 Submit Promotion", "📞 Support")
    kb.row("⭐ Rate Service", "ℹ️ Information")
    if is_admin(user_id):
        kb.row("👑 Admin Panel")
    return kb


def admin_panel_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📦 View Stock", callback_data="admin_stock"),
        types.InlineKeyboardButton("➕ Add Stock", callback_data="admin_add_stock"),
        types.InlineKeyboardButton("📋 Pending Requests", callback_data="admin_pending"),
        types.InlineKeyboardButton("⭐ View Ratings", callback_data="admin_ratings"),
        types.InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
    )
    return kb


def package_inline(prefix="addstock"):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("1 Day", callback_data=f"{prefix}_1"),
        types.InlineKeyboardButton("3 Day", callback_data=f"{prefix}_3"),
        types.InlineKeyboardButton("7 Day", callback_data=f"{prefix}_7"),
        types.InlineKeyboardButton("15 Day", callback_data=f"{prefix}_15"),
        types.InlineKeyboardButton("30 Day", callback_data=f"{prefix}_30"),
    )
    return kb


def submit_package_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🟢 500 Views → 1 Day Key", callback_data="submitpkg_500_1"),
        types.InlineKeyboardButton("🔵 2,000 Views → 3 Day Key", callback_data="submitpkg_2000_3"),
        types.InlineKeyboardButton("🟣 5,000 Views → 7 Day Key", callback_data="submitpkg_5000_7"),
        types.InlineKeyboardButton("🟠 10,000 Views → 15 Day Key", callback_data="submitpkg_10000_15"),
        types.InlineKeyboardButton("🔴 20,000 Views → 30 Day Key", callback_data="submitpkg_20000_30"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="submitpkg_cancel")
    )
    return kb


def approve_keyboard(req_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{req_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{req_id}")
    )
    return kb


def rating_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=5)
    kb.add(
        types.InlineKeyboardButton("⭐", callback_data="rate_1"),
        types.InlineKeyboardButton("⭐⭐", callback_data="rate_2"),
        types.InlineKeyboardButton("⭐⭐⭐", callback_data="rate_3"),
        types.InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rate_4"),
        types.InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rate_5"),
    )
    return kb


# ---------------- HELPERS ----------------

def notify_admins(text, markup=None):
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, text, reply_markup=markup)
        except Exception:
            pass


def stock_count(package):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM stock WHERE package=? AND status='available'", (package,))
    count = cur.fetchone()[0]
    con.close()
    return count


def get_stock_text():
    lines = ["<b>Current Stock</b>\n"]
    for p in PACKAGES:
        lines.append(f"{p} Day : {stock_count(p)} Keys")
    return "\n".join(lines)


def pop_key(package, user_id, request_id):
    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT id, key_value FROM stock
    WHERE package=? AND status='available'
    ORDER BY id ASC LIMIT 1
    """, (package,))
    row = cur.fetchone()

    if not row:
        con.close()
        return None

    key_id, key_value = row
    cur.execute("""
    UPDATE stock
    SET status='used', used_by=?, used_at=?, request_id=?
    WHERE id=?
    """, (
        user_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        request_id,
        key_id
    ))

    con.commit()
    con.close()
    return key_value


def create_request(user_id, username, promo_text, views, package):
    con = db()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO requests(user_id, username, promo_text, views, package, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        username or "",
        promo_text,
        views,
        package,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    req_id = cur.lastrowid
    con.commit()
    con.close()
    return req_id


def get_request(req_id):
    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT id, user_id, username, promo_text, views, package, status, key_value, created_at
    FROM requests WHERE id=?
    """, (req_id,))
    row = cur.fetchone()
    con.close()
    return row


def update_request_approved(req_id, admin_id, key_value):
    con = db()
    cur = con.cursor()
    cur.execute("""
    UPDATE requests
    SET status='approved', approved_by=?, approved_at=?, key_value=?
    WHERE id=?
    """, (
        admin_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        key_value,
        req_id
    ))
    con.commit()
    con.close()


def update_request_rejected(req_id, admin_id, reason="Rejected by admin"):
    con = db()
    cur = con.cursor()
    cur.execute("""
    UPDATE requests
    SET status='rejected', approved_by=?, approved_at=?, reject_reason=?
    WHERE id=?
    """, (
        admin_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        reason,
        req_id
    ))
    con.commit()
    con.close()


def save_rating(user_id, username, rating):
    con = db()
    cur = con.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO ratings(user_id, username, rating, created_at)
    VALUES (?, ?, ?, ?)
    """, (
        user_id,
        username or "",
        rating,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    con.commit()
    con.close()


def ratings_text():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*), COALESCE(AVG(rating), 0) FROM ratings")
    total, avg = cur.fetchone()

    lines = [
        "<b>Ratings Report</b>\n",
        f"Total Ratings: {total}",
        f"Average Rating: {round(avg, 2)} / 5\n"
    ]

    for i in range(5, 0, -1):
        cur.execute("SELECT COUNT(*) FROM ratings WHERE rating=?", (i,))
        count = cur.fetchone()[0]
        lines.append(f"{'⭐' * i} : {count}")

    con.close()
    return "\n".join(lines)


# ---------------- USER COMMANDS ----------------

@bot.message_handler(commands=["start"])
def start(message):
    save_user(message)
    text = (
        f"🔥 <b>{BOT_NAME}</b> 🔥\n\n"
        "🚀 Grow your YouTube video faster with a clean promotion system.\n"
        "🎥 Submit your YouTube video link only.\n"
        "📨 Request goes directly to admin team.\n"
        "⭐ Rate our service and help us improve.\n"
        "🛡 Trusted • Fast • Premium\n\n"
        "👇 Choose an option below to continue."
        + ending_text()
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard(message.from_user.id))


@bot.message_handler(func=lambda m: m.text == "📢 Submit Promotion")
def submit_start(message):
    save_user(message)
    user_steps.pop(message.from_user.id, None)
    bot.send_message(
        message.chat.id,
        "📢 <b>Select Your Promotion Package</b>\n\n"
        "🎯 Choose your target views below first.\n\n"
        "🟢 <b>500 Views</b> → 🎁 1 Day Key\n"
        "🔵 <b>2,000 Views</b> → 🎁 3 Day Key\n"
        "🟣 <b>5,000 Views</b> → 🎁 7 Day Key\n"
        "🟠 <b>10,000 Views</b> → 🎁 15 Day Key\n"
        "🔴 <b>20,000 Views</b> → 🎁 30 Day Key\n\n"
        "⚡ After package selection, send only your YouTube video link.\n"
        "🚫 Telegram, channel, group, username, or any other link is not accepted."
        + ending_text(),
        reply_markup=submit_package_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "📞 Support")
def support(message):
    bot.send_message(
        message.chat.id,
        "🛟 <b>Boss Modz Support Center</b>\n\n"
        "Need help with promotion, submission, review, or reward?\n\n"
        f"👑 Official Support: {SUPPORT_USERNAME}\n\n"
        "📌 Send your issue clearly with your User ID and screenshot if needed.\n"
        "⚡ Fast Response • 🛡 Trusted Support • ❤️ Friendly Help"
        + ending_text(),
        reply_markup=main_keyboard(message.from_user.id)
    )


@bot.message_handler(func=lambda m: m.text == "⭐ Rate Service")
def rate(message):
    cooldown = get_rating_cooldown(message.from_user.id)
    if cooldown:
        bot.send_message(
            message.chat.id,
            "⏳ <b>Rating Cooldown</b>\n\n"
            "You have already submitted your rating today.\n\n"
            f"🕒 Please wait: <b>{cooldown}</b>\n\n"
            "before submitting another rating."
            + ending_text(),
            reply_markup=main_keyboard(message.from_user.id)
        )
        return

    bot.send_message(
        message.chat.id,
        "🌟 <b>Rate Your Experience</b>\n\n"
        "Your feedback helps Boss Modz Promoters improve.\n\n"
        "⭐ Choose a rating from 1 to 5 stars below.\n"
        "❤️ Thank you for supporting us.",
        reply_markup=rating_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "ℹ️ Information")
def information(message):
    bot.send_message(
        message.chat.id,
        "📖 <b>Boss Modz Promoters Information</b>\n\n"
        "🎥 Submit only your YouTube video link.\n"
        "⚡ Valid links are auto-submitted to admin.\n"
        "👑 Admin reviews every promotion request.\n"
        "🎁 Reward/key is delivered after approval and stock availability.\n\n"
        "✅ Accepted: YouTube video / Shorts links\n"
        "❌ Not accepted: Telegram, channel, group, username, or random links\n\n"
        "🛡 Premium • Trusted • Fast"
        + ending_text(),
        reply_markup=main_keyboard(message.from_user.id)
    )


@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel")
def admin_panel(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(
        message.chat.id,
        "👑 <b>Boss Modz Admin Panel</b>\n\n"
        "📦 Manage Stock\n"
        "📋 Review Submissions\n"
        "⭐ View Ratings\n"
        "👥 Check Total Users\n"
        "📊 View Statistics\n\n"
        "⚡ Select an option below.",
        reply_markup=admin_panel_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("submitpkg_"))
def submit_package_callback(call):
    if call.data == "submitpkg_cancel":
        user_steps.pop(call.from_user.id, None)
        bot.answer_callback_query(call.id, "Cancelled")
        bot.send_message(
            call.message.chat.id,
            "❌ <b>Submission Cancelled</b>\n\nYou can start again anytime from 📢 Submit Promotion." + ending_text(),
            reply_markup=main_keyboard(call.from_user.id)
        )
        return

    try:
        _, views, package = call.data.split("_")
    except ValueError:
        bot.answer_callback_query(call.id, "Invalid package")
        return

    user_steps[call.from_user.id] = {"step": "youtube_link", "views": int(views), "package": package}
    bot.answer_callback_query(call.id, f"Selected: {views} Views → {package} Day")
    bot.send_message(
        call.message.chat.id,
        "🎥 <b>YouTube Video Link Required</b>\n\n"
        f"✅ Selected: <b>{int(views):,} Views → {package} Day Key</b>\n\n"
        "📌 Now send your <b>YouTube Video Link</b> only.\n\n"
        "✅ Accepted: YouTube video / Shorts link\n"
        "❌ Not accepted: Telegram link, channel link, group link, username, or random text\n\n"
        "⚡ Valid link भेजते ही request automatically admin के पास submit हो जाएगी."
        + ending_text(),
        reply_markup=main_keyboard(call.from_user.id)
    )


@bot.message_handler(func=lambda m: True)
def all_text(message):
    save_user(message)
    uid = message.from_user.id

    if uid in user_steps:
        data = user_steps[uid]
        step = data.get("step")

        if step == "youtube_link":
            video_link = (message.text or "").strip()

            if not is_youtube_link(video_link):
                bot.send_message(
                    message.chat.id,
                    "❌ <b>Invalid Submission</b>\n\n"
                    "Only YouTube video links are accepted.\n\n"
                    "✅ Send a valid YouTube link like:\n"
                    "• https://youtu.be/VIDEO_ID\n"
                    "• https://www.youtube.com/watch?v=VIDEO_ID\n"
                    "• https://www.youtube.com/shorts/VIDEO_ID\n\n"
                    "🚫 Telegram, channel, group, username, or other links will not be submitted.\n\n"
                    "🎥 Please send your YouTube video link again."
                    + ending_text(),
                    reply_markup=main_keyboard(uid)
                )
                return

            username = message.from_user.username or ""
            user_steps.pop(uid, None)

            views = int(data.get("views", 500))
            package = str(data.get("package", "1"))

            req_id = create_request(uid, username, video_link, views, package)

            bot.send_message(
                uid,
                "🎉 <b>Promotion Submitted Successfully</b>\n\n"
                "✅ Your YouTube video link has been received.\n"
                "📨 Your request has been sent to the Boss Modz Promoters Admin Team.\n\n"
                f"🆔 Request ID: <code>{req_id}</code>\n"
                f"🎥 Video Link: {video_link}\n"
                f"👁 Selected Views: <b>{views}</b>\n"
                f"🎁 Selected Package: <b>{package} Day</b>\n\n"
                "⏳ Please wait while admin reviews your submission."
                + ending_text(),
                reply_markup=main_keyboard(uid)
            )

            admin_text = (
                "📢 <b>New YouTube Promotion Request</b>\n\n"
                f"🆔 Request ID: <code>{req_id}</code>\n"
                f"👤 User: @{username if username else 'NoUsername'}\n"
                f"🆔 User ID: <code>{uid}</code>\n\n"
                f"🎥 YouTube Video Link:\n{video_link}\n\n"
                f"👁 Selected Views: <b>{views}</b>\n"
                f"🎁 Selected Package: <b>{package} Day</b>\n"
                "📌 Status: Pending Approval\n"
                "⚡ Submitted automatically by bot."
            )
            notify_admins(admin_text, approve_keyboard(req_id))
            return

    if uid in admin_steps and is_admin(uid):
        data = admin_steps[uid]
        step = data.get("step")

        if step == "add_keys":
            package = data.get("package")
            raw = message.text or ""
            keys = [x.strip() for x in raw.splitlines() if x.strip()]
            if not keys:
                bot.send_message(message.chat.id, "📦 Send keys line by line.")
                return

            con = db()
            cur = con.cursor()
            for key in keys:
                cur.execute("""
                INSERT INTO stock(package, key_value, status, added_by, added_at)
                VALUES (?, ?, 'available', ?, ?)
                """, (
                    package,
                    key,
                    uid,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
            con.commit()
            con.close()

            admin_steps.pop(uid, None)
            bot.send_message(
                message.chat.id,
                f"✅ <b>Stock Added Successfully</b>\n\n📅 Package: {package} Day\n📦 Added Keys: {len(keys)}\n\n{get_stock_text()}",
                reply_markup=main_keyboard(uid)
            )
            return

    bot.send_message(
        message.chat.id,
        "👇 Please choose an option from the menu below."
        + ending_text(),
        reply_markup=main_keyboard(uid)
    )


# ---------------- CALLBACKS ----------------

@bot.callback_query_handler(func=lambda call: call.data.startswith("rate_"))
def rate_callback(call):
    cooldown = get_rating_cooldown(call.from_user.id)
    if cooldown:
        bot.answer_callback_query(call.id, "Please wait before rating again")
        bot.send_message(
            call.message.chat.id,
            "⏳ <b>Rating Cooldown</b>\n\n"
            "You have already submitted your rating today.\n\n"
            f"🕒 Please wait: <b>{cooldown}</b>\n\n"
            "before submitting another rating."
            + ending_text(),
            reply_markup=main_keyboard(call.from_user.id)
        )
        return

    rating = int(call.data.replace("rate_", ""))
    save_rating(call.from_user.id, call.from_user.username or "", rating)

    bot.answer_callback_query(call.id, f"Thanks for {rating} star rating")
    bot.send_message(
        call.message.chat.id,
        "🎉 <b>Thank You</b>\n\n"
        f"❤️ Your rating has been saved successfully.\n"
        f"⭐ Rating: {'⭐' * rating}\n\n"
        "We appreciate your valuable feedback."
        + ending_text(),
        reply_markup=main_keyboard(call.from_user.id)
    )

    notify_admins(
        "⭐ <b>New Rating Received</b>\n\n"
        f"👤 User: @{call.from_user.username if call.from_user.username else 'NoUsername'}\n"
        f"🆔 User ID: <code>{call.from_user.id}</code>\n"
        f"⭐ Rating: {'⭐' * rating}"
    )


@bot.callback_query_handler(func=lambda call: call.data == "admin_stock")
def admin_stock(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Admin only")
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, get_stock_text(), reply_markup=admin_panel_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == "admin_add_stock")
def admin_add_stock(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Admin only")
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "<b>Select package for stock</b>", reply_markup=package_inline("addstock"))


@bot.callback_query_handler(func=lambda call: call.data.startswith("addstock_"))
def addstock_package(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Admin only")
        return

    package = call.data.replace("addstock_", "")
    if package not in PACKAGES:
        bot.answer_callback_query(call.id, "Invalid package")
        return

    admin_steps[call.from_user.id] = {"step": "add_keys", "package": package}
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"➕ <b>Add {package} Day Stock</b>\n\n📦 Send keys line by line.\n✅ One key per line."
    )


@bot.callback_query_handler(func=lambda call: call.data == "admin_pending")
def admin_pending(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Admin only")
        return

    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT id, user_id, username, promo_text, views, package, created_at
    FROM requests WHERE status='pending'
    ORDER BY id DESC LIMIT 10
    """)
    rows = cur.fetchall()
    con.close()

    bot.answer_callback_query(call.id)
    if not rows:
        bot.send_message(call.message.chat.id, "No pending requests.")
        return

    for r in rows:
        req_id, user_id, username, promo_text, views, package, created_at = r
        text = (
            "📋 <b>Pending YouTube Promotion Request</b>\n\n"
            f"🆔 Request ID: <code>{req_id}</code>\n"
            f"👤 User: @{username if username else 'NoUsername'}\n"
            f"🆔 User ID: <code>{user_id}</code>\n\n"
            f"🎥 YouTube Video Link:\n{promo_text}\n\n"
            f"📅 Date: {created_at}"
        )
        bot.send_message(call.message.chat.id, text, reply_markup=approve_keyboard(req_id))


@bot.callback_query_handler(func=lambda call: call.data == "admin_ratings")
def admin_ratings(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Admin only")
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, ratings_text(), reply_markup=admin_panel_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Admin only")
        return

    con = db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM requests")
    total_req = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM requests WHERE status='pending'")
    pending = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM requests WHERE status='approved'")
    approved = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM requests WHERE status='rejected'")
    rejected = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ratings")
    total_ratings = cur.fetchone()[0]
    con.close()

    text = (
        "<b>Statistics</b>\n\n"
        f"Total Users: {users}\n"
        f"Total Requests: {total_req}\n"
        f"Pending: {pending}\n"
        f"Approved: {approved}\n"
        f"Rejected: {rejected}\n"
        f"Total Ratings: {total_ratings}\n\n"
        f"{get_stock_text()}"
    )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, text, reply_markup=admin_panel_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_request(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Admin only")
        return

    req_id = int(call.data.replace("approve_", ""))
    row = get_request(req_id)

    if not row:
        bot.answer_callback_query(call.id, "Request not found")
        return

    req_id, user_id, username, promo_text, views, package, status, key_value, created_at = row

    if status != "pending":
        bot.answer_callback_query(call.id, f"Already {status}")
        return

    key = pop_key(package, user_id, req_id)
    if not key:
        try:
    bot.answer_callback_query(call.id, "Out of stock")
except Exception:
    pass
        bot.send_message(
            call.message.chat.id,
            f"<b>Out of Stock</b>\n\nPackage: {package} Day\nRequest ID: {req_id}\n\nPlease add stock first."
        )
        return

    update_request_approved(req_id, call.from_user.id, key)

    user_msg = (
        "✅ <b>Promotion Approved</b>\n\n"
        "Your YouTube promotion request has been approved.\n\n"
        f"🎁 Your Key:\n<code>{key}</code>"
        + ending_text()
    )

    try:
        bot.send_message(user_id, user_msg, reply_markup=main_keyboard(user_id))
    except Exception:
        pass

    admin_name = call.from_user.username or call.from_user.first_name or str(call.from_user.id)
    admin_msg = (
        "✅ <b>Request Approved Successfully</b>\n\n"
        f"🆔 Request ID: <code>{req_id}</code>\n"
        f"👤 User: @{username if username else 'NoUsername'}\n"
        f"🆔 User ID: <code>{user_id}</code>\n\n"
        f"🎥 YouTube Video Link:\n{promo_text}\n\n"
        f"🎁 Key Delivered: <code>{key}</code>\n"
        f"👑 Approved By: @{admin_name}\n\n"
        f"📦 Remaining {package} Day Stock: {stock_count(package)}"
    )
    notify_admins(admin_msg)

    bot.answer_callback_query(call.id, "Approved and key delivered")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_request(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Admin only")
        return

    req_id = int(call.data.replace("reject_", ""))
    row = get_request(req_id)

    if not row:
        bot.answer_callback_query(call.id, "Request not found")
        return

    req_id, user_id, username, promo_text, views, package, status, key_value, created_at = row

    if status != "pending":
        bot.answer_callback_query(call.id, f"Already {status}")
        return

    update_request_rejected(req_id, call.from_user.id)

    try:
        bot.send_message(
            user_id,
            "❌ <b>Promotion Rejected</b>\n\nYour YouTube promotion request was rejected by admin." + ending_text(),
            reply_markup=main_keyboard(user_id)
        )
    except Exception:
        pass

    admin_name = call.from_user.username or call.from_user.first_name or str(call.from_user.id)
    notify_admins(
        "<b>Request Rejected</b>\n\n"
        f"Request ID: {req_id}\n"
        f"User: @{username if username else 'NoUsername'}\n"
        f"Package: {package} Day\n"
        f"Rejected By: @{admin_name}"
    )

    bot.answer_callback_query(call.id, "Rejected")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass


# ---------------- RUN ----------------

if __name__ == "__main__":
    setup_db()
    print(f"{BOT_NAME} started...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Bot error:", e)
            time.sleep(5)
