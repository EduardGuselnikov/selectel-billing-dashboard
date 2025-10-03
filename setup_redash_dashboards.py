#!/usr/bin/env python3
"""
Скрипт для автоматической настройки дашбордов и запросов в Redash
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedashSetup:
    def __init__(self, redash_url: str = "http://localhost:5000", admin_email: str = None, admin_password: str = None):
        self.redash_url = redash_url.rstrip('/')
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.session = requests.Session()
        self.api_key = None
        self.data_source_id = None
        
    def wait_for_redash(self, max_attempts: int = 30, delay: int = 5):
        """Ожидание готовности Redash"""
        logger.info("Ожидание готовности Redash...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.redash_url}/ping", timeout=10)
                if response.status_code == 200:
                    logger.info("Redash готов к работе")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            logger.info(f"Попытка {attempt + 1}/{max_attempts}, ожидание {delay} секунд...")
            time.sleep(delay)
        
        raise Exception("Redash не отвечает после максимального количества попыток")
    
    def check_and_create_admin(self) -> bool:
        """Проверка и создание администратора, если нужно"""
        logger.info("Проверка необходимости первичной настройки...")
        
        # Проверяем, нужна ли первичная настройка
        try:
            # Используем сессию для сохранения cookies
            session = requests.Session()
            response = session.get(f"{self.redash_url}/setup", timeout=10)
            if response.status_code == 200 and "Initial Setup" in response.text:
                logger.info("Требуется первичная настройка, создаем администратора...")
                
                # Извлекаем CSRF токен из HTML
                csrf_token = None
                if 'csrf_token' in response.text:
                    import re
                    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                        logger.info("CSRF токен получен")
                
                # Создаем первого администратора с правильными полями
                setup_data = {
                    'name': 'Admin',
                    'email': self.admin_email,
                    'password': self.admin_password,
                    'org_name': 'Selectel Billing',
                    'security_notifications': 'y',
                    'newsletter': 'y'
                }
                
                if csrf_token:
                    setup_data['csrf_token'] = csrf_token
                
                # Отправляем как form-data с сессией
                response = session.post(f"{self.redash_url}/setup", data=setup_data, timeout=30)
                logger.info(f"Ответ сервера: {response.status_code}")
                logger.info(f"Содержимое ответа: {response.text[:200]}...")
                
                if response.status_code in [200, 302]:  # 302 - редирект после успешного создания
                    logger.info("Администратор успешно создан")
                    # Даем время Redash обработать создание пользователя
                    logger.info("Ожидание обработки создания пользователя...")
                    time.sleep(5)
                    return True
                else:
                    logger.error(f"Ошибка создания администратора: {response.status_code} - {response.text}")
                    return False
            else:
                logger.info("Первичная настройка уже выполнена")
                return True
        except Exception as e:
            logger.error(f"Ошибка проверки настройки: {e}")
            return False
    
    def login_and_get_api_key(self) -> str:
        """Получение API ключа администратора"""
        if not self.admin_email or not self.admin_password:
            raise ValueError("Необходимо указать email и пароль администратора")
        
        # Попытка входа
        login_data = {
            'email': self.admin_email,
            'password': self.admin_password
        }
        
        # Попытка входа с несколькими попытками
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Сначала получаем страницу логина для CSRF токена
                login_page = self.session.get(f"{self.redash_url}/login")
                csrf_token = None
                if login_page.status_code == 200 and 'csrf_token' in login_page.text:
                    import re
                    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                
                # Подготавливаем данные для входа (как в вашем curl)
                login_form_data = {
                    'email': self.admin_email,
                    'password': self.admin_password,
                    'next': ''  # Важное поле!
                }
                if csrf_token:
                    login_form_data['csrf_token'] = csrf_token
                
                # Пробуем войти через form-data с правильными заголовками
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                response = self.session.post(f"{self.redash_url}/login", 
                                           data=login_form_data, 
                                           headers=headers)
                logger.info(f"Ответ логина: {response.status_code}")
                logger.info(f"Данные для входа: email={self.admin_email}, csrf_token={'есть' if csrf_token else 'нет'}")
                logger.info(f"Содержимое ответа логина: {response.text[:300]}...")
                
                # 302 - это успешный редирект после логина!
                if response.status_code == 302:
                    logger.info("Успешный логин (редирект 302)")
                elif response.status_code != 200:
                    logger.warning(f"Попытка входа {attempt + 1}/{max_attempts} неудачна: {response.status_code}")
                    if attempt < max_attempts - 1:
                        time.sleep(3)
                        continue
                    raise Exception(f"Ошибка входа в Redash: {response.status_code}")
                
                # Получение API ключа через /api/session (стабильнее чем /api/users/me)
                session_response = self.session.get(f"{self.redash_url}/api/session")
                if session_response.status_code == 200:
                    session_info = session_response.json()
                    user_id = session_info.get('user', {}).get('id')
                    if user_id:
                        # Получаем API ключ пользователя
                        user_detail_response = self.session.get(f"{self.redash_url}/api/users/{user_id}")
                        if user_detail_response.status_code == 200:
                            user_info = user_detail_response.json()
                            self.api_key = user_info.get('api_key')
                            if self.api_key:
                                logger.info("API ключ успешно получен")
                                return self.api_key
                
                logger.warning(f"Попытка получения API ключа {attempt + 1}/{max_attempts} неудачна")
                if attempt < max_attempts - 1:
                    time.sleep(3)
                    continue
                raise Exception("Не удалось получить API ключ после нескольких попыток")
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    logger.warning(f"Попытка {attempt + 1}/{max_attempts} неудачна: {e}")
                    time.sleep(3)
                else:
                    raise e
    
    def create_data_source(self) -> int:
        """Создание источника данных PostgreSQL"""
        logger.info("Создание источника данных PostgreSQL...")
        
        # Проверяем, существует ли уже источник данных
        headers = {'Authorization': f'Key {self.api_key}'}
        response = self.session.get(f"{self.redash_url}/api/data_sources", headers=headers)
        
        if response.status_code == 200:
            data_sources = response.json()
            for ds in data_sources:
                if ds.get('name') == 'Selectel Billing DB':
                    logger.info(f"Источник данных уже существует с ID: {ds['id']}")
                    self.data_source_id = ds['id']
                    return ds['id']
        
        # Создаем новый источник данных
        data_source_config = {
            'name': 'Selectel Billing DB',
            'type': 'pg',
            'options': {
                'host': os.getenv('POSTGRES_HOST', 'postgres'),
                'port': int(os.getenv('POSTGRES_PORT', 5432)),
                'user': os.getenv('POSTGRES_USER', 'selectel_user'),
                'password': os.getenv('DB_PASSWORD', 'your_secure_password_here'),
                'dbname': os.getenv('POSTGRES_DB', 'selectel_billing')
            }
        }
        
        response = self.session.post(
            f"{self.redash_url}/api/data_sources",
            json=data_source_config,
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Ошибка создания источника данных: {response.status_code} - {response.text}")
        
        data_source = response.json()
        self.data_source_id = data_source['id']
        logger.info(f"Источник данных создан с ID: {self.data_source_id}")
        return self.data_source_id
    
    def create_query(self, name: str, sql: str, description: str = "") -> int:
        """Создание запроса в Redash"""
        logger.info(f"Создание запроса: {name}")
        
        headers = {'Authorization': f'Key {self.api_key}'}
        query_data = {
            'name': name,
            'query': sql,
            'description': description,
            'data_source_id': self.data_source_id,
            'options': {}
        }
        
        response = self.session.post(
            f"{self.redash_url}/api/queries",
            json=query_data,
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Ошибка создания запроса '{name}': {response.status_code} - {response.text}")
        
        query = response.json()
        logger.info(f"Запрос '{name}' создан с ID: {query['id']}")
        return query['id']
    
    def create_dashboard(self, name: str, query_ids: List[int]) -> int:
        """Создание дашборда с виджетами"""
        logger.info(f"Создание дашборда: {name}")
        
        headers = {'Authorization': f'Key {self.api_key}'}
        dashboard_data = {
            'name': name,
            'tags': ['selectel', 'billing', 'auto-generated']
        }
        
        response = self.session.post(
            f"{self.redash_url}/api/dashboards",
            json=dashboard_data,
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Ошибка создания дашборда '{name}': {response.status_code} - {response.text}")
        
        dashboard = response.json()
        dashboard_id = dashboard['id']
        logger.info(f"Дашборд '{name}' создан с ID: {dashboard_id}")
        
        # Добавляем виджеты на дашборд
        for i, query_id in enumerate(query_ids):
            self.add_widget_to_dashboard(dashboard_id, query_id, i)
        
        return dashboard_id
    
    def add_widget_to_dashboard(self, dashboard_id: int, query_id: int, position: int):
        """Добавление виджета на дашборд"""
        headers = {'Authorization': f'Key {self.api_key}'}
        
        # Сначала выполняем запрос для получения результатов
        response = self.session.post(
            f"{self.redash_url}/api/queries/{query_id}/refresh",
            headers=headers
        )
        
        if response.status_code == 200:
            time.sleep(2)  # Ждем выполнения запроса
        
        # Получаем информацию о запросе
        response = self.session.get(f"{self.redash_url}/api/queries/{query_id}", headers=headers)
        if response.status_code != 200:
            logger.warning(f"Не удалось получить информацию о запросе {query_id}")
            return
        
        query_info = response.json()
        
        # Создаем виджет
        widget_data = {
            'dashboard_id': dashboard_id,
            'visualization_id': query_info.get('visualizations', [{}])[0].get('id'),
            'width': 2,
            'options': {
                'position': {
                    'col': (position % 2) * 3,
                    'row': (position // 2) * 3,
                    'sizeX': 3,
                    'sizeY': 3
                }
            }
        }
        
        response = self.session.post(
            f"{self.redash_url}/api/widgets",
            json=widget_data,
            headers=headers
        )
        
        if response.status_code == 200:
            logger.info(f"Виджет для запроса {query_id} добавлен на дашборд")
        else:
            logger.warning(f"Ошибка добавления виджета: {response.status_code}")
    
    def load_config(self, config_file: str = "redash_config.json") -> dict:
        """Загрузка конфигурации из JSON файла"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Файл конфигурации {config_file} не найден")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {config_file}: {e}")
            raise
    
    def setup_default_dashboards(self):
        """Настройка дефолтных дашбордов и запросов"""
        logger.info("Начало настройки дефолтных дашбордов...")
        
        # Загружаем конфигурацию
        config = self.load_config()
        
        # Получаем запросы из конфигурации
        queries_to_create = config.get('queries', [])
        
        # Создаем запросы
        created_query_ids = []
        for query_config in queries_to_create:
            try:
                query_id = self.create_query(
                    query_config['name'],
                    query_config['sql'],
                    query_config['description']
                )
                created_query_ids.append(query_id)
            except Exception as e:
                logger.error(f"Ошибка создания запроса '{query_config['name']}': {e}")
        
        # Создаем словарь для быстрого поиска ID запросов по имени
        query_name_to_id = {}
        for i, query_config in enumerate(queries_to_create):
            if i < len(created_query_ids):
                query_name_to_id[query_config['name']] = created_query_ids[i]
        
        # Создаем дашборды из конфигурации
        dashboards_config = config.get('dashboards', [])
        for dashboard_config in dashboards_config:
            try:
                dashboard_name = dashboard_config['name']
                query_names = dashboard_config.get('queries', [])
                
                # Получаем ID запросов для дашборда
                dashboard_query_ids = []
                for query_name in query_names:
                    if query_name in query_name_to_id:
                        dashboard_query_ids.append(query_name_to_id[query_name])
                    else:
                        logger.warning(f"Запрос '{query_name}' не найден для дашборда '{dashboard_name}'")
                
                if dashboard_query_ids:
                    self.create_dashboard(dashboard_name, dashboard_query_ids)
                    logger.info(f"Дашборд '{dashboard_name}' создан с {len(dashboard_query_ids)} виджетами")
                else:
                    logger.warning(f"Не удалось создать дашборд '{dashboard_name}' - нет доступных запросов")
                    
            except Exception as e:
                logger.error(f"Ошибка создания дашборда '{dashboard_config.get('name', 'Unknown')}': {e}")
        
        if created_query_ids:
            logger.info("Настройка дашбордов завершена успешно!")
        else:
            logger.warning("Не удалось создать ни одного запроса")

def main():
    """Основная функция"""
    # Получаем параметры из переменных окружения
    redash_url = os.getenv('REDASH_URL', 'http://localhost:5000')
    admin_email = os.getenv('REDASH_ADMIN_EMAIL')
    admin_password = os.getenv('REDASH_ADMIN_PASSWORD')
    
    if not admin_email or not admin_password:
        logger.error("Необходимо установить переменные окружения REDASH_ADMIN_EMAIL и REDASH_ADMIN_PASSWORD")
        return 1
    
    try:
        setup = RedashSetup(redash_url, admin_email, admin_password)
        
        # Ожидаем готовности Redash
        setup.wait_for_redash()
        
        # Проверяем и создаем администратора, если нужно (если не пропускаем этот шаг)
        skip_admin_creation = os.getenv('SKIP_ADMIN_CREATION', '').lower() == 'true'
        if not skip_admin_creation:
            if not setup.check_and_create_admin():
                logger.error("Не удалось создать администратора")
                return 1
        else:
            logger.info("Пропуск создания администратора (SKIP_ADMIN_CREATION=true)")
        
        # Получаем API ключ
        setup.login_and_get_api_key()
        
        # Создаем источник данных
        setup.create_data_source()
        
        # Настраиваем дашборды
        setup.setup_default_dashboards()
        
        logger.info("🎉 Настройка Redash завершена успешно!")
        logger.info(f"Откройте {redash_url} для просмотра дашбордов")
        
        return 0
        
    except Exception as e:
        logger.error(f"Ошибка настройки Redash: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
