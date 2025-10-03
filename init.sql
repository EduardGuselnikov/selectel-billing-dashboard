-- Инициализация базы данных для Selectel Billing ETL
-- Этот скрипт выполняется при первом запуске PostgreSQL контейнера

-- Пользователь и БД для приложения ETL создаются автоматически через переменные окружения:
-- POSTGRES_USER=${DB_USER}, POSTGRES_PASSWORD=${DB_PASSWORD}, POSTGRES_DB=${DB_NAME}

-- Выдаем права пользователю на базу selectel_billing
GRANT ALL PRIVILEGES ON DATABASE selectel_billing TO selectel_user;
\connect selectel_billing
GRANT ALL PRIVILEGES ON SCHEMA public TO selectel_user;

-- Создаем пользователь redash для Redash (если отсутствует)
-- Используем дефолтный пароль, который можно изменить через переменные окружения в docker-compose.yml
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'redash') THEN
      CREATE ROLE redash LOGIN PASSWORD 'redash_password';
   END IF;
END
$do$;

-- Создаем базу redash (если отсутствует)
SELECT 'CREATE DATABASE redash OWNER redash'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='redash') \gexec

-- Подключаемся к базе redash и выдаем права
\connect redash
ALTER SCHEMA public OWNER TO redash;