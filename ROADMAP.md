# TGM Coin Roadmap

## Phase 0 (Done)
- Core reward loop: `1..10` coins per message
- Cooldown anti-spam (`1 reward / minute / user / chat`)
- Super prize in DM (`1..1000`)
- Owner tribute (`10%`) with exact remainder accounting
- Firework mechanics + periodic limits

## Phase 1 (In Progress)
- Referrals: `1000` bonus per invite (max `6`) + permanent `10%` commission
- User transfers (`/send`)
- Admin broadcasts to activated users
- Web app leaderboard tabs: Users / Admins / Referrals / Roadmap
- RU/EN menu and interface

## Phase 2 (Planned): Boosts and Monetization
- Free boosts (activity-based, temporary)
- Paid boosts (TON/USDT): duration packs (`24h`, `72h`, `7d`)
- Booster multipliers by stage: `x1.25`, `x1.5`, `x2`
- Strict stack rules: highest active boost applies, no unlimited stacking
- Full ON/OFF via feature flags in admin panel

## Phase 3 (Planned): Security and Monitoring
- 5-day income leaderboard for anomaly review
- Suspicious users list (high income / heavy transfer-out)
- Admin alerts for threshold spikes
- Per-user and per-chat override controls (allow/deny selected features)
- Ban and trust-risk workflow in admin panel

## Phase 4 (Planned): Product Expansion
- Coin shop
- Referral campaigns and partner drops
- Scheduled events and seasonal quests

## Phase 5 (Planned): NFT + Wallet Integration
- NFT multipliers for mining (`x2`, `x5`, `x10`)
- Anti-abuse validation before mint benefits
- Wallet withdrawals after security audit and limits

## Boosts Economic Proposal (TON/USDT)
- `Free Boost`: granted for activity milestones, short duration, lower multiplier.
- `Paid Boost Lite`: small TON/USDT payment, moderate multiplier, fixed duration.
- `Paid Boost Pro`: higher payment, strong multiplier, cooldown between purchases.
- Revenue split suggestion:
  - `70%` treasury/project development
  - `20%` growth pool (campaigns/rewards)
  - `10%` security reserve
- Safety:
  - hard daily cap per user on boosted rewards
  - anti-wash rule on transfer loops
  - alert on sudden growth bursts
