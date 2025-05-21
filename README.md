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

3. Создайте файл `.env` и добавьте:
```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

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