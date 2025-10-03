# Selectel Billing ETL System

Автоматизированная система для сбора и хранения данных Selectel Billing в PostgreSQL с интеграцией в Redash для создания живых дашбордов.

## 🎯 Цель проекта

Автоматизировать сбор и хранение данных Selectel Billing в базе PostgreSQL и предоставить возможность строить живые дашборды в Redash.

## 📋 Требования

### API токен Selectel
Для работы проекта необходим **статический токен (X-Token)** Selectel, который предоставляет доступ к API биллинга.

**Как получить токен:**
1. Войдите в [панель управления Selectel](https://my.selectel.ru)
2. В верхнем меню нажмите **Аккаунт**
3. Перейдите в раздел **Доступ** → вкладка **API-ключи**
4. Нажмите **Добавить ключ**
5. Введите название ключа (например, "Redash ETL")
6. Нажмите **Добавить** и скопируйте полученный токен

📖 **Подробные инструкции**: 
- [Как получить токен Selectel](SELECTEL_TOKEN.md)
- [Официальная документация](https://docs.selectel.ru/api/authorization/#get-static-token)

### Системные требования
- Docker и Docker Compose
- 2 ГБ свободной оперативной памяти
- 5 ГБ свободного места на диске

## 📋 Функциональность

- **ETL-скрипт** на Python для сбора данных из API Selectel
- **PostgreSQL** схема для хранения четырех типов данных:
  - Балансы (balances)
  - Прогнозы расходов (predictions)
  - Транзакции (transactions)
  - Отчеты по проектам (project_reports)
- **Redash интеграция** с готовыми SQL-запросами и дашбордами
- **Безопасное хранение** API-токена через переменные окружения
- **Автоматизация** через cron или встроенное расписание

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Selectel API  │───▶│   ETL Script    │───▶│   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Logs        │    │     Redash      │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Быстрый старт

### Вариант 1: Полная автоматизация (рекомендуется)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/EduardGuselnikov/redash-std.git
cd redash-std

# 2. Создайте файл конфигурации
cp .env.example .env

# 3. Отредактируйте .env - укажите ваш Selectel API токен
nano .env  # Замените your_selectel_static_token_here на ваш токен

# 4. Запустите полную установку с дашбордами
make docker-setup-complete

# 5. Готово! Откройте http://localhost:5000
# 📊 Дашборды настроятся автоматически, если в .env указаны REDASH_ADMIN_EMAIL и REDASH_ADMIN_PASSWORD
```

### Вариант 2: Пошаговая установка

```bash
# 1. Клонируйте репозиторий и настройте конфигурацию
git clone https://github.com/EduardGuselnikov/redash-std.git
cd redash-std
cp .env.example .env
nano .env  # Укажите ваш Selectel API токен

# 2. Запустите сервисы
make docker-up

# 3. Настройте Redash
make setup-redash

# 4. Создайте администратора через веб-интерфейс
# Откройте http://localhost:5000/setup и создайте пользователя

# 5. Настройте дашборды (опционально)
make setup-dashboards
```

### ⚙️ Настройка .env файла

После копирования `.env.example` в `.env`, обязательно укажите:

```bash
# ОБЯЗАТЕЛЬНО: Ваш статический токен Selectel
SELECTEL_API_TOKEN=ваш_реальный_токен_здесь

# РЕКОМЕНДУЕТСЯ: Смените пароли по умолчанию
DB_PASSWORD=ваш_безопасный_пароль
POSTGRES_PASSWORD=ваш_postgres_пароль
REDASH_DATABASE_PASSWORD=ваш_redash_пароль
REDASH_ADMIN_PASSWORD=ваш_админ_пароль
REDASH_SECRET_KEY=ваш_секретный_ключ
REDASH_COOKIE_SECRET=ваш_cookie_секрет
```

📖 **Как получить токен Selectel**: [SELECTEL_TOKEN.md](SELECTEL_TOKEN.md)

## 🐳 Docker развертывание

### 1. Сборка и запуск

```bash
# Сборка образов
make docker-build

# Запуск сервисов
make docker-up

# Просмотр логов
make docker-logs
```

После старта Redash будет доступен в браузере на `http://localhost:5000`.

Первичная инициализация Redash:
- На первой странице задайте организацию и административный аккаунт
- Затем в Settings → Data Sources добавьте PostgreSQL (`selectel_billing`)

### 2. Остановка

```bash
make docker-down
```

## ⏰ Автоматизация через Cron

```bash
# Настройка cron
make cron-setup

# Или добавьте вручную в crontab:
# 0 * * * * /path/to/project/cron_etl.sh
```

## 📊 Redash интеграция

> 📋 **Подробные инструкции**: См. [REDASH_SETUP.md](REDASH_SETUP.md) для пошаговой настройки

### 1. Подключение к PostgreSQL

В Redash создайте новый Data Source:
- **Type**: PostgreSQL
- **Host**: localhost (или IP вашего сервера)
- **Port**: 5432
- **Database**: selectel_billing
- **Username**: selectel_user
- **Password**: ваш_пароль

Параметры подключения к БД Redash (если нужно):
- Host: `postgres`
- Database: `redash`
- User: `redash`
- Password: `redash_password`

### 2. Создание запросов

## 🎨 Автоматическая настройка дашбордов

Проект включает автоматическую настройку дашбордов Redash с готовыми запросами и визуализациями.

### 🚀 Что настраивается автоматически:

1. **Источник данных PostgreSQL** - подключение к базе данных `selectel_billing`
2. **4 готовых запроса** - все ключевые метрики и аналитика
3. **1 основной дашборд** с полным набором визуализаций

### 📋 Готовые запросы:

- **Текущий баланс** - общий баланс на последнюю дату
- **Прогнозы расходов** - количество дней до исчерпания баланса
- **Отчеты по проектам** - расходы по проектам за текущий год
- **Транзакции по услугам** - расходы с группировкой по месяцам и услугам

### ⚙️ Настройка конфигурации:

Все дашборды и запросы настраиваются через файл `redash_config.json`. Вы можете:
- Изменить SQL-запросы
- Добавить новые запросы
- Создать дополнительные дашборды
- Настроить теги и описания

📖 **Подробная инструкция**: [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md)

## 📊 Примеры SQL-запросов

Используйте готовые SQL-запросы из файла `redash_queries.sql`:

#### Текущий баланс
```sql
SELECT 
    balance_id,
    currency,
    amount,
    credit_limit,
    status,
    fetched_at
FROM balances 
WHERE fetched_at = (SELECT MAX(fetched_at) FROM balances)
ORDER BY balance_id;
```

#### Динамика баланса
```sql
SELECT 
    DATE(fetched_at) as date,
    balance_id,
    currency,
    AVG(amount) as avg_amount,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount
FROM balances 
WHERE fetched_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(fetched_at), balance_id, currency
ORDER BY date DESC, balance_id;
```

#### Транзакции за последние 7 дней
```sql
SELECT 
    DATE(created) as date,
    transaction_type,
    balance,
    COUNT(*) as transaction_count,
    SUM(ABS(price)) as total_amount
FROM transactions 
WHERE created >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created), transaction_type, balance
ORDER BY date DESC, total_amount DESC;
```

#### Расходы по проектам за текущий год
```sql
SELECT 
    year,
    month,
    project_name,
    balance_type,
    value
FROM project_reports 
WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
ORDER BY year DESC, month DESC, value DESC;
```

### 3. Создание дашборда

1. Создайте новый дашборд в Redash
2. Добавьте запросы как виджеты
3. Настройте автоматическое обновление (рекомендуется каждые 5-15 минут)

## 📈 Ключевые метрики

### Балансы
- Текущий баланс по аккаунтам
- Динамика изменения баланса
- Кредитные лимиты и статусы

### Прогнозы
- Предсказанные расходы по типам балансов
- Детализация прогнозов по сервисам

### Транзакции
- История всех транзакций с начала года (при каждом старте скрипта)
- Обновление данных каждый час за последние 2 часа
- Расходы по услугам и сервисам
- Ежедневная статистика операций
- Обнаружение аномальных трат

### Отчеты по проектам
- Полная синхронизация с начала года при каждом старте скрипта (независимо от наличия данных в БД)
- Обновление данных ежечасно только за текущий месяц
- Месячные расходы по проектам и типам балансов
- Динамика расходов по проектам за год
- Топ проектов по расходам
- Сравнение расходов между месяцами


## 🔧 Управление проектом

### Полезные команды

```bash
# Показать все доступные команды
make help

# Запуск и остановка
make docker-up              # Запустить все сервисы
make docker-down            # Остановить все сервисы
make docker-logs            # Показать логи всех сервисов

# Настройка
make setup-redash           # Настроить Redash
make setup-dashboards       # Настроить дашборды (использует данные из .env)
make setup-dashboards-only  # Настроить только дашборды (без создания администратора)

# Полная установка
make docker-setup-complete  # Полная установка с дашбордами (автоматически, если настроен .env)
make docker-fresh-install  # Переустановка с нуля

# Локальная разработка
make run-once               # Запустить ETL один раз
make test                   # Запустить тесты
```

### ⏱️ Время установки

- **Первый запуск**: 5-8 минут (загрузка образов + сбор данных)
- **Повторные запуски**: 1-2 минуты
- **Сбор данных ETL**: 3-5 минут (зависит от объема данных Selectel)

### 🤖 Автоматическая настройка дашбордов

Команда `make docker-setup-complete` **автоматически** настраивает дашборды, если:

✅ **В файле `.env` указаны переменные:**
```bash
REDASH_ADMIN_EMAIL=admin@selectel.local
REDASH_ADMIN_PASSWORD=admin123
```

**Процесс автоматической настройки:**

1. **Создание администратора** (если нужно):
   - Система автоматически создает первого администратора
   - Использует данные из `.env` файла

2. **Настройка дашбордов**:
   - Создается источник данных PostgreSQL
   - Создаются 4 готовых запроса
   - Создается основной дашборд

❌ **Если переменных нет** - показывается инструкция для ручной настройки:
```bash
# Сначала укажите переменные в .env, затем:
make setup-dashboards
```

**Результат автоматической настройки:**
- 🔗 Источник данных PostgreSQL
- 📊 4 готовых запроса (балансы, прогнозы, проекты, транзакции)  
- 📈 1 основной дашборд со всеми визуализациями

**Альтернативный способ (если автоматическое создание не работает):**
1. Откройте http://localhost:5000/setup
2. Создайте администратора вручную (используйте данные из `.env`)
3. Выполните `make setup-dashboards-only` (пропускает создание администратора)

### 🔧 Устранение неполадок

#### Проблема: "Контейнеры не запускаются"
```bash
# Проверьте логи
docker compose logs

# Пересоберите образы
make docker-fresh-install
```

#### Проблема: "ETL не собирает данные"
```bash
# Проверьте логи ETL
docker compose logs selectel-etl

# Проверьте API токен в .env файле
```

#### Проблема: "Redash не открывается"
```bash
# Проверьте статус сервисов
docker compose ps

# Подождите 2-3 минуты после запуска
# Откройте http://localhost:5000
```

### 📊 Локальная разработка (без Docker)

```bash
make install            # Установка зависимостей
make setup             # Настройка проекта
make init-db           # Инициализация БД
make run-once          # Запуск ETL однократно
make run               # Запуск ETL в режиме демона

# 📝 Логи
make logs              # Локальные логи
make docker-logs       # Docker логи

# Очистка
make clean

# Docker команды
make docker-build
make docker-up
make docker-down
make docker-logs
```

## 📁 Структура проекта

```
redash-std/
├── selectel_etl.py          # Основной ETL-скрипт
├── models.py                # SQLAlchemy модели
├── init_db.py              # Инициализация БД
├── test_etl.py             # Тесты системы
├── requirements.txt         # Python зависимости
├── config.env.example      # Пример конфигурации
├── redash_queries.sql      # SQL-запросы для Redash
├── swagger.yaml            # OpenAPI/Swagger документация API
├── swagger.html            # Swagger UI для просмотра API
├── setup_redash.sh         # Автоматическая настройка Redash
├── docker-compose.yml      # Docker конфигурация
├── Dockerfile              # Docker образ
├── init.sql               # Инициализация PostgreSQL
├── cron_etl.sh           # Скрипт для cron
├── Makefile              # Команды управления
├── logs/                 # Директория логов
└── README.md            # Документация
```

## 📚 API Документация

### Swagger/OpenAPI
Полная документация Selectel Billing API доступна в формате OpenAPI 3.0:

- **swagger.yaml** - OpenAPI спецификация в формате YAML
- **swagger.html** - Интерактивная Swagger UI документация

#### Просмотр документации:
```bash
# Открыть swagger.html в браузере для интерактивного просмотра
open swagger.html
```

#### Основные эндпоинты:
- `GET /v3/balances` - Получение информации о балансах
- `GET /v2/billing/prediction` - Получение прогнозов расходов  
- `GET /v2/billing/transactions` - Получение истории транзакций
- `GET /v1/billing/report/by_project/detailed` - Отчеты по проектам

#### Аутентификация:
Все запросы требуют передачи API токена в заголовке `X-Token`.

## 🔒 Безопасность

- API-токен хранится в переменных окружения
- Пользователь БД создается с минимальными правами
- Логи не содержат чувствительной информации
- Docker контейнеры запускаются от непривилегированного пользователя

## 🚨 Мониторинг и алерты

### Настройка алертов в Redash

1. **Алерт на низкий баланс**:
```sql
SELECT 
    account_id,
    currency,
    amount,
    credit_limit,
    CASE 
        WHEN amount < credit_limit * 0.1 THEN 'CRITICAL'
        WHEN amount < credit_limit * 0.3 THEN 'WARNING'
        ELSE 'OK'
    END as balance_status
FROM balances 
WHERE fetched_at = (SELECT MAX(fetched_at) FROM balances)
    AND amount < credit_limit * 0.3;
```


## 🐛 Устранение неполадок

### Проблемы с подключением к API
- Проверьте правильность API-токена
- Убедитесь в доступности API Selectel
- Проверьте логи: `make logs`

### Проблемы с базой данных
- Проверьте настройки подключения в `.env`
- Убедитесь, что PostgreSQL запущен
- Проверьте права доступа пользователя

### Проблемы с Docker
- Проверьте, что Docker и Docker Compose установлены
- Убедитесь в доступности порта 5432
- Проверьте логи контейнеров: `make docker-logs`

### Проблемы с Redash
- **Ошибка "relation 'organizations' does not exist"**: 
  - Запустите `make setup-redash` для инициализации БД
  - Или используйте `make docker-setup-full` для полной настройки
- **Redash не отвечает**: Подождите 1-2 минуты после запуска контейнеров
- **Нет пользователей**: Откройте http://localhost:5000/setup для создания администратора

## 📝 Логирование

Логи сохраняются в директории `logs/`:
- `selectel_etl.log` - основные логи ETL
- `cron.log` - логи выполнения через cron

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License

## 📞 Поддержка

При возникновении проблем создайте Issue в репозитории или обратитесь к документации.
