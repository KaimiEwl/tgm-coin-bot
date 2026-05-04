# TGM Coin: User Messages and Logic Reference

Updated: 2026-02-16
Purpose: single source of truth from your original messages, plus normalized logic to avoid confusion later.

## 1) Raw messages (chronological)

1. "давай сделаем тг бота который может давать монетки за сообщения в чате просто юзер пишет и он ему сразу же дает монетку от 1 до 10 монетки проверить можно /info"
2. "начало положено надо чтобы этот бот работал во всех чатах и давал монетки всем юзерам и вел базу юзеров а иногда давал супер приз чтобы его получить пусть пишет напиши мне личное сообщение и ты получишь от 1 до 1000 монет любое личное сообщение подойдет и чтобы он за это давал награду также со временем нам понадобиться рейтинг юзеров кто сколько монет получил мини апп его прикрутим позже то есть смыфсл такой мы делаем бота он раздает монетки 1 -tgm -10 tgm coin потом план развития лидерборд магазин за монеты рефералка партнерка майнер нфт и т д можнео что угодно если пойдет я тебя держу в курсе чтобы это повлияло на археитиктуру"
3. "а владельцы канала должны получать 10 % от всех кто у них собирает типа дань с канала чтобы спама небыло пусть дает монеты не чаще одного раза в минуту"
4. "также надо вести лог чтобы если юзер собирает более 5 часов подряд его помечать не надежным"
5. "можем сделать простой ui чтобы там была нужная инфа список юзеров сколько монет у них их id чтобы им можно было написать в личку если нужно"
6. "Открыть: http://127.0.0.1:8080 неоткрыть по ссылке"
7. "так как мне открыть панель ?"
8. "можешь сам запустить за меня"
9. "давай еще добавим общий прогресс чата и когда доходит до 100% запускается феерверк и дает последним 15 любдям по 1-100 монет рандомно - также сделаем в админке включать и выключать эту функцию для каналов то есть мы сами решаем где салют а где нет потом может дадим админам выбирать"
10. "раза 3-4 в день чтобы набирался за каждое сообщение + % какой то"
11. "давай его феерверком лучше называть )) и надо возомжность меню англ и ру везде в чатах и короче везде чтобы можно было переключать"
12. "салюты ненадо блокировать делай их просто днем вечером утром и ночью по 2 примерно чтобы набирались перерыв опять набирается и т д"
13. "вопрос на англ салют нормально для феерверка звучать будет ?"
14. "пусть салют растет не на % от сообщений а если пишут время идет или как лучше? придумай логику при которой он будет раз 5-6 в сутки и в чате где мало народу и где много хотелось бы чтобы активрность влияла"
15. "такой вопрос если передалать все заново будет лучше или так лучше постепенно апгрейжевать ?"
16. "давай текущую точку сохраним и потом добавим тест режим я дам 3 апи ключа ботов они должны будут общаться в чате и мы будем наблюдать тестить все ли ок работает и еще добавим пересылку монет /send ответом на сообщение /send 10 tgm к примеру будет отправлять 10 монет - короче мы эти все фишки будем добавлять постепенно на выходе будет передача монет потом добавим то есть надо еще будет план релиза и возможность вкл выкл в админке"
17. "хотелось бы еще делать рассылку через бота для тех кто его активировал через админку чтобы писал в поле и отправлял всем также было бы круто меню в боте для юзеров и приветствие привет я бот tgm coin поставь меня в чат и сделай админом ты будешь получать 10% от всх раздачь в чате и надо чтобы админу начисляло реально если еще не сделано так вот еще было бы неплохо веб апп туда добавить в бота чтобы там был рейтинг ну этот топ людей кто собрал сколько юзеры одна вкладка админы вторая вкладка - также туда рефералку бы и награды за рефералов по 1000 монет за каждого юзера приведенного максимум за 6 юзеров еще бы круто было бы круто если юзер позвал друга то ему всегда давать 10 % от начислений друга  если есть советы готво выслушать"
18. "после всего этого надо сделать роадмап его добавить в веб апп как отдельную вкладку ну веб апп под мобилку конечно же там красиво распланировать и показать все этапы чтобы было не скучно но и дать проекту время набрать юзеров и подписчиков - также надо будет сделать бусты - платные и бесплатные в зависимости какой этап но они точно должны быть и все должно быть в админке вкл выкл и мы запланируем велючение еще бы в идеале иметь возможность что то включать и выключать для определенных юзеров и каналов и отдельный список не доверия ну те кто майнит нон стоп сливает передает их просто выделлить списком и иметь возможность бана если понадобиться еще бы хотелось защиту от взлома и добавления монет надо как то держать в курсе и отмечать такие события присылая уведомление например мне как админу проекта там уже разбираться если что то серьезное ну как то замерять резкие скачки что хоб неоткуда взялось при каком то резком росте сообщать как пример защиты и также еще бы графу где за последние 5 суток доход юзера так тоже можно смотреть там топ смотришь и если слишком много то разбираешься уже ну короч мониторинг такой бы еще потом хотелось бы добавить нфт которые увеличат в 2 5 10 раз добычу монет в майнере его в веб апп добавить можно к примеру - но это уже последним этапом перед релизом монет и отсылки их на кошельки просто про нфт пишу чтобы ты был в курсе еще бы круто было бы бусты за тон или юсдт какую то механику предложи чтобы проект на свои нужды мог продавать бусты"
19. "потом приведи админку в хороший визуал как у аппле минималистично красиво удобно пожалйста оцени уровень сложности и работы всей системы насколько она будет стабильна ?"
20. "давай да 
“Apple-style” редизайн админки,"
21. "сделай пожалуйста Полный polished UI (фильтры, таблицы, графики, микроанимации, адаптив): также подумай над логикой и удобством использования"
22. "проверь все ли у нас на ру и английском надо чтобы везде переключатель был и язык менялся"
23. "после этого сделай везде подсказки что для чего чтобы не путаться"
24. "а да еще создай фаил возьми все мои сообщения и запиши как логику чтобы если запутаемся обращаться к нему и дай почитать мало ли уже есть не точности"

## 2) Normalized product logic (short)

1. Core reward loop:
- In chats, user message can award 1-10 TGM.
- First rewarded message of the day: 1-100 TGM.
- Cooldown anti-spam: no more than once per user per 60 seconds.
- `/info` shows user stats.

2. Coverage and storage:
- Bot works in all connected chats.
- Persistent DB for users/chats/events.

3. Extra rewards:
- Occasional super prize via DM prompt; any private message can trigger 1-1000 reward.

4. Channel owner economy:
- Chat/channel owner receives 10% tribute from distributions in their chat.

5. Trust/risk:
- If user farms continuously for more than 5 hours, mark as untrusted.
- Keep logs and suspicious list for review/ban.

6. Fireworks (chat progress mechanic):
- Chat has progress toward firework trigger.
- On trigger: reward last 15 users with random 1-100.
- Should happen about 5-6 times/day with time + activity influence.
- Admin can enable/disable fireworks per chat.

7. Localization:
- RU/EN language switch should exist everywhere (admin, bot menu, mini app).

8. Admin panel:
- Users list, balances, IDs, quick DM links, filters.
- Feature toggles (global and per chat/user where needed).
- Broadcast to activated users.
- Monitoring: spikes, top income for last 5 days, suspicious behavior.

9. Mini app:
- Mobile friendly.
- User-only (no admin features inside mini app).
- Tabs: Home, Top, Friends, Earn, Settings.
- Language switch RU/EN inside the app.

10. Growth features (phased):
- Leaderboard, shop, referrals, partner system, miner, boosts, NFT multipliers, wallets (later stage).
- Referral rewards: fixed invite bonus + percent commission from friend activity (cap rules configurable).
- Transfer command plan: `/send` (reply format like `/send 10 tgm`).
- Test mode with multiple bot tokens for staged validation.

## 2.1) UX clarifications (current)

1. Chat reward message:
- Always reply in chat with an inline button (to show the bot is working):
  - If reward granted: button text `+N TGM coin` (N is the exact amount for this message).
  - If cooldown: button text like `⏳ 21s`.
- No extra balance text in chat messages (balance is inside the app / `/info`).
- App is opened via `/info` button or `/app` (to reduce spam).

2. Buttons without messages:
- Telegram inline keyboards are attached to messages; a "button only, no message bubble" is not generally possible in group chats.

## 3) Potential ambiguities / inconsistencies to resolve

1. Firework frequency:
- Mentioned "3-4/day", then "day/evening/morning/night by 2", then target "5-6/day".
- Current canonical target suggested: 5-6/day adaptive by chat activity.

2. Firework growth model:
- Mentioned percent by message, then not by percent, then "time + activity".
- Canonical direction: hybrid time-based baseline + activity acceleration.

3. Referral economics:
- One-time 1000 per invite (max 6 invites) and permanent 10% from friend rewards both requested.
- Need final rule if both active together or staged by feature flag.

4. Scope timing:
- Some items are immediate (core economy/admin/monitoring), some are late-stage (NFT/wallet withdrawals).
- Keep staged rollout to avoid instability.

## 4) How to use this file

1. Treat Section 1 as source history (what was requested).
2. Treat Section 2 as operational spec baseline.
3. Check Section 3 before implementing a new feature to avoid conflicting behavior.
