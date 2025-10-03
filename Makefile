.PHONY: help install setup run run-once logs clean docker-build docker-up docker-down docker-logs test

# Переменные
PYTHON = python3
PIP = pip3
DOCKER_COMPOSE = docker-compose

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	$(PIP) install -r requirements.txt

setup: ## Настройка проекта (создание .env файла)
	@if [ ! -f .env ]; then \
		cp config.env.example .env; \
		echo "Создан файл .env. Отредактируйте его с вашими настройками."; \
	else \
		echo "Файл .env уже существует."; \
	fi

init-db: ## Инициализация базы данных
	$(PYTHON) init_db.py

run: ## Запустить ETL в режиме демона
	$(PYTHON) selectel_etl.py

run-once: ## Запустить ETL один раз
	$(PYTHON) selectel_etl.py --run-once

logs: ## Показать логи
	@if [ -f logs/selectel_etl.log ]; then \
		tail -f logs/selectel_etl.log; \
	else \
		echo "Файл логов не найден."; \
	fi

clean: ## Очистить логи и временные файлы
	rm -rf logs/*
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

docker-build: ## Собрать Docker образ
	$(DOCKER_COMPOSE) build

docker-up: ## Запустить сервисы в Docker
	$(DOCKER_COMPOSE) up -d
	@echo "Сервисы запущены. Redash: http://localhost:5000"

docker-logs: ## Показать логи Docker контейнеров
	$(DOCKER_COMPOSE) logs -f

docker-down: ## Остановить Docker сервисы
	$(DOCKER_COMPOSE) down

test: ## Запустить тесты
	$(PYTHON) test_etl.py

cron-setup: ## Настроить cron для автоматического запуска
	@echo "Добавьте следующую строку в crontab (crontab -e):"
	@echo "0 * * * * $(shell pwd)/cron_etl.sh"

# Создание директорий
setup-dirs:
	mkdir -p logs
	chmod +x cron_etl.sh

# Полная установка
install-all: setup-dirs install setup init-db ## Полная установка проекта 

setup-redash: ## Настроить Redash (инициализация БД и создание пользователя)
	@echo "🚀 Настройка Redash..."
	chmod +x setup_redash.sh
	./setup_redash.sh

setup-dashboards: ## Настроить дашборды Redash (использует REDASH_ADMIN_EMAIL и REDASH_ADMIN_PASSWORD из .env)
	@echo "📊 Настройка дашбордов Redash..."
	@if [ -f .env ]; then \
		if grep -q "REDASH_ADMIN_EMAIL=" .env && grep -q "REDASH_ADMIN_PASSWORD=" .env; then \
			echo "✅ Переменные Redash найдены в .env, запускаем настройку..."; \
			docker compose exec selectel-etl python setup_redash_dashboards.py; \
		else \
			echo "❌ Необходимо указать REDASH_ADMIN_EMAIL и REDASH_ADMIN_PASSWORD в .env файле"; \
			echo "Пример в .env:"; \
			echo "REDASH_ADMIN_EMAIL=admin@selectel.local"; \
			echo "REDASH_ADMIN_PASSWORD=admin123"; \
			exit 1; \
		fi \
	else \
		echo "❌ Файл .env не найден. Скопируйте .env.example в .env и настройте переменные."; \
		exit 1; \
	fi

setup-dashboards-only: ## Настроить только дашборды (без создания администратора)
	@echo "📊 Настройка дашбордов Redash (пропуск создания администратора)..."
	@if [ -f .env ]; then \
		if grep -q "REDASH_ADMIN_EMAIL=" .env && grep -q "REDASH_ADMIN_PASSWORD=" .env; then \
			echo "✅ Переменные Redash найдены в .env, запускаем настройку..."; \
			SKIP_ADMIN_CREATION=true docker compose exec selectel-etl python setup_redash_dashboards.py; \
		else \
			echo "❌ Необходимо указать REDASH_ADMIN_EMAIL и REDASH_ADMIN_PASSWORD в .env файле"; \
			exit 1; \
		fi \
	else \
		echo "❌ Файл .env не найден."; \
		exit 1; \
	fi

docker-setup-full: docker-up setup-redash ## Запустить все сервисы и настроить Redash
	@echo "✅ Полная настройка завершена!"
	@echo "🌐 Redash доступен: http://localhost:5000"
	@echo "📊 Для подключения к данным используйте:"
	@echo "   Host: postgres, Port: 5432, Database: selectel_billing"
	@echo "   User: selectel_user, Password: selectel_password"

docker-fresh-install: docker-down docker-build docker-up setup-redash ## Полная переустановка с нуля

docker-setup-complete: docker-up setup-redash ## Полная настройка с дашбордами (использует данные из .env)
	@echo "🎯 Запуск полной настройки с дашбордами..."
	@if [ -f .env ]; then \
		if grep -q "REDASH_ADMIN_EMAIL=" .env && grep -q "REDASH_ADMIN_PASSWORD=" .env; then \
			echo "✅ Найдены переменные Redash в .env, запускаем автоматическую настройку дашбордов..."; \
			$(MAKE) setup-dashboards; \
		else \
			echo "⚠️  Для автоматической настройки дашбордов укажите в .env файле:"; \
			echo "   REDASH_ADMIN_EMAIL=admin@selectel.local"; \
			echo "   REDASH_ADMIN_PASSWORD=admin123"; \
			echo "   Затем выполните: make setup-dashboards"; \
		fi \
	else \
		echo "⚠️  Файл .env не найден. Скопируйте .env.example в .env и настройте переменные."; \
	fi
	@echo "🎉 Полная настройка завершена!"