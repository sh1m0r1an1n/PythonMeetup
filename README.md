# Python Meetup

Система управления мероприятиями Python Meetup с интеграцией Telegram-бота для уведомлений.

## Возможности

- Управление мероприятиями и докладами
- Система вопросов к докладчикам
- Telegram-уведомления для участников
- Профили пользователей с настройками уведомлений

## Установка

1. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
venv\Scripts\activate     # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` в корне проекта и добавьте необходимые переменные окружения:
```env
# Django settings
SECRET_KEY=your-secret-key-here-50-characters-long
DEBUG=True

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Time zone
TIME_ZONE=Europe/Moscow
```

**Описание переменных окружения:**

- `SECRET_KEY` - **(обязательно)** секретный ключ Django для криптографических функций (50+ символов)
- `DEBUG` - режим отладки (True/False), по умолчанию False
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота для отправки уведомлений
- `TIME_ZONE` - часовой пояс приложения, по умолчанию Europe/Moscow

4. Примените миграции:
```bash
python manage.py migrate
```

5. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

6. Запустите сервер:
```bash
python manage.py runserver
```