# Bot Simulation Report

Generated: 2026-02-15 19:44:49
Chat: -1003652883951
Steps: 9, interval=21s

## Send API results
- Sent ok: 9
- Sent failed: 0
- step 1: @usertgm1bot ok message_id=37
- step 2: @UserTgm2bot ok message_id=38
- step 3: @UserTgm3bot ok message_id=39
- step 4: @usertgm1bot ok message_id=40
- step 5: @UserTgm2bot ok message_id=41
- step 6: @UserTgm3bot ok message_id=42
- step 7: @usertgm1bot ok message_id=43
- step 8: @UserTgm2bot ok message_id=44
- step 9: @UserTgm3bot ok message_id=45

## coin_events delta (after simulation)
- No new events

## Test bot balances
- No test bot users in users table

## Firework state
- progress: 99/100
- period_count: 2
- period_key: 2026-02-15:evening

## Interpretation
- Simulation delivered messages but reward events are incomplete; check main bot logs/privacy settings.
- Telegram Bot API limitation: messages from one bot are usually not processed as player activity by another bot, so full gameplay validation should be done with real user accounts.
# Bot Simulation Report (Telegram)

Date: 2026-02-15

## Run: test_mode_runner.py
- Duration: 45s
- Interval: 7s
- Bots: 3
- Target chat: @chattgmcoin
- Result: sent=6 failed=0

Notes:
- This test only verifies that test user-bots can post messages to the target chat via Telegram API.
- To validate reward replies/buttons, observe the main bot in the chat during the run (test_mode feature flag must be enabled).
