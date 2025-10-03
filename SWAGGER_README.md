# Selectel Billing API Documentation

## 📖 О документации

Эта документация описывает API эндпоинты Selectel Billing, которые используются в ETL системе для сбора данных о:
- Балансах аккаунта
- Прогнозах расходов
- Истории транзакций
- Отчетах по проектам

## 🌐 Просмотр документации

### Вариант 1: Swagger UI (рекомендуется)
Откройте файл `swagger.html` в браузере для интерактивного просмотра:

```bash
# Linux/macOS
open swagger.html

# Windows
start swagger.html
```

### Вариант 2: Онлайн редактор
1. Откройте [Swagger Editor](https://editor.swagger.io/)
2. Скопируйте содержимое файла `swagger.yaml`
3. Вставьте в редактор

### Вариант 3: VS Code
Установите расширение "Swagger Viewer" и откройте `swagger.yaml`

## 🔑 Аутентификация

Все API запросы требуют аутентификации через заголовок:
```
X-Token: YOUR_API_TOKEN
```

Получить API токен можно в личном кабинете Selectel.

## 📋 Основные эндпоинты

| Эндпоинт | Описание | Частота использования |
|----------|----------|----------------------|
| `GET /v3/balances` | Текущие балансы | Каждый час |
| `GET /v2/billing/prediction` | Прогнозы расходов | Каждый час |
| `GET /v2/billing/transactions` | История транзакций | Каждый час (последние 2 часа) |
| `GET /v1/billing/report/by_project/detailed` | Отчеты по проектам | Ежедневно (текущий месяц) |

## 🔧 Использование в коде

Все эндпоинты реализованы в файле `selectel_etl.py`:

- `fetch_balances()` - использует `/v3/balances`
- `fetch_predictions()` - использует `/v2/billing/prediction`
- `fetch_transactions()` - использует `/v2/billing/transactions`
- `fetch_project_reports()` - использует `/v1/billing/report/by_project/detailed`

## 📊 Структуры данных

### Балансы
```json
{
  "balance_id": "12345",
  "balance_type": "main",
  "value": 150000
}
```

### Транзакции
```json
{
  "id_meta": {"id": [687288652]},
  "transaction_type": "withdraw",
  "balance": "bonus",
  "price": -20943,
  "created": "2025-09-11T00:40:27.572253"
}
```

### Проекты
```json
{
  "id": "038f673576ec46b2849a8bc3411d194e",
  "name": "E-learn_",
  "paid_by_balance": [
    {"balance": "main", "value": 16397012},
    {"balance": "bonus", "value": 80761}
  ]
}
```

## ❗ Важные замечания

1. **Лимиты**: Параметр `limit` обязателен для `/v2/billing/transactions` (максимум 500)
2. **Даты**: Используйте формат ISO 8601 (`2025-09-11T00:00:00`)
3. **Пагинация**: Используйте `offset` для больших наборов данных
4. **Ошибки**: API возвращает статус `error` в случае проблем

## 🔗 Полезные ссылки

- [Selectel API Documentation](https://selectel.ru/api/)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
