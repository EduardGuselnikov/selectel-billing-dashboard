#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы ETL системы
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from models import create_session, Balance, Prediction, Transaction, ProjectReport

load_dotenv()

def test_database_connection():
    """Тест подключения к базе данных"""
    try:
        session = create_session()
        session.execute("SELECT 1")
        session.close()
        print("✅ Подключение к базе данных успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def test_api_connection():
    """Тест подключения к API Selectel"""
    import requests
    
    api_token = os.getenv('SELECTEL_API_TOKEN')
    base_url = os.getenv('SELECTEL_API_BASE_URL', 'https://api.selectel.ru')
    
    if not api_token:
        print("❌ SELECTEL_API_TOKEN не установлен")
        return False
    
    headers = {
        'X-Auth-Token': api_token,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{base_url}/v3/balances", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Подключение к API Selectel успешно")
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False

def test_data_models():
    """Тест моделей данных"""
    try:
        session = create_session()
        
        # Проверка таблиц
        tables = ['balances', 'predictions', 'transactions', 'project_reports']
        for table in tables:
            result = session.execute(f"SELECT COUNT(*) FROM {table}")
            count = result.scalar()
            print(f"✅ Таблица {table}: {count} записей")
        
        session.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки моделей данных: {e}")
        return False

def test_etl_process():
    """Тест ETL процесса"""
    try:
        from selectel_etl import SelectelETL
        
        etl = SelectelETL()
        print("✅ ETL объект создан успешно")
        
        # Тест одного запроса
        data = etl.make_request('/v3/balances')
        if data:
            print("✅ API запрос выполнен успешно")
            return True
        else:
            print("❌ API запрос не вернул данных")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования ETL: {e}")
        return False

def check_environment():
    """Проверка переменных окружения"""
    required_vars = [
        'SELECTEL_API_TOKEN',
        'DB_HOST',
        'DB_PORT',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ Все необходимые переменные окружения установлены")
        return True

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование ETL системы Selectel Billing")
    print("=" * 50)
    
    tests = [
        ("Проверка переменных окружения", check_environment),
        ("Подключение к базе данных", test_database_connection),
        ("Подключение к API Selectel", test_api_connection),
        ("Проверка моделей данных", test_data_models),
        ("Тест ETL процесса", test_etl_process),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   Тест '{test_name}' не прошел")
    
    print("\n" + "=" * 50)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно! Система готова к работе.")
        return 0
    else:
        print("⚠️  Некоторые тесты не прошли. Проверьте конфигурацию.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 