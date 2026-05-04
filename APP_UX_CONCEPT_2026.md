# TGM Coin Mini App Concept (2026)

Updated: 2026-02-15 20:00:47

## Product split
- Admin panel: only for admins/channel owners (controls, moderation, feature flags, monitoring).
- Mini app: only for end users (balance, top, referrals, tasks, boosts, shop).

## Core UX principles (2026)
- One-screen value: first screen must show personal value immediately (your balance + next action).
- Progressive disclosure: advanced blocks (roadmap, boosts details, economics) open only on demand.
- Low-friction loops: reward -> open app -> see progress -> complete simple action.
- Social proof first: visible leaderboard and momentum indicators.
- Fast navigation: 3-5 top destinations max.

## Proposed user IA (no overload)
- Home
  - Your balance (primary card)
  - Global balance / economy pulse (secondary card)
  - CTA row: Open Shop, Invite Friends, Quests
  - Optional compact ticker: latest winners/top movers
- Top
  - Leaderboard by total coins
  - Filters: Today / 7d / All-time (future)
  - Sticky user row: "you are #N"
- Friends
  - Personal referral link + quick share
  - Referral stats: invited count, earned bonus, passive 10% income
  - Mini leaderboard of referrers
- Earn
  - Quests list (daily/weekly/event)
  - Boosts (free and paid) as cards
  - Roadmap collapsed section: hidden by default, expandable

## What should be hidden by default
- Admin features
- Full roadmap details
- Complex boost economics and payout formulas
- Anti-fraud internals

## Micro-interaction concept
- Reward message in chat: `+5 TGM coin (balance: X)` + single `APP` button.
- In app Home: animated counter on first open, then static.
- On quest completion: compact toast + one CTA.
- On firework day events: lightweight banner in app, no noisy feed spam.

## Monetization placement (without clutter)
- Shop and paid boosts are not separate top-level tabs initially.
- They live behind Home CTA + Earn cards.
- Show "locked" badges for upcoming mechanics (NFT, partner boosts) until rollout.

## Rollout stages
1) Stage A: Home + Top + Friends + Earn (basic cards, no heavy settings)
2) Stage B: Shop launch with 2-3 simple offers
3) Stage C: Boosts with clear expiry and effect labels
4) Stage D: Roadmap standalone page only when content volume grows

## Telegram-specific implementation notes
- Main mini app entry should be set via menu button (`/setmenubutton` in BotFather).
- If WebApp URL is HTTP (local), Telegram opens regular URL button, not full web_app mode.
- For production UX, use HTTPS domain for proper WebApp behavior.

## Current status aligned now
- Reward response minimized to one short line.
- Single APP button in reward reply.
- Extra progress noise removed from regular reward loop.
- Bot simulation report is stored separately in `BOT_SIM_REPORT.md`.
