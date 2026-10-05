# HAV — Cloud Architecture Technologies

Лендінг hav.com.ua. Тексти й картки живуть у `content.json`. Заявка з форми йде в Telegram.

## Файли

- `index.html` — головна
- `erp.html`, `bas.html`, `odoo.html` — окремі сторінки напрямків
- `css/styles.css` — стилі
- `js/main.js` — меню, анімації, відправка форми
- `content.json` — статистика, послуги, стек, кейси, контакти і картки ERP / BAS / Odoo на головній
- `leads/` — сервіс, який приймає `POST /api/lead` і пише в Telegram

Email у `content.json` (`contact.email`) продубльовано в `index.html` (блок `noscript`) і в `js/main.js` (`FALLBACK_EMAIL`) — це запасний текст, якщо файл вмісту не відкрився.

## Локально

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Сайт: http://localhost:8080

Без токена й ID чату сторінка відкривається, а форма відповідає, що прийом заявок недоступний.

## Coolify

Репозиторій GitHub, тип збірки Docker Compose, файл `docker-compose.yml`.

У змінних оточення Coolify:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Домен вказуйте сервісу `web`, порт контейнера `80`. Сервіс `leads` без домену: його бачить лише Nginx.

## Telegram

1. У `@BotFather` створіть бота й візьміть токен.
2. Напишіть боту в особисті або додайте його в групу й надішліть туди будь-яке повідомлення.
3. Відкрийте `https://api.telegram.org/bot<ТОКЕН>/getUpdates` і візьміть `chat.id`. Для групи це від'ємне число.

Вхідний webhook боту не потрібен: сервіс лише надсилає повідомлення, коли хтось залишає заявку.
