#!/bin/bash

# Скрипт автоматической настройки Redash
# Инициализирует базу данных и создает первого пользователя

set -e

echo "🚀 Начинаем настройку Redash..."

# Ждем, пока PostgreSQL будет готов
echo "⏳ Ожидание готовности PostgreSQL..."
until docker compose exec postgres pg_isready -U postgres -q; do
    echo "   PostgreSQL еще не готов, ждем..."
    sleep 2
done
echo "✅ PostgreSQL готов"

# Ждем, пока Redash сервер запустится
echo "⏳ Ожидание запуска Redash сервера..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker compose exec redash-server curl -f http://localhost:5000/ping > /dev/null 2>&1; then
        echo "✅ Redash сервер запущен"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Попытка $attempt/$max_attempts..."
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Не удалось дождаться запуска Redash сервера"
    exit 1
fi

# Проверяем, инициализирована ли база данных Redash
echo "🔍 Проверяем состояние базы данных Redash..."
table_count=$(docker compose exec postgres psql -U redash -d redash -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

if [ "$table_count" -eq "0" ] || [ -z "$table_count" ]; then
    echo "📊 Инициализируем базу данных Redash..."
    docker compose exec redash-server /app/bin/docker-entrypoint create_db
    echo "✅ База данных Redash инициализирована"
    
    # Перезапускаем сервисы Redash после инициализации
    echo "🔄 Перезапускаем сервисы Redash..."
    docker compose restart redash-server redash-worker redash-scheduler
    
    # Ждем перезапуска
    sleep 10
    echo "✅ Сервисы Redash перезапущены"
else
    echo "✅ База данных Redash уже инициализирована ($table_count таблиц)"
fi

# Проверяем, есть ли пользователи
echo "👤 Проверяем наличие пользователей..."
user_count=$(docker compose exec postgres psql -U redash -d redash -t -c "SELECT count(*) FROM users;" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$user_count" -eq "0" ] || [ -z "$user_count" ]; then
    echo "👤 Создаем первого администратора..."
    
    # Пытаемся создать пользователя через API setup
    echo "🌐 Настройка через веб-интерфейс доступна по адресу:"
    echo "   http://localhost:5000/setup"
    echo ""
    echo "📝 Рекомендуемые настройки:"
    echo "   Email: admin@selectel.local"
    echo "   Password: admin123"
    echo "   Organization: Selectel Billing"
    echo ""
    echo "💡 После создания администратора добавьте источник данных PostgreSQL:"
    echo "   Host: postgres"
    echo "   Port: 5432"
    echo "   User: selectel_user"
    echo "   Password: selectel_password"
    echo "   Database: selectel_billing"
else
    echo "✅ Пользователи уже существуют ($user_count пользователей)"
fi

echo ""
echo "🎉 Настройка Redash завершена!"
echo "🌐 Redash доступен по адресу: http://localhost:5000"
echo "📊 База данных selectel_billing готова для подключения"
echo ""
echo "🚀 Для автоматической настройки дашбордов:"
echo "   1. Укажите в .env файле: REDASH_ADMIN_EMAIL и REDASH_ADMIN_PASSWORD"
echo "   2. Выполните: make setup-dashboards"
echo ""
