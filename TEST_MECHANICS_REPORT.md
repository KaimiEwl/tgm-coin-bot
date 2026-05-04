# Test Mechanics Report

Generated: 2026-02-15 19:21:39
DB: coins.db

## Summary
- Passed: 14
- Failed: 0

## Checks
- PASS `reward_first`: result=(True, 7, 0)
- PASS `cooldown_block`: result=(False, 7, 60)
- PASS `owner_tribute`: tributes=[0, 1, 1, 1, 1] sum=4 expected=4
- PASS `super_task_create`: created=True
- PASS `super_task_claim`: claimed=(123, 123)
- PASS `transfer`: result=(True, 45, 12, 'OK')
- PASS `referral_set`: result={'assigned': True, 'bonus_awarded': True, 'referrer_balance': 1045, 'reason': 'OK'}
- PASS `referral_bonus`: result={'assigned': True, 'bonus_awarded': True, 'referrer_balance': 1045, 'reason': 'OK'}
- PASS `referral_commission`: result=(5, 7000001101)
- PASS `fireworks_trigger`: triggered=True winners=3
- PASS `reliability_flag`: flagged=True streak=19500
- PASS `bot_to_chat_send`: send_ok=True
- PASS `bot_to_bot_updates_limitation`: events_before=0 events_after=0
- PASS `bot_dm_to_bot_blocked`: dm_ok=False desc=http 400

## Integration Note
- Telegram Bot API allows sending bot messages to group, but gameplay logic should be validated with real user accounts because bot-origin messages are not reliably processed as player activity by another bot.
