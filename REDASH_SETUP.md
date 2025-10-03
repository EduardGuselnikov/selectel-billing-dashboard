# Настройка Redash - Подключение к PostgreSQL

## Добавление PostgreSQL datasource

Выполните следующие шаги для подключения к базе данных ETL:

### 1. Откройте Redash в браузере
```
http://localhost:5000
```

### 2. Войдите в систему
- **Email**: `admin@selectel.local` (или значение из `REDASH_ADMIN_EMAIL` в .env)
- **Password**: `admin123` (или значение из `REDASH_ADMIN_PASSWORD` в .env)

### 3. Добавьте Data Source
1. Перейдите в **Settings** → **Data Sources**
2. Нажмите **"New Data Source"**
3. Выберите **"PostgreSQL"**

### 4. Заполните параметры подключения:

```
Name: Selectel Billing PostgreSQL
Host: localhost
Port: 5432
User: selectel_user  
Password: selectel_password  (или значение из DB_PASSWORD в .env)
Database Name: selectel_billing
SSL Mode: prefer
```

**Важно**: Если вы подключаетесь из Docker контейнера Redash к PostgreSQL, используйте `Host: postgres` вместо `localhost`.

### 5. Протестируйте подключение
Нажмите **"Test Connection"** - должно появиться сообщение об успешном подключении.

### 6. Сохраните
Нажмите **"Create"**

## Проверка подключения

После добавления datasource выполните тестовый запрос:

```sql
SELECT 
    account_id,
    balance_type,
    amount,
    currency,
    fetched_at
FROM balances 
ORDER BY fetched_at DESC 
LIMIT 10;
```

## Готовые запросы

В файле `redash_queries.sql` находятся готовые SQL-запросы для создания дашборда:

1. **Текущие балансы по типам**
2. **Динамика балансов**  
3. **Прогнозы расходов**
4. **Статистика по проектам**
5. **Алерты на низкий баланс**

## Создание дашборда

1. Создайте новые **Queries** используя SQL из `redash_queries.sql`
2. Для каждого запроса создайте **Visualization** (график, таблица, метрика)
3. Добавьте все визуализации на новый **Dashboard**
4. Настройте **Auto Refresh** для автоматического обновления данных

## Troubleshooting

### Ошибка подключения к базе данных
- Убедитесь, что PostgreSQL запущен: `docker compose ps`
- Проверьте параметры в .env файле
- Используйте `Host: postgres` если Redash запущен в Docker

### Redash не доступен
- Проверьте статус: `docker compose ps`
- Перезапустите сервисы: `docker compose restart redash-server`
- Проверьте логи: `docker compose logs redash-server`

### Нет данных в таблицах
- Запустите ETL: `docker compose run --rm selectel-etl python selectel_etl.py --run-once`
- Проверьте логи ETL: `docker compose logs selectel-etl`

## Переменные окружения для Redash

Добавьте в ваш `.env` файл:

```env
# Redash Admin Settings
REDASH_ADMIN_EMAIL=admin@selectel.local
REDASH_ADMIN_PASSWORD=admin123
REDASH_URL=http://localhost:5000

# Redash Internal Settings
REDASH_DATABASE_URL=postgresql://redash:redash_password@postgres:5432/redash
REDASH_REDIS_URL=redis://redis:6379/0
REDASH_SECRET_KEY=your-secret-key-here
REDASH_COOKIE_SECRET=your-cookie-secret-here
```