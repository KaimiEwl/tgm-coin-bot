from __future__ import annotations

import html as html_lib
from io import BytesIO
import logging
import os
import random
import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from storage import (
    FEATURE_FIREWORKS,
    FEATURE_OWNER_TRIBUTE,
    FEATURE_REFERRALS,
    FEATURE_SEND_COINS,
    FEATURE_SUPER_PRIZE,
    FEATURE_TEST_MODE,
    FEATURE_WEBAPP,
    LANGUAGE_EN,
    LANGUAGE_RU,
    Storage,
)


DB_PATH = os.getenv("DB_PATH", "coins.db")
CHAT_REWARD_MIN = max(1, int(os.getenv("CHAT_REWARD_MIN", "1")))
CHAT_REWARD_MAX = max(CHAT_REWARD_MIN, int(os.getenv("CHAT_REWARD_MAX", "10")))
CHAT_DAILY_FIRST_MIN = max(1, int(os.getenv("CHAT_DAILY_FIRST_MIN", "1")))
CHAT_DAILY_FIRST_MAX = max(CHAT_DAILY_FIRST_MIN, int(os.getenv("CHAT_DAILY_FIRST_MAX", "100")))
SUPER_REWARD_MIN = 1
SUPER_REWARD_MAX = 1000
SUPER_PRIZE_CHANCE = float(os.getenv("SUPER_PRIZE_CHANCE", "0.03"))
REWARD_COOLDOWN_SECONDS = 60
OWNER_CACHE_TTL_SECONDS = 600
UNTRUSTED_STREAK_SECONDS = 5 * 60 * 60
UNTRUSTED_MAX_GAP_SECONDS = int(os.getenv("UNTRUSTED_MAX_GAP_SECONDS", "600"))
FIREWORK_WINNERS_LIMIT = 15
FIREWORK_REWARD_MIN = 1
FIREWORK_REWARD_MAX = 100
FIREWORK_PERIOD_MAX = int(os.getenv("FIREWORK_PERIOD_MAX", os.getenv("FIREWORK_DAILY_MAX", "2")))
FIREWORK_BASE_DAILY_POINTS = float(os.getenv("FIREWORK_BASE_DAILY_POINTS", "500"))
FIREWORK_ACTIVITY_BONUS_DAILY_POINTS = float(
    os.getenv("FIREWORK_ACTIVITY_BONUS_DAILY_POINTS", "100")
)
FIREWORK_ACTIVITY_WINDOW_HOURS = int(os.getenv("FIREWORK_ACTIVITY_WINDOW_HOURS", "6"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://127.0.0.1:8080/miniapp")
REFERRAL_BONUS_AMOUNT = int(os.getenv("REFERRAL_BONUS_AMOUNT", "1000"))
REFERRAL_BONUS_LIMIT = int(os.getenv("REFERRAL_BONUS_LIMIT", "6"))
REFERRAL_COMMISSION_PERCENT = int(os.getenv("REFERRAL_COMMISSION_PERCENT", "10"))
REWARD_MESSAGE_PLACEHOLDER = "\u2063"

try:
    from PIL import Image, ImageDraw

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


MESSAGES = {
    LANGUAGE_RU: {
        "start": (
            "Привет, я бот TGM Coin.\n"
            "Поставь меня в чат и сделай админом: владелец чата получает 10% от всех раздач в чате.\n"
            "Я даю за сообщения от 1 до 10 TGM coin (первое начисление в день: 1-100).\n"
            "Иногда появляется супер-приз: напиши мне в личку и получишь от 1 до 1000 TGM coin.\n"
            "Баланс: /info\n"
            "Язык: /lang\n"
            "Перевод: /send 10 tgm (reply)\n"
            "Рефералы: /ref\n"
            "Веб-апп: /app\n"
            "Меню: /menu"
        ),
        "menu": "Команды:\n/start\n/info\n/lang\n/send 10 tgm (reply)\n/ref\n/app\n/menu",
        "info_balance": "Твой баланс: {coins} TGM coin.",
        "info_trust_trusted": "Надежность: надежный.",
        "info_trust_untrusted": "Надежность: ненадежный.",
        "info_pending_super": "У тебя есть активный супер-приз. Напиши мне в личку, чтобы забрать.",
        "reward_gain": "+{reward} TGM coin.",
        "reward_total": "Теперь у тебя: {total} TGM coin.",
        "reward_short": "+{reward} TGM coin",
        "reward_cooldown": "Кулдаун: подожди {seconds} сек. Сейчас начисление недоступно.",
        "status_flagged": "Статус надежности обновлен: пользователь помечен как ненадежный.",
        "progress_line": "Прогресс фейерверка: {percent}% ({points}/{goal}).",
        "period_line": "Фейерверков в периоде ({period_name}): {period_count}/{period_max}.",
        "period_limit": "Лимит фейерверков в текущем периоде достигнут для этого чата.",
        "firework_triggered": "Фейерверк! Прогресс чата достиг 100%.",
        "firework_winners": "Последние 15 получили награды:",
        "firework_winners_reply": "Награды фейерверка (reply по победителям):",
        "progress_image_title": "Фейерверк: прогресс чата",
        "progress_image_caption": "Шкала фейерверка: {percent}% ({points}/{goal}).",
        "owner_tribute": "Владельцу чата начислено: {amount} TGM coin (10%).",
        "super_prompt": "Супер-приз! Напиши мне личное сообщение и ты получишь от 1 до 1000 TGM coin.",
        "super_dm": "Личка: https://t.me/{bot_username}?start=superprize",
        "super_claim": "Супер-приз получен: +{reward} TGM coin.\nТеперь у тебя: {total} TGM coin.",
        "lang_prompt": "Выбери язык интерфейса:",
        "lang_updated": "Язык обновлен: русский.",
        "lang_invalid": "Используй: /lang ru или /lang en",
        "lang_current": "Текущий язык: русский.",
        "send_disabled": "Переводы сейчас выключены.",
        "send_usage": "Использование: ответь на сообщение командой /send 10 tgm",
        "send_invalid_amount": "Неверная сумма. Пример: /send 10 tgm",
        "send_target_invalid": "Нельзя отправить монеты этому получателю.",
        "send_self": "Себе переводить нельзя.",
        "send_insufficient": "Недостаточно монет. Твой баланс: {balance} TGM coin.",
        "send_ok": (
            "Перевод отправлен: {amount} TGM coin -> {recipient}.\n"
            "Твой баланс: {sender_balance} TGM coin.\n"
            "Баланс получателя: {recipient_balance} TGM coin."
        ),
        "ref_link": "Твоя реферальная ссылка:\n{link}",
        "ref_stats": (
            "Рефералы: {total}\n"
            "Рефералы с бонусом: {rewarded}/{limit}\n"
            "Доход от 10% комиссии: {commission_total} TGM coin."
        ),
        "ref_assigned": "Рефералка активирована: ты пришел по приглашению.",
        "ref_bonus_sent": "Рефереру отправлен бонус: +{amount} TGM coin.",
        "app_unavailable": "Веб-апп сейчас недоступен.",
        "app_open": "Открыть веб-апп:",
        "app_button": "APP",
        "balance_button": "Баланс",
        "balance_menu_text": "Ваш баланс: {coins} TGM coin.\nОбщий баланс: {total_coins} TGM coin.",
        "broadcast_enabled_notice": "Рассылки активны.",
    },
    LANGUAGE_EN: {
        "start": (
            "Hi, I am the TGM Coin bot.\n"
            "Add me to a chat and make me admin: the chat owner gets 10% from all chat rewards.\n"
            "I reward 1 to 10 TGM coin for messages (first reward of the day: 1-100).\n"
            "Sometimes a super prize appears: send me a DM and get 1 to 1000 TGM coin.\n"
            "Balance: /info\n"
            "Language: /lang\n"
            "Transfer: /send 10 tgm (reply)\n"
            "Referrals: /ref\n"
            "Web app: /app\n"
            "Menu: /menu"
        ),
        "menu": "Commands:\n/start\n/info\n/lang\n/send 10 tgm (reply)\n/ref\n/app\n/menu",
        "info_balance": "Your balance: {coins} TGM coin.",
        "info_trust_trusted": "Trust: trusted.",
        "info_trust_untrusted": "Trust: untrusted.",
        "info_pending_super": "You have an active super prize. Send me a DM to claim it.",
        "reward_gain": "+{reward} TGM coin.",
        "reward_total": "Now you have: {total} TGM coin.",
        "reward_short": "+{reward} TGM coin",
        "reward_cooldown": "Cooldown: wait {seconds} sec. Reward is not available yet.",
        "status_flagged": "Trust status updated: user marked as untrusted.",
        "progress_line": "Firework progress: {percent}% ({points}/{goal}).",
        "period_line": "Fireworks in period ({period_name}): {period_count}/{period_max}.",
        "period_limit": "Firework limit reached in the current period for this chat.",
        "firework_triggered": "Firework! Chat progress reached 100%.",
        "firework_winners": "Last 15 users received rewards:",
        "firework_winners_reply": "Firework rewards (reply by winners):",
        "progress_image_title": "Firework: chat progress",
        "progress_image_caption": "Firework scale: {percent}% ({points}/{goal}).",
        "owner_tribute": "Chat owner received: {amount} TGM coin (10%).",
        "super_prompt": "Super prize! Send me a DM and you will get from 1 to 1000 TGM coin.",
        "super_dm": "DM: https://t.me/{bot_username}?start=superprize",
        "super_claim": "Super prize claimed: +{reward} TGM coin.\nNow you have: {total} TGM coin.",
        "lang_prompt": "Choose interface language:",
        "lang_updated": "Language updated: English.",
        "lang_invalid": "Use: /lang ru or /lang en",
        "lang_current": "Current language: English.",
        "send_disabled": "Transfers are currently disabled.",
        "send_usage": "Usage: reply to a message with /send 10 tgm",
        "send_invalid_amount": "Invalid amount. Example: /send 10 tgm",
        "send_target_invalid": "Cannot send coins to this recipient.",
        "send_self": "You cannot transfer to yourself.",
        "send_insufficient": "Not enough coins. Your balance: {balance} TGM coin.",
        "send_ok": (
            "Transfer sent: {amount} TGM coin -> {recipient}.\n"
            "Your balance: {sender_balance} TGM coin.\n"
            "Recipient balance: {recipient_balance} TGM coin."
        ),
        "ref_link": "Your referral link:\n{link}",
        "ref_stats": (
            "Referrals: {total}\n"
            "Rewarded referrals: {rewarded}/{limit}\n"
            "Income from 10% commission: {commission_total} TGM coin."
        ),
        "ref_assigned": "Referral activated: you joined by an invite link.",
        "ref_bonus_sent": "Referral bonus sent to inviter: +{amount} TGM coin.",
        "app_unavailable": "Web app is currently unavailable.",
        "app_open": "Open web app:",
        "app_button": "APP",
        "balance_button": "Balance",
        "balance_menu_text": "Your balance: {coins} TGM coin.\nTotal balance: {total_coins} TGM coin.",
        "broadcast_enabled_notice": "Broadcasts are active.",
    },
}


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
# Avoid leaking bot token via http client debug logs (URLs include the token).
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
storage = Storage(DB_PATH)
owner_cache: dict[int, tuple[int, float]] = {}

BOT_STARTED_AT = time.time()
BOT_STATS = {
    "updates": 0,
    "rewarded": 0,
    "cooldown": 0,
    "errors": 0,
    "last_update_ts": 0.0,
}


def normalized_super_prize_chance() -> float:
    if SUPER_PRIZE_CHANCE < 0:
        return 0.0
    if SUPER_PRIZE_CHANCE > 1:
        return 1.0
    return SUPER_PRIZE_CHANCE


def tr(lang: str, key: str, **kwargs) -> str:
    safe_lang = lang if lang in {LANGUAGE_RU, LANGUAGE_EN} else LANGUAGE_RU
    template = MESSAGES[safe_lang].get(key, MESSAGES[LANGUAGE_RU][key])
    return template.format(**kwargs)


def build_lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Русский", callback_data="set_lang:ru"),
                InlineKeyboardButton("English", callback_data="set_lang:en"),
            ]
        ]
    )


def build_user_menu(has_webapp: bool = True) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("/info"), KeyboardButton("/ref")],
        [KeyboardButton("/lang"), KeyboardButton("/menu")],
        [KeyboardButton("/send 10 tgm")],
    ]
    if has_webapp:
        rows.append([KeyboardButton("/app")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def webapp_url_for(user_id: int | None, lang: str | None) -> str:
    base = (WEBAPP_URL or "").strip()
    if not base:
        return ""
    parsed = urlparse(base)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if lang in {LANGUAGE_RU, LANGUAGE_EN}:
        query["lang"] = lang
    if user_id is not None and int(user_id) > 0:
        query["uid"] = str(int(user_id))
    new_query = urlencode(query)
    return urlunparse(parsed._replace(query=new_query))


def build_webapp_button(lang: str, user_id: int | None = None) -> InlineKeyboardButton | None:
    if not WEBAPP_URL.strip():
        return None
    url = webapp_url_for(user_id=user_id, lang=lang) or WEBAPP_URL
    if WEBAPP_URL.startswith("https://"):
        return InlineKeyboardButton(
            text=tr(lang, "app_button"),
            web_app=WebAppInfo(url=url),
        )
    return InlineKeyboardButton(text=tr(lang, "app_button"), url=url)


def build_balance_menu_keyboard(lang: str, user_id: int | None = None) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=tr(lang, "balance_button"), callback_data="balance_menu")]]
    webapp_button = build_webapp_button(lang, user_id=user_id)
    if webapp_button is not None:
        rows.append([webapp_button])
    return InlineKeyboardMarkup(rows)


def build_reward_keyboard(lang: str, user_id: int, reward: int) -> InlineKeyboardMarkup | None:
    if not WEBAPP_URL.strip():
        return None
    text = f"+{reward} TGM coin"
    url = webapp_url_for(user_id=user_id, lang=lang) or WEBAPP_URL
    if WEBAPP_URL.startswith("https://"):
        button = InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))
    else:
        button = InlineKeyboardButton(text=text, url=url)
    return InlineKeyboardMarkup([[button]])


def build_cooldown_keyboard(lang: str, user_id: int, seconds_left: int) -> InlineKeyboardMarkup | None:
    if not WEBAPP_URL.strip():
        return None
    safe_left = max(1, int(seconds_left))
    text = f"⏳ {safe_left}s"
    url = webapp_url_for(user_id=user_id, lang=lang) or WEBAPP_URL
    if WEBAPP_URL.startswith("https://"):
        button = InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))
    else:
        button = InlineKeyboardButton(text=text, url=url)
    return InlineKeyboardMarkup([[button]])


def period_name(lang: str, code: str) -> str:
    names_ru = {
        "night": "ночь",
        "morning": "утро",
        "day": "день",
        "evening": "вечер",
    }
    names_en = {
        "night": "night",
        "morning": "morning",
        "day": "day",
        "evening": "evening",
    }
    if lang == LANGUAGE_EN:
        return names_en.get(code, code or "period")
    return names_ru.get(code, code or "период")


def build_firework_progress_image(lang: str, percent: int, points: int, goal: int) -> bytes | None:
    if not PIL_AVAILABLE:
        return None
    clamped_percent = max(0, min(100, int(percent)))
    width, height = 980, 320
    img = Image.new("RGB", (width, height), (13, 19, 35))
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, width, height), fill=(13, 19, 35))
    draw.rectangle((0, height - 70, width, height), fill=(18, 28, 48))

    title = tr(lang, "progress_image_title")
    draw.text((34, 22), title, fill=(226, 232, 240))
    draw.text((34, 54), f"{clamped_percent}% ({points}/{goal})", fill=(125, 211, 252))

    bar_left, bar_top = 34, 118
    bar_right, bar_bottom = width - 34, 156
    draw.rounded_rectangle((bar_left, bar_top, bar_right, bar_bottom), radius=12, fill=(51, 65, 85))
    fill_right = bar_left + int((bar_right - bar_left) * clamped_percent / 100)
    draw.rounded_rectangle((bar_left, bar_top, fill_right, bar_bottom), radius=12, fill=(56, 189, 248))

    marks_y = 208
    label_y = 226
    for mark in range(10, 101, 10):
        x = bar_left + int((bar_right - bar_left) * mark / 100)
        active = clamped_percent >= mark
        dot_color = (52, 211, 153) if active else (100, 116, 139)
        text_color = (165, 243, 252) if active else (148, 163, 184)
        draw.ellipse((x - 7, marks_y - 7, x + 7, marks_y + 7), fill=dot_color)
        draw.text((x - 12, label_y), f"{mark}%", fill=text_color)

    draw.text((34, height - 44), "10% 20% 30% ... 100%", fill=(148, 163, 184))

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def winner_label_plain(winner: dict) -> str:
    if winner.get("username"):
        return f"@{winner['username']}"
    if winner.get("first_name"):
        return str(winner["first_name"])
    return f"id:{winner['user_id']}"


def winner_label_html(winner: dict) -> str:
    if winner.get("username"):
        return f"@{html_lib.escape(str(winner['username']))}"
    name = winner.get("first_name") or f"id:{winner['user_id']}"
    return f"<a href='tg://user?id={winner['user_id']}'>{html_lib.escape(str(name))}</a>"


def can_trigger_super_prize(chat_type: str) -> bool:
    if chat_type not in {"group", "supergroup"}:
        return False
    return random.random() < normalized_super_prize_chance()


async def get_chat_owner_id(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> int | None:
    cached = owner_cache.get(chat_id)
    now = time.time()
    if cached is not None:
        owner_id, expires_at = cached
        if now <= expires_at:
            return owner_id

    try:
        admins = await context.bot.get_chat_administrators(chat_id)
    except TelegramError as exc:
        logger.warning("Cannot fetch chat administrators for chat_id=%s: %s", chat_id, exc)
        return None

    for admin in admins:
        if admin.status == "creator":
            owner_id = admin.user.id
            owner_cache[chat_id] = (owner_id, now + OWNER_CACHE_TTL_SECONDS)
            return owner_id

    return None


def get_user_lang(user_id: int) -> str:
    return storage.get_user_language(user_id)


def user_label(user_id: int, username: str, first_name: str) -> str:
    if username:
        return f"@{username}"
    if first_name:
        return first_name
    return f"id:{user_id}"


def parse_referrer_id(args: list[str]) -> int | None:
    for arg in args:
        value = arg.strip().lower()
        if value.startswith("ref_"):
            tail = value.replace("ref_", "", 1)
            if tail.isdigit():
                return int(tail)
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    user = update.effective_user
    if user is None or user.is_bot:
        return

    storage.ensure_user(user.id, user.username or "", user.first_name or "")
    if update.effective_chat and update.effective_chat.type == "private":
        storage.set_user_activated(user.id, enabled=True)
    lang = get_user_lang(user.id)
    super_enabled = storage.is_feature_enabled(FEATURE_SUPER_PRIZE, default=True)
    referrals_enabled = storage.is_feature_enabled(FEATURE_REFERRALS, default=True)
    webapp_enabled = storage.is_feature_enabled(FEATURE_WEBAPP, default=True)

    extra_lines: list[str] = []
    if update.effective_chat and update.effective_chat.type == "private" and referrals_enabled:
        referrer_id = parse_referrer_id(context.args or [])
        if referrer_id is not None and referrer_id != user.id:
            referral_result = storage.set_referrer(
                referred_user_id=user.id,
                referrer_user_id=referrer_id,
                referral_bonus_amount=REFERRAL_BONUS_AMOUNT,
                referral_bonus_limit=REFERRAL_BONUS_LIMIT,
            )
            if referral_result.get("assigned"):
                extra_lines.append(tr(lang, "ref_assigned"))
                if referral_result.get("bonus_awarded"):
                    extra_lines.append(tr(lang, "ref_bonus_sent", amount=REFERRAL_BONUS_AMOUNT))

    if update.effective_chat and update.effective_chat.type == "private" and (
        super_enabled or storage.has_pending_super_prize(user.id)
    ):
        reward = random.randint(SUPER_REWARD_MIN, SUPER_REWARD_MAX)
        claim = storage.claim_super_prize(
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            reward=reward,
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
        if claim:
            claimed_reward, total = claim
            if referrals_enabled:
                storage.add_referral_commission(
                    referred_user_id=user.id,
                    referred_reward_amount=claimed_reward,
                    chat_id=update.effective_chat.id,
                    message_id=update.message.message_id,
                    percent=REFERRAL_COMMISSION_PERCENT,
                )
            await update.message.reply_text(tr(lang, "super_claim", reward=claimed_reward, total=total))
            return

    start_text = tr(lang, "start")
    if extra_lines:
        start_text += "\n\n" + "\n".join(extra_lines)
    await update.message.reply_text(
        start_text,
        reply_markup=build_user_menu(has_webapp=webapp_enabled and bool(WEBAPP_URL.strip())),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    user = update.effective_user
    if user is None or user.is_bot:
        return
    storage.ensure_user(user.id, user.username or "", user.first_name or "")
    lang = get_user_lang(user.id)
    webapp_enabled = storage.is_feature_enabled(FEATURE_WEBAPP, default=True)
    coins = storage.get_coins(user.id)
    total_coins = storage.get_total_coins()
    menu_text = tr(lang, "menu")
    balance_text = tr(lang, "balance_menu_text", coins=coins, total_coins=total_coins)
    inline_keyboard = build_balance_menu_keyboard(lang, user_id=user.id)
    if not webapp_enabled or not WEBAPP_URL.strip():
        inline_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text=tr(lang, "balance_button"), callback_data="balance_menu")]]
        )
    await update.message.reply_text(
        menu_text,
        reply_markup=build_user_menu(has_webapp=webapp_enabled and bool(WEBAPP_URL.strip())),
    )
    await update.message.reply_text(balance_text, reply_markup=inline_keyboard)


async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    user = update.effective_user
    if user is None or user.is_bot:
        return
    storage.ensure_user(user.id, user.username or "", user.first_name or "")

    current_lang = get_user_lang(user.id)
    if context.args:
        requested = context.args[0].strip().lower()
        if requested in {LANGUAGE_RU, LANGUAGE_EN}:
            current_lang = storage.set_user_language(user.id, requested)
            await update.message.reply_text(
                f"{tr(current_lang, 'lang_updated')}\n{tr(current_lang, 'lang_prompt')}",
                reply_markup=build_lang_keyboard(),
            )
            return
        await update.message.reply_text(
            f"{tr(current_lang, 'lang_invalid')}\n{tr(current_lang, 'lang_prompt')}",
            reply_markup=build_lang_keyboard(),
        )
        return

    await update.message.reply_text(
        f"{tr(current_lang, 'lang_current')}\n{tr(current_lang, 'lang_prompt')}",
        reply_markup=build_lang_keyboard(),
    )


async def set_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.from_user is None:
        return

    data = query.data or ""
    if not data.startswith("set_lang:"):
        return
    code = data.split(":", 1)[1].strip().lower()
    if code not in {LANGUAGE_RU, LANGUAGE_EN}:
        code = LANGUAGE_RU

    storage.ensure_user(query.from_user.id, query.from_user.username or "", query.from_user.first_name or "")
    lang_code = storage.set_user_language(query.from_user.id, code)
    await query.answer()
    await query.edit_message_text(
        f"{tr(lang_code, 'lang_updated')}\n{tr(lang_code, 'lang_prompt')}",
        reply_markup=build_lang_keyboard(),
    )


async def balance_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.from_user is None:
        return
    if (query.data or "") != "balance_menu":
        return

    user = query.from_user
    storage.ensure_user(user.id, user.username or "", user.first_name or "")
    lang = get_user_lang(user.id)
    coins = storage.get_coins(user.id)
    total_coins = storage.get_total_coins()
    text = tr(lang, "balance_menu_text", coins=coins, total_coins=total_coins)

    await query.answer()
    if query.message:
        await query.message.reply_text(
            text,
            reply_markup=build_balance_menu_keyboard(lang, user_id=user.id),
        )


async def send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return
    sender = update.effective_user
    if sender is None or sender.is_bot:
        return

    storage.ensure_user(sender.id, sender.username or "", sender.first_name or "")
    lang = get_user_lang(sender.id)

    if not storage.is_feature_enabled(FEATURE_SEND_COINS, default=False):
        await message.reply_text(tr(lang, "send_disabled"))
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text(tr(lang, "send_usage"))
        return

    args = context.args or []
    if len(args) < 1:
        await message.reply_text(tr(lang, "send_usage"))
        return

    amount_token = args[0].replace(",", "").strip()
    if not amount_token.isdigit():
        await message.reply_text(tr(lang, "send_invalid_amount"))
        return

    amount = int(amount_token)
    if amount <= 0:
        await message.reply_text(tr(lang, "send_invalid_amount"))
        return

    if len(args) >= 2:
        unit = args[1].strip().lower()
        if unit not in {"tgm", "coin", "coins"}:
            await message.reply_text(tr(lang, "send_invalid_amount"))
            return

    recipient = message.reply_to_message.from_user
    if recipient.is_bot:
        await message.reply_text(tr(lang, "send_target_invalid"))
        return
    if recipient.id == sender.id:
        await message.reply_text(tr(lang, "send_self"))
        return

    storage.ensure_user(recipient.id, recipient.username or "", recipient.first_name or "")
    ok, sender_balance, recipient_balance, reason = storage.transfer_coins(
        sender_id=sender.id,
        sender_username=sender.username or "",
        sender_first_name=sender.first_name or "",
        recipient_id=recipient.id,
        recipient_username=recipient.username or "",
        recipient_first_name=recipient.first_name or "",
        amount=amount,
        chat_id=message.chat_id,
        message_id=message.message_id,
    )
    if not ok:
        if reason == "INSUFFICIENT_FUNDS":
            await message.reply_text(tr(lang, "send_insufficient", balance=sender_balance))
            return
        if reason == "SELF_TRANSFER":
            await message.reply_text(tr(lang, "send_self"))
            return
        await message.reply_text(tr(lang, "send_invalid_amount"))
        return

    await message.reply_text(
        tr(
            lang,
            "send_ok",
            amount=amount,
            recipient=user_label(recipient.id, recipient.username or "", recipient.first_name or ""),
            sender_balance=sender_balance,
            recipient_balance=recipient_balance,
        )
    )


async def ref(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None or user.is_bot:
        return
    storage.ensure_user(user.id, user.username or "", user.first_name or "")
    if update.effective_chat and update.effective_chat.type == "private":
        storage.set_user_activated(user.id, enabled=True)
    lang = get_user_lang(user.id)

    bot_username = context.bot.username
    if bot_username:
        link = f"https://t.me/{bot_username}?start=ref_{user.id}"
    else:
        link = f"ref_{user.id}"
    summary = storage.get_referral_summary(user.id)
    await message.reply_text(
        tr(lang, "ref_link", link=link)
        + "\n\n"
        + tr(
            lang,
            "ref_stats",
            total=summary["total_referrals"],
            rewarded=summary["rewarded_referrals"],
            limit=REFERRAL_BONUS_LIMIT,
            commission_total=summary["commission_total"],
        )
    )


async def webapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None or user.is_bot:
        return
    storage.ensure_user(user.id, user.username or "", user.first_name or "")
    lang = get_user_lang(user.id)
    webapp_enabled = storage.is_feature_enabled(FEATURE_WEBAPP, default=True)
    if not webapp_enabled or not WEBAPP_URL.strip():
        await message.reply_text(tr(lang, "app_unavailable"))
        return

    button = build_webapp_button(lang, user_id=user.id)
    if button is None:
        await message.reply_text(tr(lang, "app_unavailable"))
        return
    keyboard = InlineKeyboardMarkup([[button]])
    # Keep a minimal visible response so users don't think the bot is silent.
    await message.reply_text(tr(lang, "app_button"), reply_markup=keyboard)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    user = update.effective_user
    if user is None or user.is_bot:
        return

    storage.ensure_user(user.id, user.username or "", user.first_name or "")
    lang = get_user_lang(user.id)
    coins = storage.get_coins(user.id)
    is_trusted = storage.get_user_reliability(user.id)
    lines = [tr(lang, "info_balance", coins=coins)]
    lines.append(
        tr(lang, "info_trust_trusted") if is_trusted else tr(lang, "info_trust_untrusted")
    )
    if storage.has_pending_super_prize(user.id):
        lines.append(tr(lang, "info_pending_super"))
    webapp_enabled = storage.is_feature_enabled(FEATURE_WEBAPP, default=True)
    webapp_button = build_webapp_button(lang, user_id=user.id) if webapp_enabled else None
    markup = InlineKeyboardMarkup([[webapp_button]]) if webapp_button is not None else None
    await update.message.reply_text("\n".join(lines), reply_markup=markup)


async def reward_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    BOT_STATS["updates"] += 1
    BOT_STATS["last_update_ts"] = time.time()
    message = update.effective_message
    if not message:
        return
    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None:
        return
    logger.info(
        "MSG chat_id=%s chat_type=%s user_id=%s is_bot=%s text_len=%s",
        getattr(chat, "id", None),
        getattr(chat, "type", None),
        getattr(user, "id", None),
        getattr(user, "is_bot", None),
        len(getattr(message, "text", "") or ""),
    )
    test_mode_enabled = storage.is_feature_enabled(FEATURE_TEST_MODE, default=False)
    if user.is_bot and not test_mode_enabled:
        logger.info("IGNORED bot_user (test_mode disabled) user_id=%s", user.id)
        return
    storage.ensure_user(user.id, user.username or "", user.first_name or "")
    if chat.type == "private":
        storage.set_user_activated(user.id, enabled=True)
    lang = get_user_lang(user.id)
    super_enabled = storage.is_feature_enabled(FEATURE_SUPER_PRIZE, default=True)
    fireworks_enabled = storage.is_feature_enabled(FEATURE_FIREWORKS, default=True)
    owner_tribute_enabled = storage.is_feature_enabled(FEATURE_OWNER_TRIBUTE, default=True)
    referrals_enabled = storage.is_feature_enabled(FEATURE_REFERRALS, default=True)
    webapp_enabled = storage.is_feature_enabled(FEATURE_WEBAPP, default=True)

    reward_super = random.randint(SUPER_REWARD_MIN, SUPER_REWARD_MAX)
    super_claim = None
    if chat.type == "private" and (super_enabled or storage.has_pending_super_prize(user.id)):
        super_claim = storage.claim_super_prize(
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            reward=reward_super,
            chat_id=chat.id,
            message_id=message.message_id,
        )
    if super_claim:
        claimed_reward, total = super_claim
        if referrals_enabled:
            storage.add_referral_commission(
                referred_user_id=user.id,
                referred_reward_amount=claimed_reward,
                chat_id=chat.id,
                message_id=message.message_id,
                percent=REFERRAL_COMMISSION_PERCENT,
            )
        await message.reply_text(tr(lang, "super_claim", reward=claimed_reward, total=total))
        return

    is_first_reward_today = not storage.has_chat_reward_today(user.id)
    if is_first_reward_today:
        reward = random.randint(CHAT_DAILY_FIRST_MIN, CHAT_DAILY_FIRST_MAX)
    else:
        reward = random.randint(CHAT_REWARD_MIN, CHAT_REWARD_MAX)
    granted, total, _cooldown_left = storage.add_chat_reward_with_cooldown(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        amount=reward,
        chat_id=chat.id,
        message_id=message.message_id,
        cooldown_seconds=REWARD_COOLDOWN_SECONDS,
    )
    if not granted:
        BOT_STATS["cooldown"] += 1
        # User expectation: reply to every message. We keep the "1 reward per minute" economy rule,
        # but always reply with a cooldown button so it doesn't look broken.
        webapp_enabled = storage.is_feature_enabled(FEATURE_WEBAPP, default=True)
        cooldown_kb = (
            build_cooldown_keyboard(lang, user_id=user.id, seconds_left=_cooldown_left)
            if webapp_enabled
            else None
        )
        if cooldown_kb is not None:
            logger.info(
                "REPLY cooldown_button chat_id=%s user_id=%s left=%ss",
                chat.id,
                user.id,
                _cooldown_left,
            )
            try:
                await message.reply_text(REWARD_MESSAGE_PLACEHOLDER, reply_markup=cooldown_kb)
            except TelegramError:
                BOT_STATS["errors"] += 1
                logger.exception("SEND_FAIL cooldown_button chat_id=%s user_id=%s", chat.id, user.id)
        logger.info("NO_REWARD cooldown chat_id=%s user_id=%s left=%ss", chat.id, user.id, _cooldown_left)
        return
    logger.info("REWARD_GRANTED chat_id=%s user_id=%s amount=%s total=%s", chat.id, user.id, reward, total)
    BOT_STATS["rewarded"] += 1

    firework_reply_html: str | None = None
    progress_image_bytes: bytes | None = None
    progress_image_caption: str | None = None
    progress_percent = 0
    firework_triggered = False
    if referrals_enabled:
        storage.add_referral_commission(
            referred_user_id=user.id,
            referred_reward_amount=reward,
            chat_id=chat.id,
            message_id=message.message_id,
            percent=REFERRAL_COMMISSION_PERCENT,
        )
    flagged_now, _ = storage.evaluate_user_reliability(
        user_id=user.id,
        threshold_seconds=UNTRUSTED_STREAK_SECONDS,
        max_gap_seconds=UNTRUSTED_MAX_GAP_SECONDS,
    )
    _ = flagged_now

    if chat.type in {"group", "supergroup", "channel"} and fireworks_enabled:
        progress = storage.apply_chat_fireworks_progress(
            chat_id=chat.id,
            chat_type=chat.type,
            chat_title=chat.title or "",
            message_id=message.message_id,
            winners_limit=FIREWORK_WINNERS_LIMIT,
            reward_min=FIREWORK_REWARD_MIN,
            reward_max=FIREWORK_REWARD_MAX,
            max_triggers_per_period=max(1, FIREWORK_PERIOD_MAX),
            base_daily_points=FIREWORK_BASE_DAILY_POINTS,
            max_activity_bonus_points=FIREWORK_ACTIVITY_BONUS_DAILY_POINTS,
            activity_window_hours=max(1, FIREWORK_ACTIVITY_WINDOW_HOURS),
        )
        progress_percent = int(progress.get("progress_percent", 0))
        firework_triggered = bool(progress.get("triggered"))
        if progress["enabled"]:
            if firework_triggered:
                progress_image_bytes = build_firework_progress_image(
                    lang=lang,
                    percent=progress_percent,
                    points=progress["progress_points"],
                    goal=progress["progress_goal"],
                )
                progress_image_caption = tr(
                    lang,
                    "progress_image_caption",
                    percent=progress_percent,
                    points=progress["progress_points"],
                    goal=progress["progress_goal"],
                )
        if progress["triggered"]:
            winners = progress["winners"]
            if winners:
                winner_html_lines = []
                for winner in winners:
                    winner_html_lines.append(
                        f"{winner_label_html(winner)}: +{winner['amount']} TGM coin"
                    )
                firework_reply_html = (
                    tr(lang, "firework_winners_reply") + "\n" + "\n".join(winner_html_lines)
                )
                if referrals_enabled:
                    for winner in winners:
                        storage.add_referral_commission(
                            referred_user_id=winner["user_id"],
                            referred_reward_amount=winner["amount"],
                            chat_id=chat.id,
                            message_id=message.message_id,
                            percent=REFERRAL_COMMISSION_PERCENT,
                        )

        if owner_tribute_enabled:
            owner_user_id = await get_chat_owner_id(context, chat.id)
            if owner_user_id is not None:
                tribute_amount, _ = storage.add_owner_tribute(
                    chat_id=chat.id,
                    owner_user_id=owner_user_id,
                    amount_from_user_reward=reward,
                    message_id=message.message_id,
                )
                if tribute_amount > 0:
                    if referrals_enabled:
                        storage.add_referral_commission(
                            referred_user_id=owner_user_id,
                            referred_reward_amount=tribute_amount,
                            chat_id=chat.id,
                            message_id=message.message_id,
                            percent=REFERRAL_COMMISSION_PERCENT,
                        )

    if super_enabled and can_trigger_super_prize(chat.type):
        created = storage.create_super_prize_task(
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            trigger_chat_id=chat.id,
            trigger_message_id=message.message_id,
        )
        _ = created

    if progress_image_bytes and progress_image_caption:
        try:
            await message.reply_photo(photo=progress_image_bytes, caption=progress_image_caption)
        except TelegramError:
            BOT_STATS["errors"] += 1
            logger.exception("SEND_FAIL progress_image chat_id=%s user_id=%s", chat.id, user.id)

    # Reward UX: show a single button with the reward amount. Telegram requires a message for inline keyboards,
    # so we send an invisible placeholder + button to keep the chat clean.
    reward_keyboard = (
        build_reward_keyboard(lang, user_id=user.id, reward=reward) if webapp_enabled else None
    )
    if reward_keyboard is not None:
        logger.info("REPLY reward_button chat_id=%s user_id=%s", chat.id, user.id)
        try:
            await message.reply_text(REWARD_MESSAGE_PLACEHOLDER, reply_markup=reward_keyboard)
        except TelegramError:
            BOT_STATS["errors"] += 1
            logger.exception("SEND_FAIL reward_button chat_id=%s user_id=%s", chat.id, user.id)
    else:
        logger.info("REPLY reward_text chat_id=%s user_id=%s", chat.id, user.id)
        try:
            await message.reply_text(tr(lang, "reward_short", reward=reward, total=total))
        except TelegramError:
            BOT_STATS["errors"] += 1
            logger.exception("SEND_FAIL reward_text chat_id=%s user_id=%s", chat.id, user.id)

    if firework_reply_html:
        try:
            await message.reply_text(
                firework_reply_html,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except TelegramError:
            BOT_STATS["errors"] += 1
            logger.exception("SEND_FAIL firework_reply chat_id=%s user_id=%s", chat.id, user.id)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return
    await message.reply_text("ok")


async def diag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return
    user = update.effective_user
    chat = update.effective_chat
    now = time.time()
    uptime = int(now - BOT_STARTED_AT)
    lines = [
        f"uptime={uptime}s",
        f"updates={BOT_STATS['updates']}",
        f"rewarded={BOT_STATS['rewarded']}",
        f"cooldown={BOT_STATS['cooldown']}",
        f"errors={BOT_STATS['errors']}",
        f"chat_id={getattr(chat, 'id', None)} type={getattr(chat, 'type', None)}",
        f"user_id={getattr(user, 'id', None)}",
    ]
    # Best-effort rights check (useful when bot is muted/restricted).
    try:
        if chat is not None:
            me = await context.bot.get_chat_member(chat.id, context.bot.id)
            lines.append(f"bot_status={getattr(me, 'status', None)}")
            can_send = getattr(getattr(me, 'privileges', None), 'can_send_messages', None)
            if can_send is not None:
                lines.append(f"bot_can_send={can_send}")
    except TelegramError:
        BOT_STATS["errors"] += 1
        logger.exception("DIAG get_chat_member failed")
    await message.reply_text("\n".join(lines))


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    BOT_STATS["errors"] += 1
    logger.exception("UNHANDLED_ERROR update=%r", update, exc_info=context.error)


def main() -> None:
    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set environment variable TG_BOT_TOKEN")

    storage.init_db()
    tg_app = Application.builder().token(token).build()

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("info", info))
    tg_app.add_handler(CommandHandler("menu", menu))
    tg_app.add_handler(CommandHandler("lang", lang))
    tg_app.add_handler(CommandHandler("send", send))
    tg_app.add_handler(CommandHandler("ref", ref))
    tg_app.add_handler(CommandHandler("app", webapp_command))
    tg_app.add_handler(CommandHandler("ping", ping))
    tg_app.add_handler(CommandHandler("diag", diag))
    tg_app.add_handler(CallbackQueryHandler(set_lang_callback, pattern=r"^set_lang:(ru|en)$"))
    tg_app.add_handler(CallbackQueryHandler(balance_menu_callback, pattern=r"^balance_menu$"))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reward_message))
    tg_app.add_error_handler(on_error)

    logger.info("Bot started")
    tg_app.run_polling()


if __name__ == "__main__":
    main()
