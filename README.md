# Монітор термінів — Führerscheinstelle München

Перевіряє кожні ~10 хвилин, чи з'явилися вільні дні для запису
«Umschreibung eines ausländischen Führerscheins» (Garmischer Str. 19–21),
і надсилає повідомлення в Telegram. Працює безкоштовно на GitHub Actions —
твій комп'ютер вмикати не потрібно.

## Налаштування (≈10 хвилин)

### 1. Telegram-бот
1. Напиши [@BotFather](https://t.me/BotFather) → `/newbot` → отримаєш **токен**.
2. Напиши своєму новому боту будь-що (наприклад «привіт») — інакше він не зможе писати тобі першим.
3. Дізнайся свій **chat_id**: напиши [@userinfobot](https://t.me/userinfobot).

### 2. GitHub
1. Створи **приватний** репозиторій і залий ці файли
   (`check_termin.py`, `.github/workflows/monitor.yml`).
2. У репозиторії: Settings → Secrets and variables → Actions → додай:
   - `TELEGRAM_BOT_TOKEN` — токен від BotFather
   - `TELEGRAM_CHAT_ID` — твій chat_id. Кілька отримувачів: id через кому
     (кожен має спершу написати боту), або id групи, куди додано бота
3. Вкладка **Actions** → увімкни workflows → відкрий «Termin Monitor» →
   **Run workflow** для першого тесту.

### 3. Перевірка
У логах запуску має бути «Keine freien Termine» або повідомлення в Telegram.

## Якщо API-endpoint не відповідає
Мюнхен час від часу змінює бекенд бронювання. Тоді:
1. Відкрий [сторінку запису](https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/1071896/locations/10308174)
   у Chrome → DevTools (F12) → вкладка **Network**.
2. Знайди запит типу `available-calendar` і скопіюй його URL.
3. Онови константу `BASE_URL` у `check_termin.py`.

## Нотатки
- Скрипт шле повідомлення лише коли список вільних днів **змінився**,
  щоб не спамити кожні 10 хвилин.
- Один запуск workflow працює ~5 год 45 хв і сам опитує API кожні 10 хвилин,
  а наприкінці перезапускає себе. Cron раз на 6 годин лише страхує, якщо
  ланцюжок обірветься (сам по собі cron GitHub затримується на години).
- Коли запишешся на термін — просто вимкни workflow (Actions → Disable).
