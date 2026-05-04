# Release Plan

## Goal
Roll out features in controlled steps without breaking core farming flow.

## Stage 0 (Done)
- Base bot economy running.
- Admin UI with users/chats.
- Feature flags added to control rollout.

## Stage 1
- Enable `send_coins` in admin for internal testing.
- Test `/send 10 tgm` in private and group reply flows.
- Validate insufficient balance, self-transfer protection, and event logging.

## Stage 2
- Add test mode scenario runner for 3 bot tokens.
- Bots post scripted messages in one test chat to simulate low/high activity.
- Collect metrics: reward frequency, firework frequency, transfer success rate.

## Stage 3
- Public rollout of transfers for selected communities.
- Keep ability to disable `send_coins` instantly from admin.
- Monitor abuse signals and reliability flags.

## Stage 4
- Add leaderboard and shop behind feature flags.
- Add referral flow behind feature flags.

## Rollback Rules
- Any critical bug in balances: disable `send_coins`.
- Any spam/instability in chat events: disable `fireworks`.
- Any abnormal owner tax behavior: disable `owner_tribute`.

## Test Checklist (Every Release)
- Coin balances never go negative by logic bug.
- Transfer updates both users atomically.
- Firework trigger limits by period are respected.
- Language switching does not break commands.
