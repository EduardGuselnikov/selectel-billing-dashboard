#!/bin/bash

# Скрипт для запуска ETL через cron
# Добавить в crontab: 0 * * * * /path/to/cron_etl.sh

# Путь к проекту
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Переход в директорию проекта
cd "$PROJECT_DIR"

# Активация виртуального окружения (если используется)
# source venv/bin/activate

# Запуск ETL-скрипта
python selectel_etl.py --run-once

# Логирование результата
if [ $? -eq 0 ]; then
    echo "$(date): ETL выполнен успешно" >> logs/cron.log
else
    echo "$(date): Ошибка при выполнении ETL" >> logs/cron.log
fi 