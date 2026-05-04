import html
import json
import os
import time
from math import ceil
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from flask import Flask, jsonify, redirect, request

from storage import FEATURE_BROADCASTS, FEATURE_SECURITY_MONITORING, Storage


LANGUAGE_RU = "ru"
LANGUAGE_EN = "en"
DB_PATH = os.getenv("DB_PATH", "coins.db")
ADMIN_UI_HOST = os.getenv("ADMIN_UI_HOST", "127.0.0.1")
ADMIN_UI_PORT = int(os.getenv("ADMIN_UI_PORT", "8080"))
PAGE_SIZE_DEFAULT = 50
PAGE_SIZE_MAX = 200
FIREWORK_PERIOD_MAX = int(os.getenv("FIREWORK_PERIOD_MAX", os.getenv("FIREWORK_DAILY_MAX", "2")))
BROADCAST_THROTTLE_SECONDS = float(os.getenv("BROADCAST_THROTTLE_SECONDS", "0.05"))
MINIAPP_BOT_USERNAME = os.getenv("MINIAPP_BOT_USERNAME", "tgmcoinbot").strip("@")


app = Flask(__name__)
storage = Storage(DB_PATH)

ADMIN_I18N = {
    LANGUAGE_RU: {
        "title": "TGM Coin Панель",
        "subtitle": "Управление экономикой, ростом и мониторингом проекта.",
        "open_miniapp": "Открыть мини-апп",
        "users_kpi": "Пользователи",
        "chats_kpi": "Чаты в выборке",
        "features_kpi": "Активные фичи",
        "risk_kpi": "Кандидаты риска",
        "jump_users": "Пользователи",
        "jump_broadcast": "Рассылка",
        "jump_chats": "Чаты",
        "jump_monitoring": "Мониторинг",
        "jump_features": "Фичи",
        "help_global": "Подсказка: сначала выбери раздел, затем фильтры и только потом действие.",
        "help_local_filters": "Локальные фильтры работают только по текущей загруженной таблице.",
        "help_toggle": "Переключатели применяются сразу после нажатия кнопки.",
        "users_header": "Пользователи",
        "users_subtitle": "Баланс, надежность, активация и быстрый переход в личку.",
        "help_users": "Используй фильтры, чтобы быстро найти user и управлять доступом к рассылке.",
        "search_user": "поиск по id / username / имени",
        "sort_coins_desc": "монеты: по убыванию",
        "sort_coins_asc": "монеты: по возрастанию",
        "sort_id_desc": "id: по убыванию",
        "sort_id_asc": "id: по возрастанию",
        "sort_updated_desc": "обновление: новые",
        "apply": "Применить",
        "local_filter_page": "быстрый фильтр на текущей странице",
        "trust_all": "надежность: все",
        "trust_trusted": "надежный",
        "trust_untrusted": "ненадежный",
        "activation_all": "активация: все",
        "activation_on": "вкл",
        "activation_off": "выкл",
        "total_users_db": "Всего пользователей в БД: {total}",
        "visible_page": "На странице: {visible} / {total}",
        "col_user_id": "ID",
        "col_username": "Username",
        "col_name": "Имя",
        "col_coins": "Монеты",
        "col_trust": "Надежность",
        "col_activated": "Активация",
        "col_activated_at": "Активирован",
        "col_updated": "Обновлен",
        "col_dm": "ЛС",
        "col_action": "Действие",
        "open": "Открыть",
        "disable": "Выключить",
        "enable": "Включить",
        "no_users": "Нет пользователей",
        "prev": "Назад",
        "next": "Вперед",
        "page": "Страница {page} / {total}",
        "broadcast_header": "Рассылка",
        "broadcast_subtitle": "Массовая рассылка в личку. Токен бота: {token}.",
        "help_broadcast": "Пиши коротко и по делу: рассылка уходит всем выбранным пользователям.",
        "token_configured": "настроен",
        "token_missing": "не задан",
        "message_text": "Текст сообщения для пользователей",
        "activated_only": "только активированные",
        "active_users_page": "Активных на странице: {count}",
        "send_broadcast": "Отправить рассылку",
        "local_filter_mode": "быстрый фильтр по тексту / режиму",
        "mode_all": "режим: все",
        "mode_activated": "активированные",
        "mode_everyone": "все",
        "visible_short": "Видно: {visible} / {total}",
        "token_chip": "Токен",
        "col_text": "Текст",
        "col_mode": "Режим",
        "col_sent": "Отправлено",
        "col_failed": "Ошибки",
        "col_created": "Создано",
        "no_broadcasts": "Рассылок пока нет",
        "chats_header": "Чаты и фейерверки",
        "chats_subtitle": "Включение/выключение фейерверка и прогресс по чатам.",
        "help_chats": "Если чат не появился, сначала отправь туда сообщения через бота.",
        "search_chat": "поиск по chat id / title / type",
        "find_chat": "Найти чат",
        "local_filter_chats": "быстрый фильтр по загруженным чатам",
        "firework_all": "фейерверк: все",
        "visible_chats": "Чатов видно: {visible} / {total}",
        "col_chat_id": "Chat ID",
        "col_title": "Название",
        "col_type": "Тип",
        "col_firework": "Фейерверк",
        "col_progress": "Прогресс",
        "col_period": "Период",
        "col_count": "Счетчик",
        "no_chats": "Чатов пока нет. Бот должен получить сообщения.",
        "monitoring_header": "Мониторинг",
        "monitoring_on": "Мониторинг безопасности включен.",
        "monitoring_off": "Мониторинг безопасности выключен (feature flag security_monitoring).",
        "help_monitoring": "Смотри всплески дохода и слива, затем проверяй пользователей из risk-списка.",
        "monitor_apply": "Применить фильтры мониторинга",
        "placeholder_days": "дни",
        "placeholder_income": "мин доход",
        "placeholder_out": "мин слив",
        "placeholder_limit": "лимит",
        "timeline_title": "График дохода и сливов",
        "timeline_note": "Период: последние {days} дней.",
        "top_income_chart_title": "Распределение топ-дохода",
        "top_income_chart_note": "Топ-12 пользователей в текущем окне.",
        "top_income_title": "Топ дохода (за {days} дней)",
        "suspicious_title": "Подозрительные пользователи",
        "suspicious_rule": "Правило: доход >= {income} или слив >= {out} за {days} дней.",
        "local_filter_risk": "быстрый фильтр подозрительного списка",
        "col_income": "Доход",
        "col_transfer_out": "Слив",
        "col_events": "События",
        "no_income": "Нет данных по доходам",
        "no_suspicious": "Нет подозрительных пользователей по текущему правилу",
        "features_header": "Feature Flags",
        "features_subtitle": "Поэтапный релиз и эксперименты.",
        "help_features": "Включай функции поэтапно: сначала тестовый чат, затем общий rollout.",
        "local_filter_features": "быстрый фильтр по key / описанию",
        "feature_status_all": "статус: все",
        "col_key": "Ключ",
        "col_description": "Описание",
        "col_status": "Статус",
        "no_features": "Нет feature flags",
        "status_on": "вкл",
        "status_off": "выкл",
        "status_trusted": "надежный",
        "status_untrusted": "ненадежный",
        "lang_ru": "RU",
        "lang_en": "EN",
        "visible_js": "Видно",
        "no_data_js": "Нет данных",
        "tt_search": "Поиск по текущему разделу",
        "tt_sort": "Сортировка списка",
        "tt_page_size": "Количество строк на странице",
        "tt_apply": "Применить фильтры",
        "tt_local_search": "Локальный фильтр по уже загруженным строкам",
        "tt_status_filter": "Фильтр по статусу",
        "tt_open_dm": "Открыть личный чат с пользователем",
        "tt_toggle_user": "Вкл/выкл участие пользователя в рассылках",
        "tt_toggle_chat": "Вкл/выкл фейерверк для чата",
        "tt_toggle_feature": "Вкл/выкл конкретную фичу",
        "tt_send_broadcast": "Отправить рассылку выбранной аудитории",
        "tt_monitor_apply": "Применить мониторинговые пороги",
        "tt_monitor_input": "Пороговые значения мониторинга",
        "notice_invalid_user_id": "Некорректный user id",
        "notice_broadcast_user": "Рассылка для пользователя {user_id}: {status}",
        "notice_enabled": "включена",
        "notice_disabled": "выключена",
        "notice_broadcast_empty": "Текст рассылки пустой",
        "notice_feature_disabled": "Фича 'broadcasts' выключена",
        "notice_missing_token": "Укажи TG_BOT_TOKEN для рассылки",
        "notice_broadcast_done": "Рассылка завершена. Целей={targets} Отправлено={sent} Ошибок={failed}",
    },
    LANGUAGE_EN: {
        "title": "TGM Coin Control Center",
        "subtitle": "Manage economy, growth and monitoring workflows.",
        "open_miniapp": "Open mini app",
        "users_kpi": "Users",
        "chats_kpi": "Chats in view",
        "features_kpi": "Enabled features",
        "risk_kpi": "Risk candidates",
        "jump_users": "Users",
        "jump_broadcast": "Broadcast",
        "jump_chats": "Chats",
        "jump_monitoring": "Monitoring",
        "jump_features": "Features",
        "help_global": "Tip: choose a section first, then filters, then actions.",
        "help_local_filters": "Local filters work only on the currently loaded table rows.",
        "help_toggle": "Toggle actions are applied immediately after click.",
        "users_header": "User Directory",
        "users_subtitle": "Balance, trust, activation and quick DM access.",
        "help_users": "Use filters to quickly find a user and control broadcast access.",
        "search_user": "search by id / username / name",
        "sort_coins_desc": "coins desc",
        "sort_coins_asc": "coins asc",
        "sort_id_desc": "id desc",
        "sort_id_asc": "id asc",
        "sort_updated_desc": "updated desc",
        "apply": "Apply",
        "local_filter_page": "local filter on current page",
        "trust_all": "trust: all",
        "trust_trusted": "trusted",
        "trust_untrusted": "untrusted",
        "activation_all": "activation: all",
        "activation_on": "on",
        "activation_off": "off",
        "total_users_db": "Total users in DB: {total}",
        "visible_page": "Visible on page: {visible} / {total}",
        "col_user_id": "User ID",
        "col_username": "Username",
        "col_name": "Name",
        "col_coins": "Coins",
        "col_trust": "Trust",
        "col_activated": "Activated",
        "col_activated_at": "Activated At",
        "col_updated": "Updated",
        "col_dm": "DM",
        "col_action": "Action",
        "open": "Open",
        "disable": "Disable",
        "enable": "Enable",
        "no_users": "No users",
        "prev": "Prev",
        "next": "Next",
        "page": "Page {page} / {total}",
        "broadcast_header": "Broadcast",
        "broadcast_subtitle": "Mass DM broadcast. Bot token: {token}.",
        "help_broadcast": "Keep messages short and clear: broadcast is sent to all selected users.",
        "token_configured": "configured",
        "token_missing": "missing",
        "message_text": "Message text for users",
        "activated_only": "activated users only",
        "active_users_page": "Active on page: {count}",
        "send_broadcast": "Send broadcast",
        "local_filter_mode": "local filter by text / mode",
        "mode_all": "mode: all",
        "mode_activated": "activated",
        "mode_everyone": "all",
        "visible_short": "Visible: {visible} / {total}",
        "token_chip": "Token",
        "col_text": "Text",
        "col_mode": "Mode",
        "col_sent": "Sent",
        "col_failed": "Failed",
        "col_created": "Created",
        "no_broadcasts": "No broadcasts yet",
        "chats_header": "Chat Fireworks",
        "chats_subtitle": "Enable/disable fireworks and inspect progress.",
        "help_chats": "If a chat is missing here, send messages there via bot first.",
        "search_chat": "search by chat id / title / type",
        "find_chat": "Find chat",
        "local_filter_chats": "local filter on loaded chats",
        "firework_all": "firework: all",
        "visible_chats": "Visible chats: {visible} / {total}",
        "col_chat_id": "Chat ID",
        "col_title": "Title",
        "col_type": "Type",
        "col_firework": "Firework",
        "col_progress": "Progress",
        "col_period": "Period",
        "col_count": "Count",
        "no_chats": "No chats yet. Bot must receive messages first.",
        "monitoring_header": "Monitoring",
        "monitoring_on": "Security monitoring is ON.",
        "monitoring_off": "Security monitoring is OFF (feature flag security_monitoring).",
        "help_monitoring": "Track income/transfer spikes and investigate users from risk list.",
        "monitor_apply": "Apply monitoring filters",
        "placeholder_days": "days",
        "placeholder_income": "min income",
        "placeholder_out": "min transfer out",
        "placeholder_limit": "limit",
        "timeline_title": "Income vs transfer-out timeline",
        "timeline_note": "Range: last {days} days.",
        "top_income_chart_title": "Top income distribution",
        "top_income_chart_note": "Top 12 users in current window.",
        "top_income_title": "Top income (last {days} days)",
        "suspicious_title": "Suspicious users",
        "suspicious_rule": "Rule: income >= {income} or transfer_out >= {out} for last {days} days.",
        "local_filter_risk": "local filter suspicious list",
        "col_income": "Income",
        "col_transfer_out": "Transfer out",
        "col_events": "Events",
        "no_income": "No income data",
        "no_suspicious": "No suspicious users by current rule",
        "features_header": "Feature Flags",
        "features_subtitle": "Staged rollouts and experiments.",
        "help_features": "Enable features in stages: test chat first, then full rollout.",
        "local_filter_features": "local filter by key / description",
        "feature_status_all": "status: all",
        "col_key": "Key",
        "col_description": "Description",
        "col_status": "Status",
        "no_features": "No feature flags",
        "status_on": "on",
        "status_off": "off",
        "status_trusted": "trusted",
        "status_untrusted": "untrusted",
        "lang_ru": "RU",
        "lang_en": "EN",
        "visible_js": "Visible",
        "no_data_js": "No data",
        "tt_search": "Search in current section",
        "tt_sort": "Sort current list",
        "tt_page_size": "Rows per page",
        "tt_apply": "Apply filters",
        "tt_local_search": "Filter already loaded rows",
        "tt_status_filter": "Filter by status",
        "tt_open_dm": "Open direct chat with user",
        "tt_toggle_user": "Enable/disable user in broadcasts",
        "tt_toggle_chat": "Enable/disable fireworks for this chat",
        "tt_toggle_feature": "Enable/disable this feature",
        "tt_send_broadcast": "Send broadcast to selected audience",
        "tt_monitor_apply": "Apply monitoring thresholds",
        "tt_monitor_input": "Monitoring threshold values",
        "notice_invalid_user_id": "Invalid user id",
        "notice_broadcast_user": "Broadcast for user {user_id}: {status}",
        "notice_enabled": "enabled",
        "notice_disabled": "disabled",
        "notice_broadcast_empty": "Broadcast text is empty",
        "notice_feature_disabled": "Feature 'broadcasts' is disabled",
        "notice_missing_token": "Set TG_BOT_TOKEN to send broadcasts",
        "notice_broadcast_done": "Broadcast done. Targets={targets} Sent={sent} Failed={failed}",
    },
}

ROADMAP_ITEMS = [
    {
        "phase": "MVP",
        "title_ru": "База экономики и чатов",
        "title_en": "Core economy and chats",
        "status": "done",
        "description_ru": "Награды 1-10, супер-приз, cooldown, фейерверк, 10% владельцу.",
        "description_en": "Rewards 1-10, super prize, cooldown, fireworks, 10% owner tribute.",
    },
    {
        "phase": "Phase 1",
        "title_ru": "Рост и удержание",
        "title_en": "Growth and retention",
        "status": "in_progress",
        "description_ru": "Рефералка, переводы, рассылки, мини-апп рейтинг и меню.",
        "description_en": "Referrals, transfers, broadcasts, mini-app leaderboard and menu.",
    },
    {
        "phase": "Phase 2",
        "title_ru": "Бусты и монетизация",
        "title_en": "Boosts and monetization",
        "status": "planned",
        "description_ru": "Бесплатные/платные бусты, включение по этапам, контроль из админки.",
        "description_en": "Free/paid boosts, phased rollouts, admin control toggles.",
    },
    {
        "phase": "Phase 3",
        "title_ru": "Антифрод и мониторинг",
        "title_en": "Anti-fraud and monitoring",
        "status": "planned",
        "description_ru": "Триггеры резких скачков, тревоги админу, списки риска и модерация.",
        "description_en": "Spike triggers, admin alerts, risk lists and moderation.",
    },
    {
        "phase": "Phase 4",
        "title_ru": "Магазин и партнерки",
        "title_en": "Shop and partnerships",
        "status": "planned",
        "description_ru": "Магазин за монеты, партнерка, расширенные кампании и квесты.",
        "description_en": "Coin shop, partnerships, advanced campaigns and quests.",
    },
    {
        "phase": "Phase 5",
        "title_ru": "NFT и кошельки",
        "title_en": "NFT and wallets",
        "status": "planned",
        "description_ru": "NFT-мультипликаторы 2x/5x/10x, вывод монет в кошельки после аудита.",
        "description_en": "NFT multipliers 2x/5x/10x, wallet withdrawals after security audit.",
    },
]


def to_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_lang(value: Optional[str]) -> str:
    code = (value or "").strip().lower()
    if code not in {LANGUAGE_RU, LANGUAGE_EN}:
        return LANGUAGE_RU
    return code


def admin_text(lang: str, key: str, **kwargs) -> str:
    safe_lang = normalize_lang(lang)
    template = ADMIN_I18N.get(safe_lang, ADMIN_I18N[LANGUAGE_RU]).get(
        key, ADMIN_I18N[LANGUAGE_EN].get(key, key)
    )
    return template.format(**kwargs)


def lang_from_next(next_url: str, fallback: str = LANGUAGE_RU) -> str:
    split = urlsplit(next_url or "")
    query = dict(parse_qsl(split.query, keep_blank_values=True))
    return normalize_lang(query.get("lang", fallback))


def safe_next_url(raw_next: str) -> str:
    if raw_next and raw_next.startswith("/"):
        return raw_next
    return "/"


def page_url(
    page: int,
    page_size: int,
    q: str,
    sort: str,
    chat_q: str,
    lang: str,
    monitor_days: int,
    monitor_min_income: int,
    monitor_min_transfer_out: int,
    monitor_limit: int,
) -> str:
    return "/?" + urlencode(
        {
            "page": page,
            "page_size": page_size,
            "q": q,
            "sort": sort,
            "chat_q": chat_q,
            "lang": lang,
            "monitor_days": monitor_days,
            "monitor_min_income": monitor_min_income,
            "monitor_min_transfer_out": monitor_min_transfer_out,
            "monitor_limit": monitor_limit,
        },
        doseq=False,
    )


def append_notice(next_url: str, notice: str) -> str:
    next_url = safe_next_url(next_url)
    if not notice:
        return next_url
    split = urlsplit(next_url)
    query = dict(parse_qsl(split.query, keep_blank_values=True))
    query["notice"] = notice
    query_string = urlencode(query, doseq=False)
    return urlunsplit((split.scheme, split.netloc, split.path, query_string, split.fragment))


def period_label(code: str) -> str:
    mapping = {
        "night": "night",
        "morning": "morning",
        "day": "day",
        "evening": "evening",
    }
    return mapping.get(code, "-")


def user_label(user_id: int, username: str, first_name: str) -> str:
    if username:
        return f"@{username}"
    if first_name:
        return first_name
    return f"id:{user_id}"


def send_telegram_text(token: str, chat_id: int, text: str) -> tuple[bool, str]:
    payload = urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "1",
        }
    ).encode("utf-8")
    req = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urlopen(req, timeout=12) as response:
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        try:
            details = exc.read().decode("utf-8", errors="replace")
        except Exception:
            details = str(exc)
        return False, f"HTTP {exc.code}: {details[:250]}"
    except URLError as exc:
        return False, f"URL error: {exc.reason}"
    except Exception as exc:
        return False, str(exc)

    try:
        payload_json = json.loads(body)
    except json.JSONDecodeError:
        return False, "Invalid Telegram API response"

    if isinstance(payload_json, dict) and payload_json.get("ok"):
        return True, ""
    if isinstance(payload_json, dict):
        return False, str(payload_json.get("description") or "Telegram API error")
    return False, "Unknown Telegram API response"


@app.get("/")
def index():
    ui_lang = normalize_lang(request.args.get("lang"))

    def lt(key: str, **kwargs) -> str:
        return admin_text(ui_lang, key, **kwargs)

    q = request.args.get("q", "").strip()
    q_html = html.escape(q)
    chat_q = request.args.get("chat_q", "").strip()
    chat_q_html = html.escape(chat_q)
    sort = request.args.get("sort", "coins_desc")
    page = max(1, to_int(request.args.get("page", "1"), 1))
    page_size = to_int(request.args.get("page_size", str(PAGE_SIZE_DEFAULT)), PAGE_SIZE_DEFAULT)
    page_size = min(max(page_size, 1), PAGE_SIZE_MAX)
    monitor_days = min(max(to_int(request.args.get("monitor_days", "5"), 5), 1), 30)
    monitor_min_income = max(to_int(request.args.get("monitor_min_income", "5000"), 5000), 1)
    monitor_min_transfer_out = max(
        to_int(request.args.get("monitor_min_transfer_out", "3000"), 3000), 1
    )
    monitor_limit = min(max(to_int(request.args.get("monitor_limit", "100"), 100), 1), 500)

    lang_ru_args = request.args.to_dict(flat=True)
    lang_en_args = request.args.to_dict(flat=True)
    lang_ru_args["lang"] = LANGUAGE_RU
    lang_en_args["lang"] = LANGUAGE_EN
    lang_ru_url = "/?" + urlencode(lang_ru_args, doseq=False)
    lang_en_url = "/?" + urlencode(lang_en_args, doseq=False)

    total = storage.count_users(search=q)
    total_pages = max(1, ceil(total / page_size)) if total else 1
    page = min(page, total_pages)
    offset = (page - 1) * page_size
    users = storage.list_users(limit=page_size, offset=offset, search=q, sort=sort)
    chats = storage.list_chats(limit=200, offset=0, search=chat_q)
    features = storage.list_feature_flags()
    broadcasts = storage.list_broadcast_logs(limit=20)
    monitoring_enabled = storage.is_feature_enabled(FEATURE_SECURITY_MONITORING, default=True)
    top_income_5d = (
        storage.top_income_last_days(days=monitor_days, limit=min(monitor_limit, 100))
        if monitoring_enabled
        else []
    )
    suspicious_rows = (
        storage.suspicious_users_report(
            days=monitor_days,
            min_income=monitor_min_income,
            min_transfer_out=monitor_min_transfer_out,
            limit=monitor_limit,
        )
        if monitoring_enabled
        else []
    )
    income_timeline = storage.income_timeline(days=monitor_days) if monitoring_enabled else []

    return_url = page_url(
        page,
        page_size,
        q,
        sort,
        chat_q,
        ui_lang,
        monitor_days,
        monitor_min_income,
        monitor_min_transfer_out,
        monitor_limit,
    )
    return_url_safe = html.escape(return_url, quote=True)
    notice = html.escape(request.args.get("notice", "").strip())

    rows_html = []
    for user in users:
        username = user["username"]
        dm_link = f"https://t.me/{username}" if username else f"tg://user?id={user['user_id']}"
        dm_link_safe = html.escape(dm_link, quote=True)
        username_cell = html.escape(f"@{username}" if username else "-")
        first_name_cell = html.escape(user["first_name"] or "-")
        updated_cell = html.escape(user["updated_at"])
        activated_at_cell = html.escape(user.get("activated_at") or "-")
        next_enabled = "0" if user.get("broadcast_enabled") else "1"
        button_text = lt("disable") if user.get("broadcast_enabled") else lt("enable")
        trust_key = "trusted" if user["is_trusted"] else "untrusted"
        activation_key = "on" if user.get("broadcast_enabled") else "off"
        local_search = html.escape(
            f"{user['user_id']} {username or ''} {user['first_name'] or ''}".lower(), quote=True
        )
        trust_badge = (
            f"<span class='badge badge-good'>{html.escape(lt('status_trusted'))}</span>"
            if user["is_trusted"]
            else f"<span class='badge badge-danger'>{html.escape(lt('status_untrusted'))}</span>"
        )
        activated_badge = (
            f"<span class='badge badge-good'>{html.escape(lt('status_on'))}</span>"
            if user.get("broadcast_enabled")
            else f"<span class='badge badge-muted'>{html.escape(lt('status_off'))}</span>"
        )

        rows_html.append(
            "<tr class='user-row'"
            f" data-trust='{trust_key}' data-activated='{activation_key}' data-search='{local_search}'>"
            f"<td>{user['user_id']}</td>"
            f"<td>{username_cell}</td>"
            f"<td>{first_name_cell}</td>"
            f"<td>{user['coins']}</td>"
            f"<td>{trust_badge}</td>"
            f"<td>{activated_badge}</td>"
            f"<td>{activated_at_cell}</td>"
            f"<td>{updated_cell}</td>"
            f"<td><a href='{dm_link_safe}' target='_blank' title='{html.escape(lt('tt_open_dm'), quote=True)}'>{html.escape(lt('open'))}</a></td>"
            "<td>"
            "<form method='post' action='/user-activation' class='inline-form'>"
            f"<input type='hidden' name='user_id' value='{user['user_id']}' />"
            f"<input type='hidden' name='enabled' value='{next_enabled}' />"
            f"<input type='hidden' name='next' value='{return_url_safe}' />"
            f"<input type='hidden' name='lang' value='{ui_lang}' />"
            f"<button type='submit' title='{html.escape(lt('tt_toggle_user'), quote=True)}'>{button_text}</button>"
            "</form>"
            "</td>"
            "</tr>"
        )

    prev_link = (
        f"<a href='{page_url(page - 1, page_size, q, sort, chat_q, ui_lang, monitor_days, monitor_min_income, monitor_min_transfer_out, monitor_limit)}'>{lt('prev')}</a>"
        if page > 1
        else lt("prev")
    )
    next_link = (
        f"<a href='{page_url(page + 1, page_size, q, sort, chat_q, ui_lang, monitor_days, monitor_min_income, monitor_min_transfer_out, monitor_limit)}'>{lt('next')}</a>"
        if page < total_pages
        else lt("next")
    )

    chat_rows_html = []
    for chat in chats:
        title_cell = html.escape(chat["chat_title"] or "-")
        type_cell = html.escape(chat["chat_type"] or "-")
        progress_cell = f"{chat['progress_percent']}% ({chat['progress_points']}/{chat['progress_goal']})"
        period_cell = f"{chat['fireworks_period_count']}/{FIREWORK_PERIOD_MAX}"
        period_name_cell = period_label(chat.get("fireworks_period_code", ""))
        next_enabled = "0" if chat["fireworks_enabled"] else "1"
        button_text = lt("disable") if chat["fireworks_enabled"] else lt("enable")
        fireworks_key = "on" if chat["fireworks_enabled"] else "off"
        chat_search = html.escape(
            f"{chat['chat_id']} {chat['chat_title'] or ''} {chat['chat_type'] or ''}".lower(), quote=True
        )
        firework_badge = (
            f"<span class='badge badge-good'>{html.escape(lt('status_on'))}</span>"
            if chat["fireworks_enabled"]
            else f"<span class='badge badge-muted'>{html.escape(lt('status_off'))}</span>"
        )

        chat_rows_html.append(
            "<tr class='chat-row'"
            f" data-firework='{fireworks_key}' data-search='{chat_search}'>"
            f"<td>{chat['chat_id']}</td>"
            f"<td>{title_cell}</td>"
            f"<td>{type_cell}</td>"
            f"<td>{firework_badge}</td>"
            f"<td>{progress_cell}</td>"
            f"<td>{period_name_cell}</td>"
            f"<td>{period_cell}</td>"
            f"<td>{html.escape(chat['updated_at'])}</td>"
            "<td>"
            "<form method='post' action='/chat-fireworks' class='inline-form'>"
            f"<input type='hidden' name='chat_id' value='{chat['chat_id']}' />"
            f"<input type='hidden' name='enabled' value='{next_enabled}' />"
            f"<input type='hidden' name='next' value='{return_url_safe}' />"
            f"<input type='hidden' name='lang' value='{ui_lang}' />"
            f"<button type='submit' title='{html.escape(lt('tt_toggle_chat'), quote=True)}'>{button_text}</button>"
            "</form>"
            "</td>"
            "</tr>"
        )

    feature_rows_html = []
    for feature in features:
        key_cell = html.escape(feature["key"])
        desc_cell = html.escape(feature["description"] or "-")
        next_enabled = "0" if feature["enabled"] else "1"
        button_text = lt("disable") if feature["enabled"] else lt("enable")
        enabled_key = "on" if feature["enabled"] else "off"
        feature_search = html.escape(
            f"{feature['key']} {feature['description'] or ''}".lower(), quote=True
        )
        feature_badge = (
            f"<span class='badge badge-good'>{html.escape(lt('status_on'))}</span>"
            if feature["enabled"]
            else f"<span class='badge badge-muted'>{html.escape(lt('status_off'))}</span>"
        )
        feature_rows_html.append(
            "<tr class='feature-row'"
            f" data-enabled='{enabled_key}' data-search='{feature_search}'>"
            f"<td>{key_cell}</td>"
            f"<td>{desc_cell}</td>"
            f"<td>{feature_badge}</td>"
            f"<td>{html.escape(feature['updated_at'])}</td>"
            "<td>"
            "<form method='post' action='/feature-flag' class='inline-form'>"
            f"<input type='hidden' name='key' value='{key_cell}' />"
            f"<input type='hidden' name='enabled' value='{next_enabled}' />"
            f"<input type='hidden' name='next' value='{return_url_safe}' />"
            f"<input type='hidden' name='lang' value='{ui_lang}' />"
            f"<button type='submit' title='{html.escape(lt('tt_toggle_feature'), quote=True)}'>{button_text}</button>"
            "</form>"
            "</td>"
            "</tr>"
        )

    broadcast_rows_html = []
    for row in broadcasts:
        text_preview = html.escape((row["text"] or "").replace("\n", " ")[:80])
        if len(row["text"] or "") > 80:
            text_preview += "..."
        mode = "activated" if row["activated_only"] else "all"
        mode_label = lt("mode_activated") if row["activated_only"] else lt("mode_everyone")
        row_search = html.escape(f"{mode} {mode_label} {row['text'] or ''}".lower(), quote=True)
        broadcast_rows_html.append(
            "<tr class='broadcast-row'"
            f" data-mode='{mode}' data-search='{row_search}'>"
            f"<td>{row['id']}</td>"
            f"<td>{text_preview}</td>"
            f"<td><span class='badge badge-muted'>{html.escape(mode_label)}</span></td>"
            f"<td>{row['sent_count']}</td>"
            f"<td>{row['failed_count']}</td>"
            f"<td>{html.escape(row['created_at'])}</td>"
            "</tr>"
        )

    token_present = bool(os.getenv("TG_BOT_TOKEN", "").strip())
    token_status_text = lt("token_configured") if token_present else lt("token_missing")
    monitoring_status_text = (
        lt("monitoring_on")
        if monitoring_enabled
        else lt("monitoring_off")
    )

    income_rows_html = []
    for item in top_income_5d:
        income_search = html.escape(
            f"{item['user_id']} {item['username'] or ''} {item['first_name'] or ''}".lower(),
            quote=True,
        )
        income_rows_html.append(
            "<tr class='income-row'"
            f" data-search='{income_search}'>"
            f"<td>{item['user_id']}</td>"
            f"<td>{html.escape(user_label(item['user_id'], item['username'], item['first_name']))}</td>"
            f"<td>{item['income_total']}</td>"
            f"<td>{item['transfer_out_total']}</td>"
            "</tr>"
        )

    suspicious_rows_html = []
    for item in suspicious_rows:
        risk_search = html.escape(
            f"{item['user_id']} {item['username'] or ''} {item['first_name'] or ''}".lower(), quote=True
        )
        suspicious_rows_html.append(
            "<tr class='risk-row'"
            f" data-search='{risk_search}'>"
            f"<td>{item['user_id']}</td>"
            f"<td>{html.escape(user_label(item['user_id'], item['username'], item['first_name']))}</td>"
            f"<td>{item['income_total']}</td>"
            f"<td>{item['transfer_out_total']}</td>"
            f"<td>{item['events_count']}</td>"
            "</tr>"
        )

    chats_total = len(chats)
    features_enabled_total = sum(1 for item in features if item["enabled"])
    suspicious_total = len(suspicious_rows)
    active_on_page = sum(1 for item in users if item.get("broadcast_enabled"))
    timeline_labels = [item["day"][5:] for item in income_timeline]
    timeline_income_values = [item["income_total"] for item in income_timeline]
    timeline_transfer_values = [item["transfer_out_total"] for item in income_timeline]
    timeline_max_value = max([1, *timeline_income_values, *timeline_transfer_values])

    income_chart_items: list[dict[str, Any]] = []
    for item in top_income_5d[:12]:
        income_chart_items.append(
            {
                "label": user_label(item["user_id"], item["username"], item["first_name"]),
                "income": int(item["income_total"]),
                "transfer": int(item["transfer_out_total"]),
            }
        )

    timeline_data_json = json.dumps(
        {
            "labels": timeline_labels,
            "income": timeline_income_values,
            "transfer": timeline_transfer_values,
            "max_value": timeline_max_value,
        }
    )
    income_chart_data_json = json.dumps(income_chart_items)

    return f"""
<!doctype html>
<html lang="{ui_lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{html.escape(lt("title"))}</title>
  <style>
    :root {{
      --bg: #f5f5f7;
      --surface: rgba(255, 255, 255, 0.86);
      --surface-solid: #ffffff;
      --line: #e5e7eb;
      --line-soft: #eef0f3;
      --text: #111827;
      --muted: #6b7280;
      --accent: #0a84ff;
      --accent-soft: #e7f2ff;
      --good: #16a34a;
      --warn: #d97706;
      --danger: #dc2626;
      --radius-xl: 24px;
      --radius-lg: 18px;
      --radius-md: 12px;
      --shadow: 0 20px 42px rgba(15, 23, 42, 0.08);
    }}
    * {{
      box-sizing: border-box;
    }}
    html {{
      scroll-behavior: smooth;
    }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 12% 12%, #e9f3ff 0%, transparent 36%),
        radial-gradient(circle at 88% -8%, #eef8f0 0%, transparent 30%),
        var(--bg);
    }}
    .fade-up {{
      animation: fade-up 0.35s ease both;
    }}
    @keyframes fade-up {{
      from {{
        opacity: 0;
        transform: translateY(10px);
      }}
      to {{
        opacity: 1;
        transform: translateY(0);
      }}
    }}
    a {{
      color: #0a6ce4;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .shell {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 26px 18px 40px;
    }}
    .hero {{
      background: var(--surface);
      border: 1px solid rgba(255, 255, 255, 0.7);
      border-radius: var(--radius-xl);
      padding: 20px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
      margin-bottom: 16px;
    }}
    .hero-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      flex-wrap: wrap;
    }}
    .hero h1 {{
      margin: 0;
      font-size: 30px;
      letter-spacing: -0.02em;
      line-height: 1.1;
    }}
    .hero p {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 14px;
    }}
    .quick-link {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: var(--surface-solid);
      font-weight: 600;
      color: #111827;
      white-space: nowrap;
    }}
    .kpis {{
      margin-top: 16px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .kpi {{
      background: var(--surface-solid);
      border: 1px solid var(--line-soft);
      border-radius: 14px;
      padding: 12px 13px;
    }}
    .kpi-label {{
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }}
    .kpi-value {{
      font-size: 22px;
      font-weight: 700;
      letter-spacing: -0.02em;
      line-height: 1;
    }}
    .kpi-value.danger {{
      color: var(--danger);
    }}
    .notice {{
      margin: 0 0 16px;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid #bae6fd;
      background: #effbff;
      color: #0e7490;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.72);
    }}
    .jumpbar {{
      margin: 0 0 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      position: sticky;
      top: 6px;
      z-index: 8;
      padding: 8px;
      border-radius: 14px;
      background: rgba(245, 245, 247, 0.78);
      border: 1px solid rgba(255, 255, 255, 0.78);
      backdrop-filter: blur(8px);
    }}
    .help-strip {{
      margin: -2px 0 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .help-pill {{
      font-size: 12px;
      color: #334155;
      background: #f8fbff;
      border: 1px solid #dbeafe;
      border-radius: 999px;
      padding: 6px 10px;
    }}
    .jump-link {{
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: var(--surface-solid);
      color: #0f172a;
      font-size: 13px;
      font-weight: 600;
      transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .jump-link:hover {{
      text-decoration: none;
      border-color: #c5ceda;
      transform: translateY(-1px);
    }}
    .jump-link.active {{
      border-color: #93c5fd;
      background: #eaf3ff;
      color: #0b4a8d;
    }}
	    .panel {{
	      margin-bottom: 14px;
	      background: var(--surface);
	      border: 1px solid rgba(255, 255, 255, 0.7);
	      border-radius: var(--radius-lg);
	      box-shadow: var(--shadow);
	      backdrop-filter: blur(8px);
	      overflow: hidden;
	      transition: transform 0.18s ease, box-shadow 0.18s ease;
	    }}
	    details.panel > summary {{
	      list-style: none;
	      cursor: pointer;
	      user-select: none;
	    }}
	    details.panel > summary::-webkit-details-marker {{
	      display: none;
	    }}
	    .panel-chev {{
	      width: 28px;
	      height: 28px;
	      display: inline-flex;
	      align-items: center;
	      justify-content: center;
	      color: var(--muted);
	      flex: 0 0 auto;
	      margin-top: 2px;
	    }}
	    .panel-chev::before {{
	      content: "▾";
	      font-size: 18px;
	      line-height: 1;
	      transition: transform 0.18s ease;
	    }}
	    details.panel[open] > summary .panel-chev::before {{
	      transform: rotate(180deg);
	    }}
    .panel:hover {{
      transform: translateY(-2px);
      box-shadow: 0 22px 46px rgba(15, 23, 42, 0.1);
    }}
    .panel-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      padding: 16px 16px 10px;
    }}
    .panel-head h2 {{
      margin: 0;
      font-size: 19px;
      letter-spacing: -0.015em;
    }}
    .panel-head p {{
      margin: 5px 0 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .section-help {{
      margin-top: 8px !important;
      color: #334155 !important;
      font-size: 12px !important;
      line-height: 1.35;
      background: #f8fbff;
      border: 1px solid #dbeafe;
      border-radius: 10px;
      display: inline-block;
      padding: 5px 9px;
    }}
    .panel-content {{
      padding: 0 16px 16px;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-bottom: 12px;
    }}
    textarea,
    input,
    select,
    button {{
      border: 1px solid #d7dce3;
      border-radius: 10px;
      padding: 8px 11px;
      font-size: 14px;
      line-height: 1.3;
      background: #fff;
      color: var(--text);
      transition: border-color 0.16s ease, box-shadow 0.16s ease;
    }}
    textarea:focus,
    input:focus,
    select:focus {{
      outline: none;
      border-color: #93c5fd;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.14);
    }}
    textarea {{
      width: 100%;
      min-height: 112px;
      resize: vertical;
    }}
    button {{
      cursor: pointer;
      font-weight: 600;
      background: #fff;
    }}
    button:hover {{
      border-color: #b4bdca;
      background: #fafafa;
    }}
    .btn-primary {{
      border-color: #0b0b0f;
      background: #111827;
      color: #fff;
    }}
    .btn-primary:hover {{
      background: #1f2937;
      border-color: #1f2937;
    }}
    .check-line {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: #374151;
      font-size: 13px;
      margin-right: auto;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #fff;
      font-size: 12px;
      color: #374151;
    }}
    .dim {{
      color: var(--muted);
      font-size: 13px;
    }}
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border: 1px solid transparent;
    }}
    .badge-good {{
      color: #166534;
      background: #dcfce7;
      border-color: #bbf7d0;
    }}
    .badge-danger {{
      color: #991b1b;
      background: #fee2e2;
      border-color: #fecaca;
    }}
    .badge-muted {{
      color: #374151;
      background: #f3f4f6;
      border-color: #e5e7eb;
    }}
    .table-wrap {{
      width: 100%;
      overflow: auto;
      border: 1px solid var(--line-soft);
      border-radius: 13px;
      background: #fff;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th,
    td {{
      border-bottom: 1px solid var(--line-soft);
      text-align: left;
      padding: 10px 8px;
      white-space: nowrap;
      vertical-align: middle;
    }}
    th {{
      position: sticky;
      top: 0;
      z-index: 1;
      background: #f8f9fb;
      color: #374151;
      font-weight: 600;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    tr:last-child td {{
      border-bottom: 0;
    }}
    .pager {{
      margin-top: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px 14px;
      align-items: center;
      color: var(--muted);
      font-size: 13px;
    }}
    .table-info {{
      margin: -2px 0 10px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 12px;
    }}
    .toolbar-compact {{
      margin: -2px 0 10px;
      gap: 8px;
    }}
    .toolbar-compact input,
    .toolbar-compact select {{
      padding: 7px 10px;
      font-size: 13px;
    }}
    .inline-form {{
      margin: 0;
    }}
    .split {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .subpanel {{
      background: #fff;
      border: 1px solid var(--line-soft);
      border-radius: 13px;
      padding: 10px;
    }}
    .subpanel h3 {{
      margin: 0 0 6px;
      font-size: 14px;
      letter-spacing: -0.01em;
    }}
    .chart-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 12px;
    }}
    .chart-card {{
      border: 1px solid var(--line-soft);
      background: #fff;
      border-radius: 13px;
      padding: 10px;
    }}
    .chart-card h3 {{
      margin: 0 0 7px;
      font-size: 14px;
      letter-spacing: -0.01em;
    }}
    .chart-note {{
      color: var(--muted);
      font-size: 12px;
      margin: 0 0 8px;
    }}
    .chart-canvas {{
      width: 100%;
      height: 190px;
      display: block;
      border-radius: 10px;
      background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
      border: 1px solid #eef2f6;
    }}
    @media (max-width: 980px) {{
      .kpis {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .split {{
        grid-template-columns: 1fr;
      }}
      .chart-grid {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 700px) {{
      .shell {{
        padding: 14px 10px 26px;
      }}
      .hero {{
        padding: 14px;
      }}
      .hero h1 {{
        font-size: 24px;
      }}
      .panel-head {{
        padding: 14px 12px 10px;
      }}
      .panel-content {{
        padding: 0 12px 12px;
      }}
      .toolbar {{
        flex-direction: column;
        align-items: stretch;
      }}
      .toolbar > * {{
        width: 100%;
      }}
      .check-line {{
        width: 100%;
      }}
      .help-strip {{
        gap: 6px;
      }}
      .help-pill {{
        width: 100%;
      }}
      .kpis {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="hero">
      <div class="hero-top">
        <div>
          <h1>{html.escape(lt("title"))}</h1>
          <p>{html.escape(lt("subtitle"))}</p>
        </div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
          <a class="quick-link" href="/miniapp?lang={ui_lang}" target="_blank">{html.escape(lt("open_miniapp"))}</a>
          <a class="jump-link {'active' if ui_lang == 'ru' else ''}" href="{html.escape(lang_ru_url)}">{html.escape(lt("lang_ru"))}</a>
          <a class="jump-link {'active' if ui_lang == 'en' else ''}" href="{html.escape(lang_en_url)}">{html.escape(lt("lang_en"))}</a>
        </div>
      </div>
      <div class="kpis">
        <div class="kpi">
          <div class="kpi-label">{html.escape(lt("users_kpi"))}</div>
          <div class="kpi-value">{total}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">{html.escape(lt("chats_kpi"))}</div>
          <div class="kpi-value">{chats_total}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">{html.escape(lt("features_kpi"))}</div>
          <div class="kpi-value">{features_enabled_total}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">{html.escape(lt("risk_kpi"))}</div>
          <div class="kpi-value {"danger" if suspicious_total > 0 else ""}">{suspicious_total}</div>
        </div>
      </div>
    </header>

    {f"<div class='notice'>{notice}</div>" if notice else ""}

    <nav class="jumpbar">
      <a class="jump-link" href="#users-panel">{html.escape(lt("jump_users"))}</a>
      <a class="jump-link" href="#broadcast-panel">{html.escape(lt("jump_broadcast"))}</a>
      <a class="jump-link" href="#chats-panel">{html.escape(lt("jump_chats"))}</a>
      <a class="jump-link" href="#monitoring-panel">{html.escape(lt("jump_monitoring"))}</a>
      <a class="jump-link" href="#features-panel">{html.escape(lt("jump_features"))}</a>
    </nav>
    <div class="help-strip">
      <div class="help-pill">{html.escape(lt("help_global"))}</div>
      <div class="help-pill">{html.escape(lt("help_local_filters"))}</div>
      <div class="help-pill">{html.escape(lt("help_toggle"))}</div>
    </div>

	    <details id="users-panel" class="panel fade-up" open>
	      <summary class="panel-head">
	        <div>
	          <h2>{html.escape(lt("users_header"))}</h2>
	          <p>{html.escape(lt("users_subtitle"))}</p>
	          <p class="section-help">{html.escape(lt("help_users"))}</p>
	        </div>
	        <div class="panel-chev" aria-hidden="true"></div>
	      </summary>
	      <div class="panel-content">
        <form class="toolbar" method="get" action="/">
          <input type="text" name="q" value="{q_html}" placeholder="{html.escape(lt('search_user'))}" title="{html.escape(lt('tt_search'), quote=True)}" />
          <select name="sort" title="{html.escape(lt('tt_sort'), quote=True)}">
            <option value="coins_desc" {"selected" if sort == "coins_desc" else ""}>{html.escape(lt("sort_coins_desc"))}</option>
            <option value="coins_asc" {"selected" if sort == "coins_asc" else ""}>{html.escape(lt("sort_coins_asc"))}</option>
            <option value="id_desc" {"selected" if sort == "id_desc" else ""}>{html.escape(lt("sort_id_desc"))}</option>
            <option value="id_asc" {"selected" if sort == "id_asc" else ""}>{html.escape(lt("sort_id_asc"))}</option>
            <option value="updated_desc" {"selected" if sort == "updated_desc" else ""}>{html.escape(lt("sort_updated_desc"))}</option>
          </select>
          <input type="number" min="1" max="{PAGE_SIZE_MAX}" name="page_size" value="{page_size}" title="{html.escape(lt('tt_page_size'), quote=True)}" />
          <input type="hidden" name="chat_q" value="{chat_q_html}" />
          <input type="hidden" name="lang" value="{ui_lang}" />
          <input type="hidden" name="monitor_days" value="{monitor_days}" />
          <input type="hidden" name="monitor_min_income" value="{monitor_min_income}" />
          <input type="hidden" name="monitor_min_transfer_out" value="{monitor_min_transfer_out}" />
          <input type="hidden" name="monitor_limit" value="{monitor_limit}" />
          <button class="btn-primary" type="submit" title="{html.escape(lt('tt_apply'), quote=True)}">{html.escape(lt("apply"))}</button>
        </form>

        <div class="toolbar toolbar-compact">
          <input id="users-local-search" type="text" placeholder="{html.escape(lt('local_filter_page'))}" title="{html.escape(lt('tt_local_search'), quote=True)}" />
          <select id="users-local-trust" title="{html.escape(lt('tt_status_filter'), quote=True)}">
            <option value="">{html.escape(lt("trust_all"))}</option>
            <option value="trusted">{html.escape(lt("trust_trusted"))}</option>
            <option value="untrusted">{html.escape(lt("trust_untrusted"))}</option>
          </select>
          <select id="users-local-activated" title="{html.escape(lt('tt_status_filter'), quote=True)}">
            <option value="">{html.escape(lt("activation_all"))}</option>
            <option value="on">{html.escape(lt("activation_on"))}</option>
            <option value="off">{html.escape(lt("activation_off"))}</option>
          </select>
        </div>
        <div class="table-info">
          <span>{html.escape(lt("total_users_db", total=total))}</span>
          <span id="users-visible-count">{html.escape(lt("visible_page", visible=len(users), total=len(users)))}</span>
        </div>

        <div class="table-wrap">
          <table id="users-table">
            <thead>
              <tr>
                <th>{html.escape(lt("col_user_id"))}</th>
                <th>{html.escape(lt("col_username"))}</th>
                <th>{html.escape(lt("col_name"))}</th>
                <th>{html.escape(lt("col_coins"))}</th>
                <th>{html.escape(lt("col_trust"))}</th>
                <th>{html.escape(lt("col_activated"))}</th>
                <th>{html.escape(lt("col_activated_at"))}</th>
                <th>{html.escape(lt("col_updated"))}</th>
                <th>{html.escape(lt("col_dm"))}</th>
                <th>{html.escape(lt("col_action"))}</th>
              </tr>
            </thead>
            <tbody>
              {''.join(rows_html) if rows_html else f"<tr><td colspan='10'>{html.escape(lt('no_users'))}</td></tr>"}
            </tbody>
          </table>
        </div>

        <div class="pager">
          <span>{prev_link}</span>
          <span>{html.escape(lt("page", page=page, total=total_pages))}</span>
          <span>{next_link}</span>
        </div>
	      </div>
	    </details>

	    <details id="broadcast-panel" class="panel fade-up">
	      <summary class="panel-head">
	        <div>
	          <h2>{html.escape(lt("broadcast_header"))}</h2>
	          <p>{html.escape(lt("broadcast_subtitle", token=token_status_text))}</p>
	          <p class="section-help">{html.escape(lt("help_broadcast"))}</p>
	        </div>
	        <div class="panel-chev" aria-hidden="true"></div>
	      </summary>
	      <div class="panel-content">
        <form method="post" action="/broadcast">
          <textarea name="text" placeholder="{html.escape(lt('message_text'))}" title="{html.escape(lt('tt_send_broadcast'), quote=True)}" required></textarea>
          <div class="toolbar" style="margin-top: 8px;">
            <label class="check-line"><input type="checkbox" name="activated_only" value="1" checked /> {html.escape(lt("activated_only"))}</label>
            <span class="chip">{html.escape(lt("token_chip"))}: {html.escape(token_status_text)}</span>
            <span class="chip">{html.escape(lt("active_users_page", count=active_on_page))}</span>
            <input type="hidden" name="next" value="{return_url_safe}" />
            <input type="hidden" name="lang" value="{ui_lang}" />
            <button class="btn-primary" type="submit" title="{html.escape(lt('tt_send_broadcast'), quote=True)}">{html.escape(lt("send_broadcast"))}</button>
          </div>
        </form>

        <div class="toolbar toolbar-compact">
          <input id="broadcast-local-search" type="text" placeholder="{html.escape(lt('local_filter_mode'))}" title="{html.escape(lt('tt_local_search'), quote=True)}" />
          <select id="broadcast-local-mode" title="{html.escape(lt('tt_status_filter'), quote=True)}">
            <option value="">{html.escape(lt("mode_all"))}</option>
            <option value="activated">{html.escape(lt("mode_activated"))}</option>
            <option value="all">{html.escape(lt("mode_everyone"))}</option>
          </select>
        </div>
        <div class="table-info">
          <span id="broadcast-visible-count">{html.escape(lt("visible_short", visible=len(broadcasts), total=len(broadcasts)))}</span>
        </div>

        <div class="table-wrap">
          <table id="broadcast-table">
            <thead>
              <tr>
                <th>{html.escape(lt("col_user_id"))}</th>
                <th>{html.escape(lt("col_text"))}</th>
                <th>{html.escape(lt("col_mode"))}</th>
                <th>{html.escape(lt("col_sent"))}</th>
                <th>{html.escape(lt("col_failed"))}</th>
                <th>{html.escape(lt("col_created"))}</th>
              </tr>
            </thead>
            <tbody>
              {''.join(broadcast_rows_html) if broadcast_rows_html else f"<tr><td colspan='6'>{html.escape(lt('no_broadcasts'))}</td></tr>"}
            </tbody>
          </table>
        </div>
	      </div>
	    </details>

	    <details id="chats-panel" class="panel fade-up">
	      <summary class="panel-head">
	        <div>
	          <h2>{html.escape(lt("chats_header"))}</h2>
	          <p>{html.escape(lt("chats_subtitle"))}</p>
	          <p class="section-help">{html.escape(lt("help_chats"))}</p>
	        </div>
	        <div class="panel-chev" aria-hidden="true"></div>
	      </summary>
	      <div class="panel-content">
        <form class="toolbar" method="get" action="/">
          <input type="hidden" name="q" value="{q_html}" />
          <input type="hidden" name="sort" value="{html.escape(sort)}" />
          <input type="hidden" name="page" value="{page}" />
          <input type="hidden" name="page_size" value="{page_size}" />
          <input type="hidden" name="lang" value="{ui_lang}" />
          <input type="hidden" name="monitor_days" value="{monitor_days}" />
          <input type="hidden" name="monitor_min_income" value="{monitor_min_income}" />
          <input type="hidden" name="monitor_min_transfer_out" value="{monitor_min_transfer_out}" />
          <input type="hidden" name="monitor_limit" value="{monitor_limit}" />
          <input type="text" name="chat_q" value="{chat_q_html}" placeholder="{html.escape(lt('search_chat'))}" title="{html.escape(lt('tt_search'), quote=True)}" />
          <button class="btn-primary" type="submit" title="{html.escape(lt('tt_apply'), quote=True)}">{html.escape(lt("find_chat"))}</button>
        </form>

        <div class="toolbar toolbar-compact">
          <input id="chats-local-search" type="text" placeholder="{html.escape(lt('local_filter_chats'))}" title="{html.escape(lt('tt_local_search'), quote=True)}" />
          <select id="chats-local-firework" title="{html.escape(lt('tt_status_filter'), quote=True)}">
            <option value="">{html.escape(lt("firework_all"))}</option>
            <option value="on">{html.escape(lt("status_on"))}</option>
            <option value="off">{html.escape(lt("status_off"))}</option>
          </select>
        </div>
        <div class="table-info">
          <span id="chats-visible-count">{html.escape(lt("visible_chats", visible=len(chats), total=len(chats)))}</span>
        </div>

        <div class="table-wrap">
          <table id="chats-table">
            <thead>
              <tr>
                <th>{html.escape(lt("col_chat_id"))}</th>
                <th>{html.escape(lt("col_title"))}</th>
                <th>{html.escape(lt("col_type"))}</th>
                <th>{html.escape(lt("col_firework"))}</th>
                <th>{html.escape(lt("col_progress"))}</th>
                <th>{html.escape(lt("col_period"))}</th>
                <th>{html.escape(lt("col_count"))}</th>
                <th>{html.escape(lt("col_updated"))}</th>
                <th>{html.escape(lt("col_action"))}</th>
              </tr>
            </thead>
            <tbody>
              {''.join(chat_rows_html) if chat_rows_html else f"<tr><td colspan='9'>{html.escape(lt('no_chats'))}</td></tr>"}
            </tbody>
          </table>
        </div>
	      </div>
	    </details>

	    <details id="monitoring-panel" class="panel fade-up">
	      <summary class="panel-head">
	        <div>
	          <h2>{html.escape(lt("monitoring_header"))}</h2>
	          <p>{html.escape(monitoring_status_text)}</p>
	          <p class="section-help">{html.escape(lt("help_monitoring"))}</p>
	        </div>
	        <div class="panel-chev" aria-hidden="true"></div>
	      </summary>
	      <div class="panel-content">
        <form class="toolbar" method="get" action="/">
          <input type="hidden" name="q" value="{q_html}" />
          <input type="hidden" name="sort" value="{html.escape(sort)}" />
          <input type="hidden" name="page" value="{page}" />
          <input type="hidden" name="page_size" value="{page_size}" />
          <input type="hidden" name="chat_q" value="{chat_q_html}" />
          <input type="hidden" name="lang" value="{ui_lang}" />
          <input type="number" min="1" max="30" name="monitor_days" value="{monitor_days}" placeholder="{html.escape(lt('placeholder_days'))}" title="{html.escape(lt('tt_monitor_input'), quote=True)}" />
          <input type="number" min="1" name="monitor_min_income" value="{monitor_min_income}" placeholder="{html.escape(lt('placeholder_income'))}" title="{html.escape(lt('tt_monitor_input'), quote=True)}" />
          <input type="number" min="1" name="monitor_min_transfer_out" value="{monitor_min_transfer_out}" placeholder="{html.escape(lt('placeholder_out'))}" title="{html.escape(lt('tt_monitor_input'), quote=True)}" />
          <input type="number" min="1" max="500" name="monitor_limit" value="{monitor_limit}" placeholder="{html.escape(lt('placeholder_limit'))}" title="{html.escape(lt('tt_monitor_input'), quote=True)}" />
          <button class="btn-primary" type="submit" title="{html.escape(lt('tt_monitor_apply'), quote=True)}">{html.escape(lt("monitor_apply"))}</button>
        </form>

        <div class="chart-grid">
          <div class="chart-card">
            <h3>{html.escape(lt("timeline_title"))}</h3>
            <p class="chart-note">{html.escape(lt("timeline_note", days=monitor_days))}</p>
            <canvas id="timeline-chart" class="chart-canvas"></canvas>
          </div>
          <div class="chart-card">
            <h3>{html.escape(lt("top_income_chart_title"))}</h3>
            <p class="chart-note">{html.escape(lt("top_income_chart_note"))}</p>
            <canvas id="top-income-chart" class="chart-canvas"></canvas>
          </div>
        </div>

        <div class="split">
          <div class="subpanel">
            <h3>{html.escape(lt("top_income_title", days=monitor_days))}</h3>
            <div class="table-info">
              <span id="income-visible-count">{html.escape(lt("visible_short", visible=len(top_income_5d), total=len(top_income_5d)))}</span>
            </div>
            <div class="table-wrap">
              <table id="income-table">
                <thead>
                  <tr>
                    <th>{html.escape(lt("col_user_id"))}</th>
                    <th>{html.escape(lt("col_name"))}</th>
                    <th>{html.escape(lt("col_income"))}</th>
                    <th>{html.escape(lt("col_transfer_out"))}</th>
                  </tr>
                </thead>
                <tbody>
                  {''.join(income_rows_html) if income_rows_html else f"<tr><td colspan='4'>{html.escape(lt('no_income'))}</td></tr>"}
                </tbody>
              </table>
            </div>
          </div>
          <div class="subpanel">
            <h3>{html.escape(lt("suspicious_title"))}</h3>
            <p class="dim">{html.escape(lt("suspicious_rule", income=monitor_min_income, out=monitor_min_transfer_out, days=monitor_days))}</p>
            <div class="toolbar toolbar-compact">
              <input id="risk-local-search" type="text" placeholder="{html.escape(lt('local_filter_risk'))}" title="{html.escape(lt('tt_local_search'), quote=True)}" />
            </div>
            <div class="table-info">
              <span id="risk-visible-count">{html.escape(lt("visible_short", visible=len(suspicious_rows), total=len(suspicious_rows)))}</span>
            </div>
            <div class="table-wrap">
              <table id="risk-table">
                <thead>
                  <tr>
                    <th>{html.escape(lt("col_user_id"))}</th>
                    <th>{html.escape(lt("col_name"))}</th>
                    <th>{html.escape(lt("col_income"))}</th>
                    <th>{html.escape(lt("col_transfer_out"))}</th>
                    <th>{html.escape(lt("col_events"))}</th>
                  </tr>
                </thead>
                <tbody>
                  {''.join(suspicious_rows_html) if suspicious_rows_html else f"<tr><td colspan='5'>{html.escape(lt('no_suspicious'))}</td></tr>"}
                </tbody>
              </table>
            </div>
          </div>
        </div>
	      </div>
	    </details>
	
	    <details id="features-panel" class="panel fade-up">
	      <summary class="panel-head">
	        <div>
	          <h2>{html.escape(lt("features_header"))}</h2>
	          <p>{html.escape(lt("features_subtitle"))}</p>
	          <p class="section-help">{html.escape(lt("help_features"))}</p>
	        </div>
	        <div class="panel-chev" aria-hidden="true"></div>
	      </summary>
	      <div class="panel-content">
        <div class="toolbar toolbar-compact">
          <input id="features-local-search" type="text" placeholder="{html.escape(lt('local_filter_features'))}" title="{html.escape(lt('tt_local_search'), quote=True)}" />
          <select id="features-local-status" title="{html.escape(lt('tt_status_filter'), quote=True)}">
            <option value="">{html.escape(lt("feature_status_all"))}</option>
            <option value="on">{html.escape(lt("status_on"))}</option>
            <option value="off">{html.escape(lt("status_off"))}</option>
          </select>
        </div>
        <div class="table-info">
          <span id="features-visible-count">{html.escape(lt("visible_short", visible=len(features), total=len(features)))}</span>
        </div>
        <div class="table-wrap">
          <table id="features-table">
            <thead>
              <tr>
                <th>{html.escape(lt("col_key"))}</th>
                <th>{html.escape(lt("col_description"))}</th>
                <th>{html.escape(lt("col_status"))}</th>
                <th>{html.escape(lt("col_updated"))}</th>
                <th>{html.escape(lt("col_action"))}</th>
              </tr>
            </thead>
            <tbody>
              {''.join(feature_rows_html) if feature_rows_html else f"<tr><td colspan='5'>{html.escape(lt('no_features'))}</td></tr>"}
            </tbody>
          </table>
        </div>
	      </div>
	    </details>

    <script id="dashboard-data" type="application/json">
      {json.dumps({"timeline": json.loads(timeline_data_json), "top_income": json.loads(income_chart_data_json)})}
    </script>
    <script>
      const VISIBLE_LABEL = "{html.escape(lt('visible_js'))}";
      const NO_DATA_LABEL = "{html.escape(lt('no_data_js'))}";
      const dashboardDataNode = document.getElementById("dashboard-data");
      let dashboardData = {{}};
      try {{
        dashboardData = JSON.parse(dashboardDataNode.textContent || "{{}}");
      }} catch (_) {{
        dashboardData = {{}};
      }}

      function setVisibleCount(nodeId, visible, total) {{
        const node = document.getElementById(nodeId);
        if (!node) {{
          return;
        }}
        node.textContent = `${{VISIBLE_LABEL}}: ${{visible}} / ${{total}}`;
      }}

      function tableFilter(options) {{
        const rows = Array.from(document.querySelectorAll(options.rowSelector));
        const total = rows.length;
        const run = () => {{
          const searchValue = options.searchInput ? (options.searchInput.value || "").trim().toLowerCase() : "";
          const visible = rows.reduce((count, row) => {{
            const hay = (row.dataset.search || "").toLowerCase();
            let ok = searchValue === "" || hay.includes(searchValue);
            if (ok && options.extraCheck) {{
              ok = options.extraCheck(row);
            }}
            row.style.display = ok ? "" : "none";
            return count + (ok ? 1 : 0);
          }}, 0);
          setVisibleCount(options.countNodeId, visible, total);
        }};

        if (options.searchInput) {{
          options.searchInput.addEventListener("input", run);
        }}
        (options.inputs || []).forEach((node) => {{
          if (node) {{
            node.addEventListener("change", run);
          }}
        }});
        run();
      }}

      tableFilter({{
        rowSelector: "#users-table tbody tr.user-row",
        searchInput: document.getElementById("users-local-search"),
        countNodeId: "users-visible-count",
        inputs: [document.getElementById("users-local-trust"), document.getElementById("users-local-activated")],
        extraCheck: (row) => {{
          const trustValue = (document.getElementById("users-local-trust").value || "").trim();
          const activatedValue = (document.getElementById("users-local-activated").value || "").trim();
          if (trustValue && row.dataset.trust !== trustValue) {{
            return false;
          }}
          if (activatedValue && row.dataset.activated !== activatedValue) {{
            return false;
          }}
          return true;
        }},
      }});

      tableFilter({{
        rowSelector: "#chats-table tbody tr.chat-row",
        searchInput: document.getElementById("chats-local-search"),
        countNodeId: "chats-visible-count",
        inputs: [document.getElementById("chats-local-firework")],
        extraCheck: (row) => {{
          const val = (document.getElementById("chats-local-firework").value || "").trim();
          if (val && row.dataset.firework !== val) {{
            return false;
          }}
          return true;
        }},
      }});

      tableFilter({{
        rowSelector: "#features-table tbody tr.feature-row",
        searchInput: document.getElementById("features-local-search"),
        countNodeId: "features-visible-count",
        inputs: [document.getElementById("features-local-status")],
        extraCheck: (row) => {{
          const val = (document.getElementById("features-local-status").value || "").trim();
          if (val && row.dataset.enabled !== val) {{
            return false;
          }}
          return true;
        }},
      }});

      tableFilter({{
        rowSelector: "#broadcast-table tbody tr.broadcast-row",
        searchInput: document.getElementById("broadcast-local-search"),
        countNodeId: "broadcast-visible-count",
        inputs: [document.getElementById("broadcast-local-mode")],
        extraCheck: (row) => {{
          const val = (document.getElementById("broadcast-local-mode").value || "").trim();
          if (val && row.dataset.mode !== val) {{
            return false;
          }}
          return true;
        }},
      }});

      tableFilter({{
        rowSelector: "#risk-table tbody tr.risk-row",
        searchInput: document.getElementById("risk-local-search"),
        countNodeId: "risk-visible-count",
      }});

      function setupCanvas(canvas) {{
        if (!canvas) {{
          return null;
        }}
        const dpr = Math.max(1, window.devicePixelRatio || 1);
        const cssW = Math.max(280, canvas.clientWidth || 280);
        const cssH = Math.max(180, canvas.clientHeight || 180);
        canvas.width = Math.floor(cssW * dpr);
        canvas.height = Math.floor(cssH * dpr);
        const ctx = canvas.getContext("2d");
        ctx.scale(dpr, dpr);
        return {{ ctx, width: cssW, height: cssH }};
      }}

      function drawLineChart() {{
        const canvas = document.getElementById("timeline-chart");
        const prepared = setupCanvas(canvas);
        if (!prepared) {{
          return;
        }}
        const {{ ctx, width, height }} = prepared;
        const timeline = dashboardData.timeline || {{}};
        const labels = Array.isArray(timeline.labels) ? timeline.labels : [];
        const income = Array.isArray(timeline.income) ? timeline.income : [];
        const transfer = Array.isArray(timeline.transfer) ? timeline.transfer : [];
        const maxValue = Math.max(1, Number(timeline.max_value || 0));
        const pad = {{ left: 34, right: 14, top: 12, bottom: 26 }};
        const chartW = width - pad.left - pad.right;
        const chartH = height - pad.top - pad.bottom;

        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, width, height);

        ctx.strokeStyle = "#e5e7eb";
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i += 1) {{
          const y = pad.top + (chartH * i) / 4;
          ctx.beginPath();
          ctx.moveTo(pad.left, y);
          ctx.lineTo(width - pad.right, y);
          ctx.stroke();
        }}

        const pointX = (idx, total) => {{
          if (total <= 1) {{
            return pad.left + chartW / 2;
          }}
          return pad.left + (chartW * idx) / (total - 1);
        }};
        const pointY = (value) => pad.top + chartH - (chartH * value) / maxValue;

        function drawSeries(values, color) {{
          if (!values.length) {{
            return;
          }}
          ctx.beginPath();
          values.forEach((value, idx) => {{
            const x = pointX(idx, values.length);
            const y = pointY(Number(value || 0));
            if (idx === 0) {{
              ctx.moveTo(x, y);
            }} else {{
              ctx.lineTo(x, y);
            }}
          }});
          ctx.strokeStyle = color;
          ctx.lineWidth = 2;
          ctx.stroke();
        }}

        drawSeries(income, "#0a84ff");
        drawSeries(transfer, "#ef4444");

        ctx.fillStyle = "#6b7280";
        ctx.font = "11px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif";
        labels.forEach((label, idx) => {{
          if (labels.length > 8 && idx % 2 !== 0) {{
            return;
          }}
          const x = pointX(idx, labels.length);
          ctx.fillText(label, x - 12, height - 7);
        }});
      }}

      function drawBarChart() {{
        const canvas = document.getElementById("top-income-chart");
        const prepared = setupCanvas(canvas);
        if (!prepared) {{
          return;
        }}
        const {{ ctx, width, height }} = prepared;
        const items = Array.isArray(dashboardData.top_income) ? dashboardData.top_income : [];
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, width, height);

        if (!items.length) {{
          ctx.fillStyle = "#6b7280";
          ctx.font = "12px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif";
          ctx.fillText(NO_DATA_LABEL, 12, 20);
          return;
        }}

        const maxValue = Math.max(1, ...items.map((item) => Number(item.income || 0)));
        const barH = Math.max(10, Math.floor((height - 24) / items.length) - 4);
        items.forEach((item, idx) => {{
          const y = 10 + idx * (barH + 4);
          const w = Math.max(2, ((width - 170) * Number(item.income || 0)) / maxValue);
          ctx.fillStyle = "#dbeafe";
          ctx.fillRect(140, y, width - 150, barH);
          ctx.fillStyle = "#0a84ff";
          ctx.fillRect(140, y, w, barH);
          ctx.fillStyle = "#111827";
          ctx.font = "11px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif";
          const label = String(item.label || "user").slice(0, 18);
          ctx.fillText(label, 8, y + barH - 2);
          ctx.fillText(String(item.income || 0), 146 + w, y + barH - 2);
        }});
      }}

      function redrawCharts() {{
        drawLineChart();
        drawBarChart();
      }}

      redrawCharts();
      window.addEventListener("resize", () => {{
        clearTimeout(window.__uiResizeTimer);
        window.__uiResizeTimer = setTimeout(redrawCharts, 130);
      }});

      const jumpLinks = Array.from(document.querySelectorAll(".jump-link"));
      const sectionIds = jumpLinks
        .map((link) => (link.getAttribute("href") || "").replace("#", ""))
        .filter(Boolean);
      const sectionNodes = sectionIds
        .map((id) => document.getElementById(id))
        .filter(Boolean);

      function setActiveJump(id) {{
        jumpLinks.forEach((link) => {{
          const target = (link.getAttribute("href") || "").replace("#", "");
          link.classList.toggle("active", target === id);
        }});
      }}

      if (sectionNodes.length > 0) {{
        const observer = new IntersectionObserver(
          (entries) => {{
            entries.forEach((entry) => {{
              if (entry.isIntersecting && entry.target && entry.target.id) {{
                setActiveJump(entry.target.id);
              }}
            }});
          }},
          {{
            rootMargin: "-20% 0px -60% 0px",
            threshold: 0.1,
          }}
        );
        sectionNodes.forEach((node) => observer.observe(node));
        setActiveJump(sectionNodes[0].id);
      }}
    </script>
  </main>
</body>
</html>
"""


@app.get("/miniapp")
def miniapp():
    initial_lang = normalize_lang(request.args.get("lang"))
    return """
<!doctype html>
<html lang="__HTML_LANG__">
<head>
  <meta charset="utf-8">
	  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>TGM Coin</title>
  <style>
    :root {
      --bg: #f4f5f7;
      --surface: rgba(255, 255, 255, 0.84);
      --surface-strong: #ffffff;
      --line: #e5e7eb;
      --text: #0f172a;
      --muted: #64748b;
      --accent: #0a84ff;
      --accent-soft: #e6f1ff;
      --success: #10b981;
      --radius-xl: 24px;
      --radius-lg: 18px;
      --radius-md: 12px;
      --shadow: 0 16px 42px rgba(15, 23, 42, 0.12);
    }
    body.theme-dark {
      --bg: #0b1220;
      --surface: rgba(15, 23, 42, 0.72);
      --surface-strong: #0f172a;
      --line: rgba(148, 163, 184, 0.22);
      --text: #e5e7eb;
      --muted: rgba(226, 232, 240, 0.68);
      --accent: #0a84ff;
      --accent-soft: rgba(10, 132, 255, 0.18);
      --success: #34d399;
      --shadow: 0 18px 48px rgba(0, 0, 0, 0.35);
    }
    * { box-sizing: border-box; }
    button { -webkit-tap-highlight-color: transparent; touch-action: manipulation; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 8% 2%, #e6f2ff 0%, transparent 34%),
        radial-gradient(circle at 100% 0%, #f5fff5 0%, transparent 28%),
        var(--bg);
      padding: 12px;
    }
    body.theme-dark {
      background:
        radial-gradient(circle at 10% 6%, rgba(10, 132, 255, 0.22) 0%, transparent 40%),
        radial-gradient(circle at 96% 2%, rgba(52, 211, 153, 0.16) 0%, transparent 36%),
        var(--bg);
    }
    .app-shell {
      max-width: 860px;
      margin: 0 auto;
      background: var(--surface);
      border: 1px solid rgba(255, 255, 255, 0.8);
      border-radius: var(--radius-xl);
      backdrop-filter: blur(10px);
      box-shadow: var(--shadow);
      overflow: hidden;
      animation: rise .42s ease;
    }
    @keyframes rise {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .head {
      position: sticky;
      top: 0;
      z-index: 40;
      padding: calc(14px + env(safe-area-inset-top)) 16px 12px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      background: rgba(255,255,255,.78);
      backdrop-filter: blur(18px) saturate(180%);
      -webkit-backdrop-filter: blur(18px) saturate(180%);
    }
    body.theme-dark .head {
      background: rgba(15,23,42,.72);
    }
    .brand {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .title {
      margin: 0;
      font-size: 22px;
      font-weight: 780;
      letter-spacing: -0.02em;
    }
    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
    }
    .head-right {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .lang-switch {
      display: inline-flex;
      gap: 6px;
    }
    .mode-switch {
      display: inline-flex;
      gap: 6px;
    }
    .chip-btn {
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      color: #1f2937;
      font-weight: 640;
      padding: 10px 12px;
      font-size: 12px;
      min-height: 44px;
      min-width: 44px;
      cursor: pointer;
      transition: all .15s ease;
    }
    .chip-btn:active { transform: translateY(1px); }
    .chip-btn.icon-btn {
      width: 38px;
      padding: 7px 0;
      text-align: center;
    }
    body.theme-dark .chip-btn { background: rgba(15,23,42,.82); color: var(--text); }
    .chip-btn.active {
      border-color: #9ec5ff;
      background: var(--accent-soft);
      color: #0b5ec4;
    }
    :root { --tabbar-space: calc(78px + env(safe-area-inset-bottom)); }
    .tabs {
      position: sticky;
      bottom: 0;
      z-index: 35;
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 2px;
      padding: 10px 10px calc(10px + env(safe-area-inset-bottom));
      border-top: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.80);
      backdrop-filter: blur(18px) saturate(180%);
      -webkit-backdrop-filter: blur(18px) saturate(180%);
      overflow: hidden;
    }
    body.theme-dark .tabs { background: rgba(15, 23, 42, 0.68); }
    .tab-indicator {
      position: absolute;
      left: 10px;
      top: 10px;
      height: 54px;
      width: 20px;
      border-radius: 16px;
      background: rgba(10, 132, 255, 0.10);
      border: 1px solid rgba(10, 132, 255, 0.14);
      box-shadow: 0 10px 24px rgba(2, 8, 23, 0.10);
      transform: translateX(0);
      transition:
        transform 380ms cubic-bezier(.2,.9,.2,1),
        width 380ms cubic-bezier(.2,.9,.2,1);
      pointer-events: none;
    }
    body.theme-dark .tab-indicator {
      background: rgba(10, 132, 255, 0.14);
      border-color: rgba(158, 197, 255, 0.18);
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.38);
    }
    .tab {
      position: relative;
      border: 0;
      background: transparent;
      border-radius: 16px;
      padding: 8px 6px 7px;
      min-height: 54px;
      font-size: 10px;
      font-weight: 700;
      color: var(--muted);
      cursor: pointer;
      transition: color .18s ease, transform .18s ease;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
    }
    .tab:active { transform: translateY(1px); }
    .tab-ico {
      width: 20px;
      height: 20px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: currentColor;
      opacity: 0.92;
    }
    .tab-label { line-height: 1; }
    .tab.active { color: #0b5ec4; }
    body.theme-dark .tab.active { color: rgba(191, 219, 254, 0.96); }
    @keyframes tabpop {
      0% { transform: translateY(2px) scale(0.92); opacity: 0.55; }
      60% { transform: translateY(-1px) scale(1.08); opacity: 1; }
      100% { transform: translateY(0) scale(1); opacity: 1; }
    }
    .tab.active .tab-ico { animation: tabpop 280ms cubic-bezier(.2,.9,.2,1); }

    .panel {
      display: none;
      padding: 14px 14px calc(14px + var(--tabbar-space));
      animation: fade .22s ease;
    }
    @keyframes fade {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .panel.active { display: block; }
    .hero-card {
      border-radius: var(--radius-lg);
      background: linear-gradient(155deg, #0f172a 0%, #111827 40%, #0a84ff 100%);
      color: #fff;
      padding: 14px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.14);
      margin-bottom: 12px;
    }
    .hero-title {
      margin: 0;
      font-size: 12px;
      color: rgba(226,232,240,.9);
      letter-spacing: .06em;
      text-transform: uppercase;
    }
    .hero-balance {
      margin: 8px 0 0;
      font-size: 34px;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1;
    }
    .hero-row {
      margin-top: 10px;
      display: flex;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 12px;
      color: rgba(241,245,249,.92);
    }
    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-bottom: 12px;
    }
    .stat-card, .content-card {
      border: 1px solid var(--line);
      background: var(--surface-strong);
      border-radius: var(--radius-md);
      padding: 10px;
    }
    .stat-label {
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .05em;
      margin-bottom: 4px;
    }
    .stat-value {
      font-size: 22px;
      font-weight: 770;
      letter-spacing: -0.02em;
    }
    .cta-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin-bottom: 12px;
    }
    .cta {
      border-radius: 12px;
      border: 1px solid var(--line);
      background: #fff;
      font-weight: 700;
      color: #334155;
      padding: 10px 8px;
      font-size: 12px;
      cursor: pointer;
      text-align: center;
    }
    .cta.primary {
      border-color: #9ec5ff;
      background: var(--accent-soft);
      color: #0b5ec4;
    }
    .prefs {
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 12px;
      padding: 10px;
      margin-bottom: 12px;
    }
    .toggle-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 8px 0;
      border-bottom: 1px solid var(--line);
    }
    .toggle-row:last-child { border-bottom: 0; }
    .toggle-copy {
      min-width: 0;
    }
    .toggle-title {
      margin: 0;
      font-size: 12px;
      font-weight: 700;
      color: #1f2937;
    }
    .toggle-note {
      margin: 2px 0 0;
      color: #64748b;
      font-size: 11px;
      line-height: 1.25;
    }
    .switch {
      position: relative;
      width: 44px;
      height: 26px;
      display: inline-block;
    }
    .switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }
    .switch-slider {
      position: absolute;
      inset: 0;
      background: #d1d5db;
      border-radius: 999px;
      transition: .2s ease;
      cursor: pointer;
    }
    .switch-slider:before {
      content: "";
      position: absolute;
      width: 20px;
      height: 20px;
      left: 3px;
      top: 3px;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0 1px 3px rgba(0,0,0,.2);
      transition: .2s ease;
    }
    .switch input:checked + .switch-slider {
      background: var(--success);
    }
    .switch input:checked + .switch-slider:before {
      transform: translateX(18px);
    }
    .segment {
      display: inline-grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 4px;
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 3px;
      background: #f8fafc;
      margin-bottom: 8px;
    }
    .segment-btn {
      border: 0;
      border-radius: 8px;
      background: transparent;
      color: #64748b;
      padding: 8px 6px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
    }
    .segment-btn.active {
      background: #fff;
      color: #0b5ec4;
      box-shadow: 0 1px 3px rgba(15,23,42,.12);
    }
    .segment-btn.disabled {
      color: #94a3b8;
    }
    .section-title {
      margin: 0 0 6px;
      font-size: 14px;
      font-weight: 760;
      letter-spacing: -0.01em;
    }
    .section-note {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 12px;
    }
    .list-row {
      display: grid;
      grid-template-columns: 34px 1fr auto;
      gap: 8px;
      align-items: center;
      padding: 9px 4px;
      border-bottom: 1px solid var(--line);
      font-size: 13px;
    }
    .list-row:last-child { border-bottom: 0; }
    .rank {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      border: 1px solid var(--line);
      background: #f8fafc;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      color: #475569;
      font-weight: 700;
    }
    .you-row {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 10px;
      padding: 8px;
      margin-bottom: 8px;
      font-size: 12px;
      color: #1e3a8a;
      font-weight: 700;
    }
    .who {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-weight: 640;
    }
    .score {
      font-weight: 780;
      color: #0f172a;
      white-space: nowrap;
    }
    .input-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
    }
    input.ref-input {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      font-size: 12px;
      width: 100%;
      background: #f8fafc;
      color: #0f172a;
    }
    body.theme-dark input.ref-input { background: rgba(2,6,23,.45); color: var(--text); }
    .btn {
      border: 1px solid #9ec5ff;
      border-radius: 10px;
      padding: 10px 12px;
      background: var(--accent-soft);
      color: #0b5ec4;
      font-weight: 700;
      font-size: 12px;
      cursor: pointer;
    }
    body.theme-dark .btn { color: rgba(219,234,254,.96); border-color: rgba(158,197,255,.55); }
    .cards {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .task-card {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #fff;
      padding: 10px;
    }
    body.theme-dark .task-card { background: rgba(15,23,42,.86); }
    .task-title {
      margin: 0;
      font-size: 13px;
      font-weight: 730;
    }
    .task-meta {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 11px;
    }
    .badge {
      display: inline-block;
      margin-top: 7px;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 10px;
      font-weight: 700;
      border: 1px solid #dbeafe;
      background: #eff6ff;
      color: #1e40af;
    }
    body.theme-dark .badge { border-color: rgba(147,197,253,.28); background: rgba(30,58,138,.28); color: rgba(191,219,254,.96); }
    details {
      margin-top: 10px;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 8px 10px;
      background: #fff;
    }
    body.theme-dark details { background: rgba(15,23,42,.86); }
    summary {
      cursor: pointer;
      font-weight: 700;
      font-size: 13px;
      color: #334155;
    }
    body.theme-dark summary { color: rgba(226,232,240,.92); }

    .mini-hint {
      margin: 8px 0 0;
      padding: 8px 10px;
      border-radius: 12px;
      border: 1px dashed rgba(148, 163, 184, 0.35);
      color: var(--muted);
      background: rgba(255,255,255,0.45);
      font-size: 12px;
      line-height: 1.35;
    }
    body.theme-dark .mini-hint { background: rgba(2,6,23,.26); border-color: rgba(148, 163, 184, 0.22); }
    .road-item {
      margin-top: 8px;
      border-top: 1px solid var(--line);
      padding-top: 8px;
    }
    .road-phase {
      font-size: 10px;
      letter-spacing: .07em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 2px;
    }
    .road-title {
      margin: 0 0 2px;
      font-size: 13px;
      font-weight: 700;
    }
    .road-desc {
      margin: 0;
      color: #64748b;
      font-size: 11px;
      line-height: 1.35;
    }
    .hint {
      margin-top: 6px;
      font-size: 12px;
      color: var(--muted);
    }
    .support {
      margin-top: 8px;
      font-size: 11px;
      color: #64748b;
    }
    .util-hidden {
      display: none !important;
    }
    body.mode-simple .pro-only {
      display: none !important;
    }
    body.mode-pro .simple-only {
      display: none !important;
    }
    body.mode-simple .tabs { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .util-no-motion *,
    .util-no-motion *::before,
    .util-no-motion *::after {
      animation: none !important;
      transition: none !important;
    }
    .toast {
      position: fixed;
      left: 50%;
      bottom: calc(var(--tabbar-space) + 12px);
      transform: translate(-50%, 14px);
      max-width: min(88vw, 380px);
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.88);
      color: #f8fafc;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: .01em;
      box-shadow: 0 16px 34px rgba(2, 8, 23, 0.34);
      opacity: 0;
      pointer-events: none;
      transition: opacity .22s ease, transform .26s ease;
      z-index: 60;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
    .toast.show {
      opacity: 1;
      transform: translate(-50%, 0);
    }
    body.theme-dark .toast {
      background: rgba(2, 6, 23, 0.92);
      box-shadow: 0 16px 34px rgba(0, 0, 0, 0.48);
    }
    @media (max-width: 720px) {
      body { padding: 0; }
      .app-shell { border-radius: 0; }
      .cta-row { grid-template-columns: 1fr; }
      .grid-2, .cards { grid-template-columns: 1fr; }
      .hero-balance { font-size: 30px; }
    }
  </style>
  <script defer src="https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js"></script>
</head>
<body>
  <main class="app-shell">
    <header class="head">
      <div class="brand">
        <h1 class="title" id="title">TGM Coin</h1>
        <p class="subtitle" id="subtitle">Personal wallet and growth center</p>
      </div>
      <div class="head-right">
        <button id="btn-lang" class="chip-btn" type="button" title="Language">RU</button>
        <button id="btn-mode" class="chip-btn" type="button" title="Mode">Simple</button>
        <button id="theme-toggle" class="chip-btn icon-btn" type="button" title="Theme">☀</button>
      </div>
    </header>

    <nav class="tabs" aria-label="Navigation">
      <div class="tab-indicator" aria-hidden="true"></div>
      <button id="tab-home" class="tab active" type="button">
        <span class="tab-ico" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 10.5 12 3l9 7.5"></path>
            <path d="M5 10.5V21h14V10.5"></path>
          </svg>
        </span>
        <span class="tab-label" id="tab-home-label">Home</span>
      </button>
      <button id="tab-top" class="tab pro-only" type="button">
        <span class="tab-ico" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M7 21V10"></path>
            <path d="M12 21V3"></path>
            <path d="M17 21v-7"></path>
          </svg>
        </span>
        <span class="tab-label" id="tab-top-label">Top</span>
      </button>
      <button id="tab-friends" class="tab" type="button">
        <span class="tab-ico" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="8.5" cy="7" r="3"></circle>
            <path d="M20 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16.5 4a3 3 0 0 1 0 6"></path>
          </svg>
        </span>
        <span class="tab-label" id="tab-friends-label">Friends</span>
      </button>
      <button id="tab-earn" class="tab" type="button">
        <span class="tab-ico" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v20"></path>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7H14a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
        </span>
        <span class="tab-label" id="tab-earn-label">Earn</span>
      </button>
      <button id="tab-settings" class="tab pro-only" type="button">
        <span class="tab-ico" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 15.5A3.5 3.5 0 1 0 12 8.5a3.5 3.5 0 0 0 0 7z"></path>
            <path d="M19.4 15a1.7 1.7 0 0 0 .33 1.87l.05.05a2 2 0 0 1-1.41 3.41h-.12a1.7 1.7 0 0 0-1.61 1.17 2 2 0 0 1-3.8 0A1.7 1.7 0 0 0 11.1 20.3h-.12a2 2 0 0 1-1.41-3.41l.05-.05A1.7 1.7 0 0 0 9.94 15a1.7 1.7 0 0 0-1.47-1.1A2 2 0 0 1 6.7 10.1a1.7 1.7 0 0 0 1.17-1.61V8.37A2 2 0 0 1 11.28 7l.05.05A1.7 1.7 0 0 0 13.2 7l.05-.05A2 2 0 0 1 16.66 8.37v.12a1.7 1.7 0 0 0 1.17 1.61 2 2 0 0 1 0 3.8A1.7 1.7 0 0 0 19.4 15z"></path>
          </svg>
        </span>
        <span class="tab-label" id="tab-settings-label">Settings</span>
      </button>
    </nav>

    <section id="panel-home" class="panel active">
      <div class="hero-card">
        <p class="hero-title" id="home-hero-title">Your Balance</p>
        <p class="hero-balance"><span id="home-coins">0</span> TGM</p>
        <div class="hero-row">
          <span id="home-name">Guest</span>
          <span id="home-rank-hero" class="pro-only"># -</span>
        </div>
      </div>
      <div class="grid-2 simple-only">
        <div class="stat-card">
          <div class="stat-label" id="label-today-income">Today</div>
          <div class="stat-value"><span id="home-today-income">0</span> TGM</div>
        </div>
        <div class="stat-card">
          <div class="stat-label" id="label-streak">Streak</div>
          <div class="stat-value"><span id="home-streak-days">0</span><span id="label-days-suffix">d</span></div>
        </div>
      </div>
      <div class="content-card simple-only" style="margin-bottom:12px;">
        <h3 class="section-title" id="simple-next-title">Next reward</h3>
        <p class="section-note" id="simple-next-note">One reward per minute per user.</p>
        <div class="hero-row" style="margin-top:8px;">
          <span id="simple-next-status">Ready</span>
          <span class="chip"><span id="simple-next-seconds">0</span>s</span>
        </div>
      </div>
      <div class="grid-2 pro-only">
        <div class="stat-card">
          <div class="stat-label" id="label-total-economy">Total economy</div>
          <div class="stat-value" id="home-total-coins">0</div>
        </div>
        <div class="stat-card">
          <div class="stat-label" id="label-total-users">Users</div>
          <div class="stat-value" id="home-total-users">0</div>
        </div>
      </div>
      <div class="cta-row">
        <button id="cta-earn" class="cta primary" type="button">Earn</button>
        <button id="cta-friends" class="cta" type="button">Invite</button>
        <button id="cta-wallet" class="cta pro-only" type="button">Wallet</button>
      </div>
      <div class="content-card simple-only" style="margin-bottom:12px;">
        <h3 class="section-title" id="simple-how-title">How to earn</h3>
        <p class="section-note" id="simple-how-note">Write in the chat to get coins. No buttons, no thinking.</p>
        <div class="mini-hint" id="simple-how-steps"></div>
      </div>
      <div class="content-card pro-only">
        <h3 class="section-title" id="home-top-title">Top right now</h3>
        <p class="section-note" id="home-top-note">Social proof keeps users active.</p>
        <div id="home-top-list"></div>
      </div>
      <div class="support" id="support-line"></div>
    </section>

    <section id="panel-top" class="panel pro-only">
      <div class="content-card">
        <h3 class="section-title" id="top-title">Leaderboard</h3>
        <p class="section-note" id="top-note">Who collected the most coins.</p>
        <div class="segment">
          <button id="top-range-all" class="segment-btn active" type="button">All</button>
          <button id="top-range-7d" class="segment-btn" type="button">7D</button>
          <button id="top-range-24h" class="segment-btn" type="button">24H</button>
        </div>
        <div id="you-row" class="you-row"></div>
        <div id="top-list"></div>
      </div>
    </section>

    <section id="panel-friends" class="panel">
      <div class="content-card simple-only" style="margin-bottom:8px;">
        <h3 class="section-title" id="friends-simple-title">Invite = more coins</h3>
        <p class="section-note" id="friends-simple-note">Get a bonus for each friend and a commission from their rewards.</p>
      </div>
      <div class="content-card" style="margin-bottom:8px;">
        <h3 class="section-title" id="friends-title">Invite friends</h3>
        <p class="section-note" id="friends-note">Share your referral link and earn more.</p>
        <div class="input-row">
          <input id="ref-link" class="ref-input" readonly value="">
          <button id="copy-ref" class="btn" type="button">Copy</button>
        </div>
        <p class="hint" id="copy-hint"></p>
      </div>
      <div class="grid-2">
        <div class="stat-card">
          <div class="stat-label" id="friends-total-label">Invited</div>
          <div class="stat-value" id="friends-total">0</div>
        </div>
        <div class="stat-card">
          <div class="stat-label" id="friends-income-label">Referral income</div>
          <div class="stat-value" id="friends-income">0</div>
        </div>
      </div>
      <div class="content-card pro-only">
        <h3 class="section-title" id="friends-top-title">Top referrers</h3>
        <div id="friends-top-list"></div>
      </div>
    </section>

    <section id="panel-earn" class="panel">
      <div class="content-card" style="margin-bottom:8px;">
        <h3 class="section-title" id="earn-title">Earn and spend</h3>
        <p class="section-note" id="earn-note">Tasks, boosts and shop without overload.</p>
        <div class="cards">
          <div class="task-card">
            <p class="task-title" id="shop-title">Shop</p>
            <p class="task-meta" id="shop-meta">Spend TGM on boosts and perks.</p>
            <span class="badge" id="shop-badge">Soon</span>
          </div>
          <div class="task-card">
            <p class="task-title" id="boost-free-title">Boosts</p>
            <p class="task-meta" id="boost-free-meta">Multipliers and extra rewards (planned).</p>
            <span class="badge" id="boost-free-badge">Roadmap</span>
          </div>
          <div id="wallet-card" class="task-card pro-only">
            <p class="task-title" id="wallet-title">Wallet</p>
            <p class="task-meta" id="wallet-note">Connect wallet via TON Connect.</p>
            <div id="ton-connect" style="margin-top:8px;"></div>
            <p class="task-meta" id="wallet-status" style="margin-top:8px;"></p>
          </div>
        </div>
        <div class="pro-only">
          <div class="toggle-row" style="padding-top:10px;">
            <div class="toggle-copy">
              <p class="toggle-title" id="pref-planned-title">Show planned modules</p>
              <p class="toggle-note" id="pref-planned-note">Hide cards that are not released yet.</p>
            </div>
            <label class="switch">
              <input id="toggle-planned" type="checkbox" checked>
              <span class="switch-slider"></span>
            </label>
          </div>
          <div class="cards" style="margin-top:8px;">
            <div class="task-card planned-item">
              <p class="task-title" id="task-chat-title">Daily chat streak</p>
              <p class="task-meta" id="task-chat-meta">Write messages in chats to keep streak alive.</p>
              <span class="badge" id="task-chat-badge">Active</span>
            </div>
            <div class="task-card planned-item">
              <p class="task-title" id="task-friends-title">Invite friends</p>
              <p class="task-meta" id="task-friends-meta">Earn fixed bonus and passive commission.</p>
              <span class="badge" id="task-friends-badge">Top loop</span>
            </div>
          </div>
        </div>
      </div>
      <details class="pro-only">
        <summary id="roadmap-summary">Roadmap (expand)</summary>
        <div id="roadmap-list"></div>
      </details>
    </section>

    <section id="panel-settings" class="panel pro-only">
      <div class="content-card" style="margin-bottom:8px;">
        <h3 class="section-title" id="settings-title">Settings</h3>
        <p class="section-note" id="settings-note">UI preferences and hints. (Mode/theme are in the top bar.)</p>
        <div class="prefs">
          <div class="toggle-row pro-only">
            <div class="toggle-copy">
              <p class="toggle-title" id="pref-focus-title">Focus mode</p>
              <p class="toggle-note" id="pref-focus-note">Hide secondary hints for a cleaner screen.</p>
            </div>
            <label class="switch">
              <input id="toggle-focus" type="checkbox">
              <span class="switch-slider"></span>
            </label>
          </div>
          <div class="toggle-row pro-only">
            <div class="toggle-copy">
              <p class="toggle-title" id="pref-anim-title">Smooth motion</p>
              <p class="toggle-note" id="pref-anim-note">Use subtle transitions between sections.</p>
            </div>
            <label class="switch">
              <input id="toggle-animate" type="checkbox" checked>
              <span class="switch-slider"></span>
            </label>
          </div>
          <div class="toggle-row pro-only">
            <div class="toggle-copy">
              <p class="toggle-title" id="pref-roadmap-title">Show roadmap details</p>
              <p class="toggle-note" id="pref-roadmap-note">Expand roadmap section by default.</p>
            </div>
            <label class="switch">
              <input id="toggle-roadmap" type="checkbox">
              <span class="switch-slider"></span>
            </label>
          </div>
        </div>
        <div class="mini-hint" id="settings-hint">
          Tip: open the app from the bot menu to see your ID, rank and referral link.
        </div>
      </div>
      <div class="content-card">
        <h3 class="section-title" id="settings-about-title">About</h3>
        <p class="section-note" id="settings-about-note">Open via bot to see your personal rank and referral link.</p>
        <div class="support" id="support-line-settings"></div>
      </div>
    </section>
  </main>
  <div id="toast" class="toast" role="status" aria-live="polite"></div>

  <script>
    const I18N = {
      ru: {
        title: "TGM Coin",
        subtitle: "Твой баланс, рейтинг и рост",
        tabHome: "Баланс",
        tabTop: "ТОП",
        tabFriends: "Друзья",
        tabEarn: "Заработок",
        tabSettings: "Настройки",
        heroTitle: "Твой счет",
        todayIncome: "Сегодня",
        streak: "Стрик",
        daysSuffix: "д",
        simpleHowTitle: "Как зарабатывать",
        simpleHowNote: "Пиши в чате и получай монеты. Без кнопок и без лишнего.",
        simpleHowSteps: "1) Напиши сообщение в чате (раз в минуту).\\n2) Забирай монеты и держи стрик каждый день.\\n3) В приложении: магазин, бусты, рефералы, кошелек.",
        simpleNextTitle: "Следующая награда",
        simpleNextNote: "Награда не чаще 1 раза в минуту на пользователя.",
        simpleNextReady: "Готово",
        simpleNextWait: "Жди",
        totalEconomy: "Общая экономика",
        usersCount: "Пользователей",
        ctaEarn: "Заработок",
        ctaFriends: "Друзья",
        ctaWallet: "Кошелек",
        prefModeTitle: "Режим",
        prefModeNote: "Обыч / PRO",
        modeSimple: "Обыч",
        modePro: "PRO",
        ttLang: "Язык",
        ttMode: "Режим",
        ttTheme: "Тема",
        toastProOn: "Режим PRO включен",
        toastProOff: "Режим Обыч включен",
        toastDark: "Темная тема",
        toastLight: "Светлая тема",
        settingsTitle: "Настройки",
        settingsNote: "Подсказки и поведение интерфейса. (Режим и тема в верхней панели.)",
        settingsAboutTitle: "О приложении",
        settingsAboutNote: "Открывай через бота, чтобы видеть свой ранг и реф-ссылку.",
        settingsHint: "Подсказка: открывай приложение через бота, тогда подтянется твой Telegram ID, ранг и реф-ссылка.",
        prefThemeTitle: "Тема",
        prefThemeNote: "Авто / Светлая / Темная",
        themeAuto: "Авто",
        themeLight: "Светлая",
        themeDark: "Темная",
        walletTitle: "Кошелек",
        walletNote: "Подключи кошелек через TON Connect.",
        walletStatusDisconnected: "Кошелек не подключен",
        walletStatusConnected: "Подключен: {addr}",
        walletStatusUnavailable: "TON Connect недоступен в этой среде",
        prefFocusTitle: "Фокус-режим",
        prefFocusNote: "Скрывает вторичные подсказки и лишние блоки.",
        prefAnimTitle: "Плавная анимация",
        prefAnimNote: "Мягкие переходы между вкладками и карточками.",
        prefRoadmapTitle: "Показывать roadmap",
        prefRoadmapNote: "Открывать roadmap сразу по умолчанию.",
        prefPlannedTitle: "Показывать плановые модули",
        prefPlannedNote: "Скрывает карточки, которые еще не вышли.",
        homeTopTitle: "Топ сейчас",
        homeTopNote: "Лидеры мотивируют заходить чаще.",
        topTitle: "Лидерборд",
        topNote: "Кто собрал больше всего монет.",
        topNotePreview: "Фильтр пока в preview режиме: используется текущий общий рейтинг.",
        rangeAll: "Все время",
        range7d: "7 дней",
        range24h: "24 часа",
        yourRow: "Ты: #{rank} из {total}",
        yourRowGuest: "Открой через бота, чтобы видеть свой ранг.",
        friendsTitle: "Пригласи друзей",
        friendsNote: "Делись ссылкой и получай больше монет.",
        friendsSimpleTitle: "Приглашай = больше монет",
        friendsSimpleNote: "Бонус за друга + комиссия с его начислений.",
        copy: "Копировать",
        copied: "Ссылка скопирована",
        copyFail: "Не удалось скопировать",
        invited: "Приглашено",
        refIncome: "Доход с рефералов",
        topReferrers: "Топ рефереров",
        earnTitle: "Заработок и траты",
        earnNote: "Задания, бусты и магазин без перегруза.",
        taskChatTitle: "Дневной чат-стрик",
        taskChatMeta: "Пиши в чатах, чтобы держать стрик активным.",
        taskChatBadge: "Активно",
        taskFriendsTitle: "Пригласи друзей",
        taskFriendsMeta: "Бонус за друга и постоянная комиссия.",
        taskFriendsBadge: "Главный цикл",
        boostFreeTitle: "Бесплатный буст",
        boostFreeMeta: "Временный x2 множитель активности (план).",
        boostFreeBadge: "Скоро",
        shopTitle: "Магазин за монеты",
        shopMeta: "Трать TGM на перки и сезонные активности.",
        shopBadge: "Roadmap",
        roadmapSummary: "Roadmap (раскрыть)",
        statusDone: "готово",
        statusProgress: "в работе",
        statusPlanned: "запланировано",
        noData: "Пока данных нет",
        support: "Поддержка: @{bot_username}",
      },
      en: {
        title: "TGM Coin",
        subtitle: "Your balance, leaderboard and growth",
        tabHome: "Balance",
        tabTop: "Top",
        tabFriends: "Friends",
        tabEarn: "Earn",
        tabSettings: "Settings",
        heroTitle: "Your Balance",
        todayIncome: "Today",
        streak: "Streak",
        daysSuffix: "d",
        simpleHowTitle: "How to earn",
        simpleHowNote: "Write in the chat and get coins. No buttons, no thinking.",
        simpleHowSteps: "1) Write a message in chat (once per minute).\\n2) Keep your streak daily.\\n3) In the app: shop, boosts, referrals, wallet.",
        simpleNextTitle: "Next reward",
        simpleNextNote: "Max 1 reward per minute per user.",
        simpleNextReady: "Ready",
        simpleNextWait: "Wait",
        totalEconomy: "Total economy",
        usersCount: "Users",
        ctaEarn: "Earn",
        ctaFriends: "Friends",
        ctaWallet: "Wallet",
        prefModeTitle: "Mode",
        prefModeNote: "Simple / PRO",
        modeSimple: "Simple",
        modePro: "PRO",
        ttLang: "Language",
        ttMode: "Mode",
        ttTheme: "Theme",
        toastProOn: "PRO mode enabled",
        toastProOff: "Simple mode enabled",
        toastDark: "Dark theme",
        toastLight: "Light theme",
        settingsTitle: "Settings",
        settingsNote: "Hints and UI behavior. (Mode and theme are in the top bar.)",
        settingsAboutTitle: "About",
        settingsAboutNote: "Open via bot to show your rank and referral link.",
        settingsHint: "Tip: open the app from the bot so it can read your Telegram user id, rank and referral link.",
        prefThemeTitle: "Theme",
        prefThemeNote: "Auto / Light / Dark",
        themeAuto: "Auto",
        themeLight: "Light",
        themeDark: "Dark",
        walletTitle: "Wallet",
        walletNote: "Connect wallet via TON Connect.",
        walletStatusDisconnected: "Wallet not connected",
        walletStatusConnected: "Connected: {addr}",
        walletStatusUnavailable: "TON Connect unavailable in this environment",
        prefFocusTitle: "Focus mode",
        prefFocusNote: "Hide secondary hints and non-critical blocks.",
        prefAnimTitle: "Smooth motion",
        prefAnimNote: "Soft transitions between tabs and cards.",
        prefRoadmapTitle: "Show roadmap",
        prefRoadmapNote: "Expand roadmap by default.",
        prefPlannedTitle: "Show planned modules",
        prefPlannedNote: "Hide cards that are not released yet.",
        homeTopTitle: "Top right now",
        homeTopNote: "Leaders increase session frequency.",
        topTitle: "Leaderboard",
        topNote: "Who collected the most coins.",
        topNotePreview: "Range filter is in preview mode and currently uses all-time ranking.",
        rangeAll: "All time",
        range7d: "7 days",
        range24h: "24 hours",
        yourRow: "You: #{rank} of {total}",
        yourRowGuest: "Open via bot to show your personal rank.",
        friendsTitle: "Invite friends",
        friendsNote: "Share your link and grow your balance.",
        friendsSimpleTitle: "Invite = more coins",
        friendsSimpleNote: "Friend bonus plus commission from their rewards.",
        copy: "Copy",
        copied: "Link copied",
        copyFail: "Copy failed",
        invited: "Invited",
        refIncome: "Referral income",
        topReferrers: "Top referrers",
        earnTitle: "Earn and spend",
        earnNote: "Tasks, boosts and shop without overload.",
        taskChatTitle: "Daily chat streak",
        taskChatMeta: "Write in chats to keep streak alive.",
        taskChatBadge: "Active",
        taskFriendsTitle: "Invite friends",
        taskFriendsMeta: "Friend bonus and permanent commission.",
        taskFriendsBadge: "Core loop",
        boostFreeTitle: "Free boost",
        boostFreeMeta: "Temporary x2 activity multiplier (planned).",
        boostFreeBadge: "Soon",
        shopTitle: "Coin shop",
        shopMeta: "Spend TGM on perks and seasonal campaigns.",
        shopBadge: "Roadmap",
        roadmapSummary: "Roadmap (expand)",
        statusDone: "done",
        statusProgress: "in progress",
        statusPlanned: "planned",
        noData: "No data yet",
        support: "Support: @{bot_username}",
      }
    };

    const state = {
      lang: "__INITIAL_LANG__",
      tab: "home",
      topRange: "all",
      userId: 0,
      profile: null,
      topUsers: [],
      topRefs: [],
      roadmap: [],
      botUsername: "__BOT_USERNAME__",
      prefs: {
        mode: "simple",
        theme: "system",
        focus: false,
        animate: true,
        roadmapOpen: false,
        showPlanned: true,
      }
    };

    function esc(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function formatName(item) {
      if (!item) return "Guest";
      if (item.username) return "@" + item.username;
      if (item.first_name) return item.first_name;
      return "id:" + item.user_id;
    }

    function setTab(tab) {
      state.tab = tab;
      ["home", "top", "friends", "earn", "settings"].forEach((name) => {
        document.getElementById("tab-" + name).classList.toggle("active", tab === name);
        document.getElementById("panel-" + name).classList.toggle("active", tab === name);
      });
      updateTabIndicator();
    }

    function setText(id, value) {
      const node = document.getElementById(id);
      if (node) node.textContent = value;
    }

    function hapticLight() {
      try {
        const tg = window.Telegram && window.Telegram.WebApp;
        const hf = tg && tg.HapticFeedback;
        if (hf && typeof hf.impactOccurred === "function") {
          hf.impactOccurred("light");
        }
      } catch (_) {}
    }

    function prefsStorageKey() {
      return "tgm_miniapp_prefs_v2";
    }

    function loadPrefs() {
      try {
        const raw = localStorage.getItem(prefsStorageKey());
        if (!raw) return;
        const parsed = JSON.parse(raw);
        state.prefs = {
          mode: parsed.mode === "pro" ? "pro" : "simple",
          theme: parsed.theme === "light" || parsed.theme === "dark" ? parsed.theme : "system",
          focus: !!parsed.focus,
          animate: parsed.animate !== false,
          roadmapOpen: !!parsed.roadmapOpen,
          showPlanned: parsed.showPlanned !== false,
        };
      } catch (_) {}
    }

    function savePrefs() {
      try {
        localStorage.setItem(prefsStorageKey(), JSON.stringify(state.prefs));
      } catch (_) {}
    }

    function applyTheme() {
      const prefersDark = !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
      const mode = state.prefs.theme || "system";
      const useDark = mode === "dark" || (mode === "system" && prefersDark);
      document.body.classList.toggle("theme-dark", useDark);
      const toggle = document.getElementById("theme-toggle");
      if (toggle) {
        toggle.textContent = useDark ? "☾" : "☀";
      }
    }

    function applyMode() {
      const mode = state.prefs.mode === "pro" ? "pro" : "simple";
      document.body.classList.toggle("mode-pro", mode === "pro");
      document.body.classList.toggle("mode-simple", mode !== "pro");
    }

    function applyPrefs() {
      applyMode();
      applyTheme();
      updateHeaderControls();
      updateTabIndicator();
      document.body.classList.toggle("util-no-motion", !state.prefs.animate);
      [
        "home-top-note",
        "support-line",
        "support-line-settings",
        "top-note",
        "friends-note",
        "earn-note",
        "settings-note",
      ].forEach((id) => {
        const node = document.getElementById(id);
        if (node) node.classList.toggle("util-hidden", state.prefs.focus);
      });

      const details = document.querySelector("#panel-earn details");
      if (details) details.open = !!state.prefs.roadmapOpen;

      document.querySelectorAll(".planned-item").forEach((node) => {
        node.classList.toggle("util-hidden", !state.prefs.showPlanned);
      });

      const focusToggle = document.getElementById("toggle-focus");
      const animToggle = document.getElementById("toggle-animate");
      const roadmapToggle = document.getElementById("toggle-roadmap");
      const plannedToggle = document.getElementById("toggle-planned");
      if (focusToggle) focusToggle.checked = !!state.prefs.focus;
      if (animToggle) animToggle.checked = !!state.prefs.animate;
      if (roadmapToggle) roadmapToggle.checked = !!state.prefs.roadmapOpen;
      if (plannedToggle) plannedToggle.checked = !!state.prefs.showPlanned;
    }

    function setMode(mode) {
      state.prefs.mode = mode === "pro" ? "pro" : "simple";
      savePrefs();
      applyPrefs();
      if (state.prefs.mode !== "pro" && (state.tab === "top" || state.tab === "settings")) {
        setTab("home");
      }
      const t = I18N[state.lang];
      showToast(state.prefs.mode === "pro" ? t.toastProOn : t.toastProOff);
    }

    function setTheme(mode) {
      state.prefs.theme = mode === "light" || mode === "dark" ? mode : "system";
      savePrefs();
      applyPrefs();
      const t = I18N[state.lang];
      showToast(state.prefs.theme === "dark" ? t.toastDark : t.toastLight);
    }

    function updateHeaderControls() {
      const t = I18N[state.lang];
      const btnLang = document.getElementById("btn-lang");
      if (btnLang) {
        btnLang.textContent = state.lang === "en" ? "EN" : "RU";
        btnLang.title = t.ttLang;
      }
      const btnMode = document.getElementById("btn-mode");
      if (btnMode) {
        btnMode.textContent = state.prefs.mode === "pro" ? t.modePro : t.modeSimple;
        btnMode.title = t.ttMode;
      }
      const themeBtn = document.getElementById("theme-toggle");
      if (themeBtn) themeBtn.title = t.ttTheme;
    }

    function updateTabIndicator() {
      const bar = document.querySelector(".tabs");
      const ind = bar && bar.querySelector(".tab-indicator");
      const active = bar && bar.querySelector(".tab.active");
      if (!bar || !ind || !active) return;
      const barRect = bar.getBoundingClientRect();
      const rect = active.getBoundingClientRect();
      const x = Math.max(0, rect.left - barRect.left);
      ind.style.width = Math.max(44, rect.width) + "px";
      ind.style.transform = `translateX(${x}px)`;
    }

    let toastTimer = null;
    function showToast(text) {
      const node = document.getElementById("toast");
      if (!node) return;
      node.textContent = String(text || "");
      node.classList.add("show");
      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(() => node.classList.remove("show"), 1400);
    }

    function setTopRange(range) {
      state.topRange = range;
      const map = {
        all: "top-range-all",
        "7d": "top-range-7d",
        "24h": "top-range-24h",
      };
      Object.values(map).forEach((id) => {
        const node = document.getElementById(id);
        if (!node) return;
        node.classList.toggle("active", id === map[range]);
      });
      render();
    }

    function renderList(containerId, rows, buildScore) {
      const t = I18N[state.lang];
      const node = document.getElementById(containerId);
      if (!node) return;
      if (!rows.length) {
        node.innerHTML = `<p class="hint">${esc(t.noData)}</p>`;
        return;
      }
      node.innerHTML = rows.map((item, idx) => {
        const isYou = state.profile && state.profile.user_id === item.user_id;
        return `
          <div class="list-row" style="${isYou ? "background:#f0f9ff;border-radius:10px;" : ""}">
            <div class="rank">${idx + 1}</div>
            <div class="who">${esc(formatName(item))}</div>
            <div class="score">${esc(buildScore(item))}</div>
          </div>
        `;
      }).join("");
    }

    function roadmapStatus(status, t) {
      if (status === "done") return t.statusDone;
      if (status === "in_progress") return t.statusProgress;
      return t.statusPlanned;
    }

    function renderRoadmap() {
      const t = I18N[state.lang];
      const node = document.getElementById("roadmap-list");
      if (!node) return;
      if (!state.roadmap.length) {
        node.innerHTML = `<p class="hint">${esc(t.noData)}</p>`;
        return;
      }
      node.innerHTML = state.roadmap.map((item) => {
        const title = state.lang === "en" ? (item.title_en || item.title_ru || "") : (item.title_ru || item.title_en || "");
        const desc = state.lang === "en" ? (item.description_en || item.description_ru || "") : (item.description_ru || item.description_en || "");
        return `
          <div class="road-item">
            <div class="road-phase">${esc(item.phase || "")} · ${esc(roadmapStatus(item.status, t))}</div>
            <p class="road-title">${esc(title)}</p>
            <p class="road-desc">${esc(desc)}</p>
          </div>
        `;
      }).join("");
    }

    function referralLink() {
      if (!state.profile || !state.profile.user_id) return "";
      return `https://t.me/${state.botUsername}?start=ref_${state.profile.user_id}`;
    }

    let tonUi = null;
    function initTonConnect() {
      const root = document.getElementById("ton-connect");
      if (!root) return;
      const t = I18N[state.lang];
      function setStatus(text) {
        const node = document.getElementById("wallet-status");
        if (node) node.textContent = text || "";
      }
      try {
        const TC = window.TonConnectUI;
        const TonConnectUIClass = TC && (TC.TonConnectUI || TC.default || TC);
        if (!TonConnectUIClass) {
          setStatus(t.walletStatusUnavailable);
          return;
        }
        tonUi = new TonConnectUIClass({
          manifestUrl: `${window.location.origin}/tonconnect-manifest.json`,
          buttonRootId: "ton-connect",
        });
        setStatus(t.walletStatusDisconnected);
        if (typeof tonUi.onStatusChange === "function") {
          tonUi.onStatusChange((wallet) => {
            if (wallet && wallet.account && wallet.account.address) {
              const addr = String(wallet.account.address);
              setStatus(t.walletStatusConnected.replace("{addr}", addr.slice(0, 6) + "…" + addr.slice(-6)));
            } else {
              setStatus(t.walletStatusDisconnected);
            }
          });
        }
      } catch (_) {
        setStatus(t.walletStatusUnavailable);
      }
    }

    function render() {
      const t = I18N[state.lang];
      const p = state.profile || {
        user_id: 0,
        username: "",
        first_name: "",
        coins: 0,
        rank: null,
        total_users: 0,
        total_coins: 0,
        referrals_total: 0,
        commission_total: 0,
      };

      setText("title", t.title);
      setText("subtitle", t.subtitle);
      setText("tab-home-label", t.tabHome);
      setText("tab-top-label", t.tabTop);
      setText("tab-friends-label", t.tabFriends);
      setText("tab-earn-label", t.tabEarn);
      setText("tab-settings-label", t.tabSettings);
      setText("home-hero-title", t.heroTitle);
      setText("label-today-income", t.todayIncome);
      setText("label-streak", t.streak);
      setText("label-days-suffix", t.daysSuffix);
      setText("label-total-economy", t.totalEconomy);
      setText("label-total-users", t.usersCount);
      setText("cta-earn", t.ctaEarn);
      setText("cta-friends", t.ctaFriends);
      setText("cta-wallet", t.ctaWallet);
      setText("simple-how-title", t.simpleHowTitle);
      setText("simple-how-note", t.simpleHowNote);
      setText("simple-how-steps", t.simpleHowSteps);
      setText("simple-next-title", t.simpleNextTitle);
      setText("simple-next-note", t.simpleNextNote);
      setText("pref-focus-title", t.prefFocusTitle);
      setText("pref-focus-note", t.prefFocusNote);
      setText("pref-anim-title", t.prefAnimTitle);
      setText("pref-anim-note", t.prefAnimNote);
      setText("pref-roadmap-title", t.prefRoadmapTitle);
      setText("pref-roadmap-note", t.prefRoadmapNote);
      updateHeaderControls();
      setText("pref-planned-title", t.prefPlannedTitle);
      setText("pref-planned-note", t.prefPlannedNote);
      setText("home-top-title", t.homeTopTitle);
      setText("home-top-note", t.homeTopNote);
      setText("top-title", t.topTitle);
      setText("top-note", state.topRange === "all" ? t.topNote : t.topNotePreview);
      setText("top-range-all", t.rangeAll);
      setText("top-range-7d", t.range7d);
      setText("top-range-24h", t.range24h);
      setText("friends-title", t.friendsTitle);
      setText("friends-note", t.friendsNote);
      setText("friends-simple-title", t.friendsSimpleTitle);
      setText("friends-simple-note", t.friendsSimpleNote);
      setText("copy-ref", t.copy);
      setText("friends-total-label", t.invited);
      setText("friends-income-label", t.refIncome);
      setText("friends-top-title", t.topReferrers);
      setText("earn-title", t.earnTitle);
      setText("earn-note", t.earnNote);
      setText("settings-title", t.settingsTitle);
      setText("settings-note", t.settingsNote);
      setText("settings-about-title", t.settingsAboutTitle);
      setText("settings-about-note", t.settingsAboutNote);
      setText("settings-hint", t.settingsHint);
      setText("wallet-title", t.walletTitle);
      setText("wallet-note", t.walletNote);
      setText("task-chat-title", t.taskChatTitle);
      setText("task-chat-meta", t.taskChatMeta);
      setText("task-chat-badge", t.taskChatBadge);
      setText("task-friends-title", t.taskFriendsTitle);
      setText("task-friends-meta", t.taskFriendsMeta);
      setText("task-friends-badge", t.taskFriendsBadge);
      setText("boost-free-title", t.boostFreeTitle);
      setText("boost-free-meta", t.boostFreeMeta);
      setText("boost-free-badge", t.boostFreeBadge);
      setText("shop-title", t.shopTitle);
      setText("shop-meta", t.shopMeta);
      setText("shop-badge", t.shopBadge);
      setText("roadmap-summary", t.roadmapSummary);
      setText("home-coins", String(p.coins || 0));
      setText("home-today-income", String(p.today_income || 0));
      setText("home-streak-days", String(p.streak_days || 0));
      const nextSec = Math.max(0, Number(p.next_reward_seconds || 0));
      setText("simple-next-seconds", String(nextSec));
      setText("simple-next-status", nextSec <= 0 ? t.simpleNextReady : t.simpleNextWait);
      setText("home-total-coins", String(p.total_coins || 0));
      setText("home-total-users", String(p.total_users || 0));
      setText("home-name", formatName(p));
      setText("home-rank-hero", p.rank ? `#${p.rank}` : "#-");
      setText("friends-total", String(p.referrals_total || 0));
      setText("friends-income", String(p.commission_total || 0));
      setText("support-line", t.support.replace("{bot_username}", state.botUsername));
      setText("support-line-settings", t.support.replace("{bot_username}", state.botUsername));

      const youText = p.rank
        ? t.yourRow.replace("{rank}", String(p.rank)).replace("{total}", String(p.total_users || 0))
        : t.yourRowGuest;
      setText("you-row", youText);

      const refInput = document.getElementById("ref-link");
      if (refInput) {
        refInput.value = referralLink();
      }
      setText("copy-hint", "");

      const themeBtn = document.getElementById("theme-toggle");
      if (themeBtn) themeBtn.title = t.ttTheme;
      const modeBtn = document.getElementById("btn-mode");
      if (modeBtn) modeBtn.title = t.ttMode;
      const langBtn = document.getElementById("btn-lang");
      if (langBtn) langBtn.title = t.ttLang;

      renderList("home-top-list", state.topUsers.slice(0, 5), (item) => `${item.coins} TGM`);
      const topRows = state.topRange === "all" ? state.topUsers : state.topUsers.slice(0, 30);
      renderList("top-list", topRows, (item) => `${item.coins} TGM`);
      renderList(
        "friends-top-list",
        state.topRefs.slice(0, 20),
        (item) => `${item.referrals_total} / ${item.commission_total}`
      );
      renderRoadmap();
      applyPrefs();
      initTonConnect();
    }

    function resolveUserId() {
      try {
        const tg = window.Telegram && window.Telegram.WebApp;
        const tgUid = Number(tg?.initDataUnsafe?.user?.id || 0);
        if (tgUid > 0) return tgUid;
      } catch (_) {}
      const query = new URLSearchParams(window.location.search);
      const queryUid = Number(query.get("uid") || 0);
      if (queryUid > 0) return queryUid;
      return 0;
    }

    async function loadData() {
      state.userId = resolveUserId();
      const [profileResp, topUsersResp, topRefsResp, roadmapResp] = await Promise.all([
        fetch(`/api/user-overview?user_id=${state.userId}`),
        fetch("/api/top-users?limit=100"),
        fetch("/api/top-referrers?limit=100"),
        fetch("/api/roadmap"),
      ]);

      const profileData = await profileResp.json();
      const usersData = await topUsersResp.json();
      const refsData = await topRefsResp.json();
      const roadmapData = await roadmapResp.json();

      state.profile = profileData.item || null;
      state.topUsers = Array.isArray(usersData.items) ? usersData.items : [];
      state.topRefs = Array.isArray(refsData.items) ? refsData.items : [];
      state.roadmap = Array.isArray(roadmapData.items) ? roadmapData.items : [];
      render();
    }

    document.getElementById("btn-lang").addEventListener("click", () => {
      hapticLight();
      state.lang = state.lang === "en" ? "ru" : "en";
      render();
    });

    document.getElementById("tab-home").addEventListener("click", () => setTab("home"));
    document.getElementById("tab-top").addEventListener("click", () => setTab("top"));
    document.getElementById("tab-friends").addEventListener("click", () => setTab("friends"));
    document.getElementById("tab-earn").addEventListener("click", () => setTab("earn"));
    document.getElementById("tab-settings").addEventListener("click", () => setTab("settings"));
    document.getElementById("cta-earn").addEventListener("click", () => setTab("earn"));
    document.getElementById("cta-friends").addEventListener("click", () => setTab("friends"));
    document.getElementById("cta-wallet").addEventListener("click", () => setTab("earn"));
    document.getElementById("top-range-all").addEventListener("click", () => setTopRange("all"));
    document.getElementById("top-range-7d").addEventListener("click", () => setTopRange("7d"));
    document.getElementById("top-range-24h").addEventListener("click", () => setTopRange("24h"));

    document.getElementById("toggle-focus").addEventListener("change", (e) => {
      state.prefs.focus = !!e.target.checked;
      savePrefs();
      applyPrefs();
    });
    document.getElementById("toggle-animate").addEventListener("change", (e) => {
      state.prefs.animate = !!e.target.checked;
      savePrefs();
      applyPrefs();
    });
    document.getElementById("toggle-roadmap").addEventListener("change", (e) => {
      state.prefs.roadmapOpen = !!e.target.checked;
      savePrefs();
      applyPrefs();
    });
    document.getElementById("toggle-planned").addEventListener("change", (e) => {
      state.prefs.showPlanned = !!e.target.checked;
      savePrefs();
      applyPrefs();
    });

    document.getElementById("btn-mode").addEventListener("click", () => {
      hapticLight();
      setMode(state.prefs.mode === "pro" ? "simple" : "pro");
    });
    document.getElementById("theme-toggle").addEventListener("click", () => {
      hapticLight();
      const prefersDark = !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
      const current = state.prefs.theme === "light" || state.prefs.theme === "dark"
        ? state.prefs.theme
        : (prefersDark ? "dark" : "light");
      setTheme(current === "dark" ? "light" : "dark");
    });

    document.getElementById("copy-ref").addEventListener("click", async () => {
      const t = I18N[state.lang];
      const val = document.getElementById("ref-link").value || "";
      if (!val) {
        setText("copy-hint", t.copyFail);
        return;
      }
      try {
        await navigator.clipboard.writeText(val);
        setText("copy-hint", t.copied);
      } catch (_) {
        setText("copy-hint", t.copyFail);
      }
    });

    try {
      if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
      }
    } catch (_) {}

    window.addEventListener("resize", updateTabIndicator);

    setTab("home");
    loadPrefs();
    setTopRange("all");
    loadData().catch((err) => {
      console.error(err);
      render();
    });
  </script>
</body>
</html>
""".replace("__INITIAL_LANG__", initial_lang).replace("__HTML_LANG__", initial_lang).replace("__BOT_USERNAME__", MINIAPP_BOT_USERNAME)


@app.get("/assets/tgm.svg")
def asset_tgm_svg():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="#0a84ff"/>
      <stop offset="1" stop-color="#34d399"/>
    </linearGradient>
  </defs>
  <rect x="16" y="16" width="224" height="224" rx="56" fill="#0f172a"/>
  <rect x="28" y="28" width="200" height="200" rx="50" fill="url(#g)" opacity="0.18"/>
  <path d="M64 88h128v24H140v92h-24v-92H64V88z" fill="#e5e7eb"/>
  <path d="M64 88h128v10H64V88z" fill="#e5e7eb" opacity="0.45"/>
</svg>"""
    return Response(svg, mimetype="image/svg+xml")


@app.get("/tonconnect-manifest.json")
def tonconnect_manifest():
    base = request.host_url.rstrip("/")
    manifest = {
        "url": base,
        "name": "TGM Coin",
        "iconUrl": f"{base}/assets/tgm.svg",
    }
    return jsonify(manifest)


@app.get("/api/users")
def api_users():
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "coins_desc")
    limit = to_int(request.args.get("limit", "100"), 100)
    offset = to_int(request.args.get("offset", "0"), 0)
    limit = min(max(limit, 1), PAGE_SIZE_MAX)
    offset = max(offset, 0)

    total = storage.count_users(search=q)
    users = storage.list_users(limit=limit, offset=offset, search=q, sort=sort)
    return jsonify({"total": total, "limit": limit, "offset": offset, "items": users})


@app.get("/api/chats")
def api_chats():
    q = request.args.get("q", "").strip()
    limit = to_int(request.args.get("limit", "100"), 100)
    offset = to_int(request.args.get("offset", "0"), 0)
    limit = min(max(limit, 1), PAGE_SIZE_MAX)
    offset = max(offset, 0)

    total = storage.count_chats(search=q)
    chats = storage.list_chats(limit=limit, offset=offset, search=q)
    return jsonify({"total": total, "limit": limit, "offset": offset, "items": chats})


@app.get("/api/features")
def api_features():
    return jsonify({"items": storage.list_feature_flags()})


@app.get("/api/top-users")
def api_top_users():
    limit = to_int(request.args.get("limit", "100"), 100)
    limit = min(max(limit, 1), 500)
    return jsonify({"items": storage.top_users(limit=limit)})


@app.get("/api/user-overview")
def api_user_overview():
    user_id = to_int(request.args.get("user_id", "0"), 0)
    if user_id <= 0:
        return jsonify(
            {
                "item": {
                    "user_id": 0,
                    "username": "",
                    "first_name": "",
                    "coins": 0,
                    "rank": None,
                    "total_users": storage.count_users(),
                    "total_coins": storage.get_total_coins(),
                    "referrals_total": 0,
                    "rewarded_referrals": 0,
                    "commission_total": 0,
                }
            }
        )
    return jsonify({"item": storage.get_user_overview(user_id=user_id)})


@app.get("/health")
def health():
    return jsonify({"ok": True, "ts": int(time.time())})


@app.get("/api/top-admins")
def api_top_admins():
    limit = to_int(request.args.get("limit", "100"), 100)
    limit = min(max(limit, 1), 500)
    return jsonify({"items": storage.top_admins(limit=limit)})


@app.get("/api/top-referrers")
def api_top_referrers():
    limit = to_int(request.args.get("limit", "100"), 100)
    limit = min(max(limit, 1), 500)
    return jsonify({"items": storage.top_referrers(limit=limit)})


@app.get("/api/top-income")
def api_top_income():
    limit = to_int(request.args.get("limit", "100"), 100)
    days = to_int(request.args.get("days", "5"), 5)
    limit = min(max(limit, 1), 500)
    days = min(max(days, 1), 30)
    return jsonify({"items": storage.top_income_last_days(days=days, limit=limit)})


@app.get("/api/income-timeline")
def api_income_timeline():
    days = to_int(request.args.get("days", "7"), 7)
    days = min(max(days, 1), 60)
    return jsonify({"items": storage.income_timeline(days=days)})


@app.get("/api/suspicious-users")
def api_suspicious_users():
    limit = to_int(request.args.get("limit", "100"), 100)
    days = to_int(request.args.get("days", "5"), 5)
    min_income = to_int(request.args.get("min_income", "5000"), 5000)
    min_transfer_out = to_int(request.args.get("min_transfer_out", "3000"), 3000)
    limit = min(max(limit, 1), 500)
    days = min(max(days, 1), 30)
    return jsonify(
        {
            "items": storage.suspicious_users_report(
                days=days,
                min_income=min_income,
                min_transfer_out=min_transfer_out,
                limit=limit,
            )
        }
    )


@app.get("/api/roadmap")
def api_roadmap():
    return jsonify({"items": ROADMAP_ITEMS})


@app.get("/api/broadcasts")
def api_broadcasts():
    limit = to_int(request.args.get("limit", "20"), 20)
    limit = min(max(limit, 1), 500)
    return jsonify({"items": storage.list_broadcast_logs(limit=limit)})


@app.post("/chat-fireworks")
def chat_fireworks_toggle():
    chat_id = to_int(request.form.get("chat_id"), 0)
    enabled = request.form.get("enabled", "0") == "1"
    if chat_id != 0:
        storage.set_chat_fireworks_enabled(chat_id=chat_id, enabled=enabled)

    next_url = safe_next_url(request.form.get("next", "/"))
    return redirect(next_url, code=303)


@app.post("/feature-flag")
def feature_flag_toggle():
    key = (request.form.get("key") or "").strip()
    enabled = request.form.get("enabled", "0") == "1"
    if key:
        storage.set_feature_flag(key=key, enabled=enabled)

    next_url = safe_next_url(request.form.get("next", "/"))
    return redirect(next_url, code=303)


@app.post("/user-activation")
def user_activation_toggle():
    user_id = to_int(request.form.get("user_id"), 0)
    enabled = request.form.get("enabled", "0") == "1"
    next_url = safe_next_url(request.form.get("next", "/"))
    ui_lang = normalize_lang(request.form.get("lang") or lang_from_next(next_url))

    if user_id <= 0:
        return redirect(append_notice(next_url, admin_text(ui_lang, "notice_invalid_user_id")), code=303)

    storage.set_user_activated(user_id=user_id, enabled=enabled)
    status = admin_text(ui_lang, "notice_enabled") if enabled else admin_text(ui_lang, "notice_disabled")
    return redirect(
        append_notice(next_url, admin_text(ui_lang, "notice_broadcast_user", user_id=user_id, status=status)),
        code=303,
    )


@app.post("/broadcast")
def broadcast_send():
    next_url = safe_next_url(request.form.get("next", "/"))
    ui_lang = normalize_lang(request.form.get("lang") or lang_from_next(next_url))
    text = (request.form.get("text") or "").strip()
    activated_only = request.form.get("activated_only", "0") == "1"

    if not text:
        return redirect(append_notice(next_url, admin_text(ui_lang, "notice_broadcast_empty")), code=303)

    if not storage.is_feature_enabled(FEATURE_BROADCASTS, default=True):
        return redirect(append_notice(next_url, admin_text(ui_lang, "notice_feature_disabled")), code=303)

    token = os.getenv("TG_BOT_TOKEN", "").strip()
    if not token:
        return redirect(append_notice(next_url, admin_text(ui_lang, "notice_missing_token")), code=303)

    targets = storage.list_broadcast_targets(activated_only=activated_only, limit=50000)
    sent_count = 0
    failed_count = 0

    for user_id in targets:
        ok, _ = send_telegram_text(token=token, chat_id=user_id, text=text)
        if ok:
            sent_count += 1
        else:
            failed_count += 1
        if BROADCAST_THROTTLE_SECONDS > 0:
            time.sleep(BROADCAST_THROTTLE_SECONDS)

    storage.log_broadcast(
        text=text,
        activated_only=activated_only,
        sent_count=sent_count,
        failed_count=failed_count,
    )
    return redirect(
        append_notice(
            next_url,
            admin_text(
                ui_lang,
                "notice_broadcast_done",
                targets=len(targets),
                sent=sent_count,
                failed=failed_count,
            ),
        ),
        code=303,
    )


def main() -> None:
    storage.init_db()
    app.run(host=ADMIN_UI_HOST, port=ADMIN_UI_PORT, debug=False)


if __name__ == "__main__":
    main()
