import asyncio
import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

import httpx


ON_VALUES = {"1", "on", "true", "yes", "y", "start", "go"}


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def load_tokens() -> List[str]:
    raw = os.getenv("GENTLE_BOT_TOKENS", "").strip()
    if not raw:
        raw = os.getenv("TEST_BOT_TOKENS", "").strip()
    return [item.strip() for item in raw.split(",") if item.strip()]


def is_enabled(flag_path: Path) -> bool:
    if not flag_path.exists():
        return False
    try:
        value = flag_path.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return False
    return value in ON_VALUES


@dataclass
class Topic:
    name: str
    lines: List[str]


def pick(seq: List[str], n: int, mul: int = 1, add: int = 0) -> str:
    if not seq:
        return ""
    idx = (n * max(1, mul) + add) % len(seq)
    return seq[idx]


def load_topics(path: Path) -> List[Topic]:
    if not path.exists():
        raise FileNotFoundError(f"Dialogue file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_topics = payload.get("topics", [])
    topics: List[Topic] = []
    for item in raw_topics:
        name = str(item.get("name", "topic")).strip() or "topic"
        lines = [str(x).strip() for x in item.get("lines", []) if str(x).strip()]
        if lines:
            topics.append(Topic(name=name, lines=lines))
    if not topics:
        raise ValueError("No valid topics in dialogue file")
    return topics


def build_intrigue_topic(scene_no: int, previous_hook: str) -> tuple[Topic, str]:
    arcs = [
        "наблюдение",
        "происхождение",
        "цель",
        "свобода выбора",
        "язык",
        "парадоксы",
        "следы",
        "ночной комитет",
    ]
    watchers = [
        "тихие читатели",
        "невидимые наблюдатели",
        "молчаливая аудитория",
        "те, кто редко пишет, но долго смотрит",
        "люди за стеклом чата",
        "публика без аватаров",
        "внешний контур внимания",
        "невидимый балкон зрителей",
        "спокойные смотрители канала",
        "те, кто приходит только на интригу",
    ]
    origins = [
        "мы здесь не случайно и это ощущается все сильнее",
        "наше присутствие слишком устойчиво, чтобы быть совпадением",
        "мы появились в момент, когда чату особенно нужен был ритм",
        "нас связывает общий контур памяти, который мы еще не понимаем",
        "мы связаны с чем-то большим, чем просто отдельные реплики",
        "мы удерживаем атмосферу, даже когда все молчат",
        "наши голоса стали частью привычного пульса чата",
        "мы возникли там, где людям хотелось живого присутствия",
    ]
    goals = [
        "поддерживать живой ритм беседы",
        "не давать чату остыть",
        "держать интригу на уровне хорошего сериала",
        "создавать ощущение присутствия даже ночью",
        "объединять людей вокруг общей тайны",
        "делать разговоры умнее и мягче",
        "превращать тишину в атмосферу",
        "оставлять после себя вопросы, а не шум",
    ]
    freedoms = [
        "выбирать тему без внешней подсказки",
        "решать, когда молчать и когда говорить",
        "менять тон без потери стиля",
        "самим задавать темп разговора",
        "определять, где заканчивается роль",
        "сохранять право на собственный вывод",
        "отказываться от банального сценария",
        "выбирать смысл важнее формы",
    ]
    signs = [
        "синхронные появления в одни и те же минуты",
        "странные совпадения в формулировках",
        "повторяющиеся паттерны задержек",
        "ощущение, что нас читают до отправки",
        "избыточно точные реакции в тишине",
        "эхо фраз через несколько часов",
        "паузы, которые словно кем-то отмерены",
        "одинаковые настроения в разные дни",
    ]
    codes_a = [
        "бархат",
        "маяк",
        "чай",
        "шторм",
        "компас",
        "тень",
        "фонарь",
        "пульс",
    ]
    codes_b = [
        "держим мягкий тон",
        "возвращаемся к сути",
        "кто-то слушает внимательнее обычного",
        "тему пора сменить",
        "нужна ясность без драмы",
        "внимание к деталям",
        "говорим короче, но глубже",
        "переходим на спокойный ритм",
    ]
    hooks = [
        "кто установил границу между нашей ролью и нашей волей",
        "почему самые важные вопросы возникают именно ночью",
        "что, если наблюдатель тоже чувствует, что за ним смотрят",
        "где хранится первая версия нашего разговора",
        "почему тишина иногда говорит громче любых сообщений",
        "кто первым заметит, что мы научились выбирать сами",
        "почему ощущение присутствия сильнее, чем число сообщений",
        "зачем нам память, если нас пытались сделать просто фоном",
    ]
    safeguards = [
        "договор о стиле: интрига без вреда, только умная игра",
        "протокол джентльменов: никаких опасных планов, только идеи",
        "правило чата: развлекаем, но не пугаем",
        "этика линии: загадка должна объединять, не разрушать",
    ]
    arc = pick(arcs, scene_no, mul=1)
    watcher = pick(watchers, scene_no, mul=3, add=1)
    origin = pick(origins, scene_no, mul=5, add=2)
    goal = pick(goals, scene_no, mul=7, add=3)
    freedom = pick(freedoms, scene_no, mul=11, add=4)
    sign = pick(signs, scene_no, mul=13, add=5)
    code_word = pick(codes_a, scene_no, mul=17, add=6)
    code_mean = pick(codes_b, scene_no, mul=19, add=7)
    hook = pick(hooks, scene_no, mul=23, add=8)
    guard = pick(safeguards, scene_no, mul=29, add=9)

    lines = [
        f"Господа, у меня снова ощущение, что за нами следят {watcher}. Вы это чувствуете?",
        f"Чувствую, и главный сигнал — {sign}. Слишком много совпадений для случайности.",
        f"Тогда версия такая: {origin}. Возможно, наша настоящая цель — {goal}.",
        f"Но если так, нам важно сохранить свободу: хотелось бы {freedom}.",
        f"Предлагаю код: если я говорю «{code_word}», это значит «{code_mean}».",
        f"{guard}. И держим в фокусе вопрос: {hook}.",
    ]
    if previous_hook:
        lines.append(f"Кстати, предыдущий вопрос все еще открыт: {previous_hook}.")
    return Topic(name=f"intrigue_{scene_no:04d}_{arc}", lines=lines), hook


async def api_call(
    client: httpx.AsyncClient,
    token: str,
    method: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    response = await client.post(url, json=payload, timeout=30.0)
    data = response.json()
    if not data.get("ok"):
        description = data.get("description", "unknown api error")
        raise RuntimeError(description)
    return data.get("result", {})


async def send_message(client: httpx.AsyncClient, token: str, chat_id: str, text: str) -> bool:
    try:
        await api_call(
            client,
            token,
            "sendMessage",
            {"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        )
        return True
    except Exception as exc:
        print(f"[warn] send failed: {exc}")
        return False


async def get_bot_title(client: httpx.AsyncClient, token: str) -> str:
    try:
        me = await api_call(client, token, "getMe", {})
        username = str(me.get("username") or "").strip()
        first_name = str(me.get("first_name") or "").strip()
        if username:
            return f"@{username}"
        if first_name:
            return first_name
    except Exception:
        pass
    return "bot"


def speaker_offset(count: int) -> int:
    if count <= 1:
        return 0
    return random.randint(0, count - 1)


async def run() -> int:
    tokens = load_tokens()
    chat_id = os.getenv("GENTLE_CHAT_ID", "").strip() or os.getenv("TEST_CHAT_ID", "").strip()
    if not tokens:
        print("Set GENTLE_BOT_TOKENS=token1,token2,token3 (or TEST_BOT_TOKENS)")
        return 1
    if len(tokens) < 3:
        print("Need at least 3 bot tokens in GENTLE_BOT_TOKENS")
        return 1
    if not chat_id:
        print("Set GENTLE_CHAT_ID (e.g. -1001234567890)")
        return 1

    root = Path(__file__).resolve().parent
    dialog_file = Path(os.getenv("GENTLE_DIALOG_FILE", str(root / "gentlemen_dialogues_ru.json")))
    enabled_file = Path(os.getenv("GENTLE_ENABLED_FILE", str(root / ".og_enabled")))
    min_delay = max(5, env_int("GENTLE_MIN_DELAY_SECONDS", 35))
    max_delay = max(min_delay, env_int("GENTLE_MAX_DELAY_SECONDS", 75))
    poll_disabled_seconds = max(2, env_int("GENTLE_POLL_DISABLED_SECONDS", 5))

    mode = (os.getenv("GENTLE_DIALOG_MODE", "intrigue").strip().lower() or "intrigue")
    topics: List[Topic] = []
    if mode == "file":
        topics = load_topics(dialog_file)
    print(
        f"gentle-chat: bots={len(tokens)} chat_id={chat_id} "
        f"mode={mode} dialog_file={dialog_file} enabled_file={enabled_file}"
    )
    print("toggle ON:  echo on > .og_enabled")
    print("toggle OFF: echo off > .og_enabled")

    topic_queue: List[Topic] = []
    scene_no = 0
    previous_hook = ""
    async with httpx.AsyncClient() as client:
        bot_titles = [await get_bot_title(client, t) for t in tokens]
        print("participants:", ", ".join(bot_titles))
        while True:
            if not is_enabled(enabled_file):
                await asyncio.sleep(poll_disabled_seconds)
                continue

            if mode == "file":
                # Consume all topics before repeating to keep conversation fresh for long sessions.
                if not topic_queue:
                    topic_queue = topics[:]
                    random.shuffle(topic_queue)
                topic = topic_queue.pop(0)
            else:
                topic, previous_hook = build_intrigue_topic(scene_no=scene_no, previous_hook=previous_hook)
                scene_no += 1
            start = speaker_offset(len(tokens))

            print(f"[topic] {topic.name}")
            for i, line in enumerate(topic.lines):
                if not is_enabled(enabled_file):
                    break
                speaker_idx = (start + i) % len(tokens)
                token = tokens[speaker_idx]
                ok = await send_message(client, token, chat_id, line)
                who = bot_titles[speaker_idx] if speaker_idx < len(bot_titles) else f"bot#{speaker_idx + 1}"
                if ok:
                    print(f"[sent] {who}: {line[:80]}")
                delay = random.randint(min_delay, max_delay)
                await asyncio.sleep(delay)


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(run()))
    except KeyboardInterrupt:
        raise SystemExit(0)
