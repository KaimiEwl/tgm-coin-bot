import asyncio
import os
import random
import sys
from typing import List

import httpx


def env_int(name: str, default: int) -> int:
    value = os.getenv(name, "")
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_tokens() -> List[str]:
    raw = os.getenv("TEST_BOT_TOKENS", "")
    tokens = [item.strip() for item in raw.split(",") if item.strip()]
    return tokens


async def send_message(client: httpx.AsyncClient, token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        response = await client.post(url, json=payload, timeout=20.0)
        data = response.json()
        return bool(data.get("ok"))
    except Exception:
        return False


async def main() -> int:
    tokens = load_tokens()
    chat_id = os.getenv("TEST_CHAT_ID", "").strip()
    duration_sec = env_int("TEST_DURATION_SECONDS", 900)
    interval_sec = max(1, env_int("TEST_INTERVAL_SECONDS", 8))

    if not tokens:
        print("Set TEST_BOT_TOKENS=token1,token2,token3")
        return 1
    if not chat_id:
        print("Set TEST_CHAT_ID (e.g. -1001234567890)")
        return 1

    phrases = [
        "test ping",
        "farming message",
        "checking rewards",
        "firework progress",
        "economy smoke test",
    ]

    print(
        f"Starting test mode: bots={len(tokens)} chat_id={chat_id} "
        f"duration={duration_sec}s interval={interval_sec}s"
    )
    success = 0
    failed = 0
    steps = max(1, duration_sec // interval_sec)

    async with httpx.AsyncClient() as client:
        for i in range(steps):
            token = tokens[i % len(tokens)]
            text = f"[TEST] {random.choice(phrases)} #{i + 1}"
            ok = await send_message(client, token, chat_id, text)
            if ok:
                success += 1
                print(f"[{i + 1}/{steps}] sent")
            else:
                failed += 1
                print(f"[{i + 1}/{steps}] failed")
            await asyncio.sleep(interval_sec)

    print(f"Done. sent={success} failed={failed}")
    return 0 if success > 0 else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
