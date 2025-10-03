#!/bin/bash
# Скрипт для создания пользователя redash с паролем из переменной окружения

set -e

# Получаем пароль из переменной окружения или используем дефолтный
REDASH_PASSWORD="${POSTGRES_REDASH_PASSWORD:-redash_password}"

# Создаем пользователя redash если он не существует
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'redash') THEN
            CREATE ROLE redash LOGIN PASSWORD '$REDASH_PASSWORD';
        END IF;
    END
    \$\$;
    
    SELECT 'CREATE DATABASE redash OWNER redash'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='redash') \\gexec
EOSQL

# Подключаемся к базе redash и выдаем права
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "redash" <<-EOSQL
    ALTER SCHEMA public OWNER TO redash;
EOSQL

echo "Пользователь redash создан успешно"
