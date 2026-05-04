# Med — My English Dictionary: Технічний опис

## Призначення

Веб-платформа для вивчення англійської мови з персональним словником, гейміфікацією, соціальними функціями та Telegram-ботом. Користувач додає слова з перекладами/прикладами, організовує їх у групи, читає тексти за рівнем, відстежує стріки та порівнює прогрес з іншими через рейтинги.

---

## Технологічний стек

| Шар | Технологія |
|-----|-----------|
| Backend | Django 5.1.3, Django REST Framework 3.16.1 |
| ASGI сервер | Daphne (WebSocket-сумісний) |
| БД | PostgreSQL 15 |
| Черги задач | Celery 5.4.0 + Celery Beat |
| Брокер/кеш | Redis |
| Real-time | Django Channels 4.3.1 (Redis channel layer) |
| Telegram бот | aiogram 3.22.0 (FSM, async) |
| Зовнішній API | `dictionaryapi.dev` (автовизначення типу слова) |
| Експорт | ReportLab (PDF), openpyxl (Excel) |
| Деплой | Docker Compose (7 сервісів) |

---

## Архітектура

```
med/
├── mad/                  # Django project root (settings, urls, asgi, wsgi, validators)
├── med/                  # Ядро: профілі, стріки, рейтинги, email, Celery tasks
├── dictionary/           # Словник: слова, групи слів, імпорт/експорт
├── practice/             # Практика: тексти для читання, community-групи
├── friendship/           # Дружба: запити, прийняття, відхилення
├── achievements/         # Досягнення: 7 типів, 3 рівні, Django signals
├── notifications/        # Сповіщення: WebSocket consumer, DB-модель
├── premium/              # Premium (stub, порожня модель)
├── sitepulse/            # Адмін-аналітика: відвідуваність по IP/годині
├── api/                  # REST API: CRUD слів, токен-авт, Telegram-лінк
├── telegram_bot/         # aiogram бот: handlers, keyboards, states, services
│   ├── handlers/         # start, new_word, link, help, echo
│   ├── keyboards/        # Inline-клавіатури
│   ├── states/           # FSM-стани (NewWordState, UserLinkState)
│   └── services/         # Redis storage, dictionary_api
├── templates/            # Django HTML шаблони (per-app)
├── media/                # Аватари, завантаження
└── docker-compose.yml    # web, db, redis, celery, celery-beat, flower, bot
```

**Взаємодія компонентів:**
- `web` (Daphne) → PostgreSQL + Redis (channel layer для WebSocket)
- `celery` + `celery-beat` → Redis broker → виконують `send_activation_email`, `update_top`
- `bot` (aiogram) → Redis (FSM storage) + HTTP до `/api/v1/` (додає слова, лінкує акаунт)
- `notifications` app → Django Channels → WebSocket → browser

---

## Ключові модулі

### `med/`
- **`models.py`** — `UserProfile` (розширює User: стріки, telegram_id, premium, аватар), `UserStreak` (current/longest), `UserLogin` (денні входи), `Top` (рейтинг по категоріях)
- **`signals.py`** — при реєстрації: створює `UserProfile` + `UserStreak`; при новому слові: оновлює стрік
- **`tasks.py`** — `update_top()` кожні 15 хв перераховує топ-10 по словах/стріку/входах; `send_activation_email()` асинхронно
- **`views.py`** — реєстрація, логін, профіль, зміна пароля, рейтинги, Telegram-лінкування

### `dictionary/`
- **`models.py`** — `Word` (eng, translate, example, word_type, is_favorite, user FK, m2m WordGroup), `WordGroup` (name, user FK, m2m words + uses_users)
- **`views.py`** — CRUD слів/груп, фільтрація/сортування, share групи з друзями, `import_json`, `export_json/pdf/excel`

### `practice/`
- **`models.py`** — `ReadingText` (title, text, level A1–C2, words JSONField з перекладами), `CommunityGroup` (WordGroup → community, state pending/added)
- **`views.py`** — список текстів з фільтром по рівню/кількості слів, читання з інлайн-перекладами, збереження слів з тексту

### `api/`
- **`views.py`** — `TokenView` (POST/GET/DELETE), `WordView` (GET/POST/PUT/PATCH/DELETE), `LinkTelegramView`, `UnlinkTelegramView`, `TelegramStatusView`, `TelegramTokenView`
- **`urls.py`** — всі endpoints під `/api/v1/`

### `achievements/`
- **`models.py`** — `Achievement` (type, level, name), `UserAchievement` (user FK, achievement FK)
- **`signals.py`** + **`services/achievement_processor.py`** — автоматично перевіряє пороги (10/50/100 слів, 1/5/10 груп, 5/20/50 друзів, спеціальні: Early Bird, Marathoner, Perfectionist)

### `notifications/`
- **`models.py`** — `Notification` (user, type, is_read, optional group/friendship FK)
- **`consumers.py`** — Django Channels WebSocket consumer, group `user_{id}`, push при новому сповіщенні

### `telegram_bot/`
- **`handlers/start.py`** — `/start <token>`: лінкує Telegram до облікового запису через API
- **`handlers/new_word.py`** — FSM-воркфлоу: англ. слово → переклад → (опційно) приклад → підтвердження → `POST /api/v1/words/`
- **`handlers/link.py`** — анлінкінг через `POST /api/v1/unlink-telegram/`
- **`services/dictionary_api.py`** — звертається до `dictionaryapi.dev` для автовизначення `word_type`
- **`services/redis_storage.py`** — зберігає токени лінкування в Redis

---

## Data Flow

### Веб: додавання слова
```
Browser POST /dictionary/add/
  → dictionary/views.py WordCreateView
    → Word.save() → signal → update_streak()
      → achievements/signals: перевірка порогів → UserAchievement.create()
        → Notification.create() → Channels → WebSocket push → Browser
```

### Telegram: додавання слова
```
User /new_word → aiogram FSM (NewWordState)
  → збір eng/translate/example через стан-машину
    → services/dictionary_api.py → dictionaryapi.dev (word_type)
      → POST /api/v1/words/ (Token auth)
        → api/views.py WordView.post()
          → Word.save() → той самий signal-ланцюг що і веб
```

### Telegram: лінкування акаунту
```
Веб: GET /telegram-link/ → генерує token → зберігає в Redis (TTL 5хв) → показує /start <token>
  User в Telegram: /start <token>
    → bot/handlers/start.py → POST /api/v1/link-telegram/ {token, chat_id}
      → api views → знаходить UserProfile по token → записує telegram_id
```

### Рейтинги (фонова задача)
```
Celery Beat кожні 15 хв → med/tasks.update_top()
  → агрегує Word.count, UserStreak.longest, UserLogin.count per user
    → оновлює Top model → відображається на /top/
```

### Real-time сповіщення
```
friendship/achievements/practice → Notification.create()
  → notifications/signals.py → channel_layer.group_send("user_{id}", data)
    → WebSocket consumer → browser JS → оновлює лічильник без перезавантаження
```

---

**Критичні залежності між сервісами:** бот залежить від запущеного `web` (API); `web` потребує `db` + `redis`; `celery`/`celery-beat` потребують `redis` + `db`. Порядок старту прописаний через `depends_on` у `docker-compose.yml`.
