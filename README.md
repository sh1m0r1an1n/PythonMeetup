# Python Meetup

Система управления мероприятиями Python Meetup с интеграцией Telegram-бота для уведомлений.

## Возможности

- Управление мероприятиями и докладами
- Система вопросов к докладчикам
- Telegram-уведомления для участников
- Профили пользователей с настройками уведомлений

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd python-meetup
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Скопируйте `.env.example` в `.env` и настройте переменные окружения:
```bash
cp .env.example .env
```

5. Примените миграции:
```bash
python manage.py migrate
```

6. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

7. Запустите сервер разработки:
```bash
python manage.py runserver
```

## Разработка

### Тестирование

```bash
pytest
pytest --cov=meetup
```

### Линтинг

```bash
ruff check .
ruff format .
```

## Структура проекта

- `meetup/` - основное приложение
  - `models.py` - модели данных
  - `services.py` - бизнес-логика
  - `admin.py` - настройки админки
  - `tests/` - тесты

## Лицензия

MIT 