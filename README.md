# TGM Coin Bot

![Project preview](docs/screenshots/preview.png)

A Telegram economy bot that rewards chat activity, supports referrals, tracks balances and exposes admin controls.

## Demo

- GitHub: https://github.com/KaimiEwl/tgm-coin-bot
- Live demo: not applicable for this project type
- Video: planned
- Case notes: see `docs/architecture.md`

## What it shows

This project shows bot mechanics, anti-spam logic, SQLite persistence, admin tooling and product roadmap thinking.

## Features

- Random coin rewards with cooldowns
- Super-prize and referral mechanics
- Owner tribute and anti-abuse state
- Admin UI for users/chats/broadcasts
- Mini-app and monetization roadmap docs

## Tech stack

- Python
- python-telegram-bot
- Flask
- SQLite
- Pillow

## Local setup

```
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

## Verification

```
python -m py_compile bot.py admin_ui.py storage.py
```

## Status

Demo export. Bot tokens, local database and logs are excluded.

## Security and cleanup

This public repository is a clean portfolio export. It intentionally excludes production secrets, local databases, logs, generated media, backups, runtime folders and private deployment artifacts.
