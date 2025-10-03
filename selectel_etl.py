#!/usr/bin/env python3
"""
ETL-скрипт для сбора данных Selectel Billing API
"""

import requests
import os
import schedule
import time
from datetime import datetime, timedelta
from loguru import logger
from dotenv import load_dotenv
from models import Balance, Prediction, Transaction, ProjectReport, create_session, init_database

load_dotenv()

class SelectelETL:
    def __init__(self):
        self.api_token = os.getenv('SELECTEL_API_TOKEN')
        self.base_url = os.getenv('SELECTEL_API_BASE_URL', 'https://api.selectel.ru')
        self.headers = {
            'X-Token': self.api_token,
            'Content-Type': 'application/json'
        }
        
        if not self.api_token:
            raise ValueError("SELECTEL_API_TOKEN не установлен в переменных окружения")
        
        # Инициализация базы данных
        init_database()
        logger.info("ETL-система инициализирована")

    def make_request(self, endpoint, params=None):
        """Выполнить HTTP-запрос к API Selectel"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к {url}: {e}")
            return None

    def fetch_balances(self):
        """Получить данные о балансах"""
        logger.info("Запрос данных о балансах...")
        data = self.make_request('/v3/balances')
        
        if not data:
            return
        
        session = create_session()
        try:
            # Получаем данные из правильной структуры ответа
            response_data = data.get('data', {})
            billings = response_data.get('billings', [])
            
            total_balances = 0
            for billing in billings:
                balances = billing.get('balances', [])
                for balance_data in balances:
                    balance = Balance(
                        balance_id=str(balance_data.get('balance_id')),
                        balance_type=balance_data.get('balance_type'),
                        currency='RUB',
                        amount=float(balance_data.get('value', 0)),
                        credit_limit=None,
                        status='active',
                        raw_data=balance_data
                    )
                    session.add(balance)
                    total_balances += 1
            
            session.commit()
            logger.info(f"Сохранено {total_balances} записей о балансах")
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при сохранении балансов: {e}")
        finally:
            session.close()

    def fetch_predictions(self):
        """Получить данные о прогнозах расходов"""
        logger.info("Запрос данных о прогнозах...")
        data = self.make_request('/v2/billing/prediction')
        
        if not data:
            return
        
        session = create_session()
        try:
            response_data = data.get('data', {})
            total_predictions = 0
            
            # Обрабатываем каждый тип баланса из ответа API
            for balance_type, predicted_amount in response_data.items():
                # Пропускаем null значения
                if predicted_amount is None:
                    logger.debug(f"Пропускаем {balance_type}: значение null")
                    continue
                
                prediction = Prediction(
                    balance_type=balance_type,
                    predicted_amount=float(predicted_amount),
                    raw_data=response_data
                )
                session.add(prediction)
                total_predictions += 1
            
            session.commit()
            logger.info(f"Сохранено {total_predictions} записей о прогнозах")
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при сохранении прогнозов: {e}")
        finally:
            session.close()

    def fetch_transactions(self, full_sync=False):
        """Получить транзакции: полная синхронизация с начала года или за последние 2 часа"""
        session = create_session()
        try:
            current_year = datetime.now().year
            end_date = datetime.now()
            
            if full_sync:
                # Полная синхронизация - запрашиваем с начала года
                start_date = datetime(current_year, 1, 1)
                logger.info(f"Полная синхронизация: запрос транзакций с начала года ({start_date.strftime('%Y-%m-%dT%H:%M:%S')}) до сейчас ({end_date.strftime('%Y-%m-%dT%H:%M:%S')})...")
            else:
                # Обычный режим - запрашиваем за последние 2 часа
                start_date = end_date - timedelta(hours=2)
                logger.info(f"Обновление: запрос транзакций за последние 2 часа ({start_date.strftime('%Y-%m-%dT%H:%M:%S')}) до сейчас ({end_date.strftime('%Y-%m-%dT%H:%M:%S')})...")
            
            # Если период большой (больше месяца), разбиваем на части
            if (end_date - start_date).days > 30:
                self._fetch_transactions_in_chunks(session, start_date, end_date)
            else:
                self._fetch_transactions_for_period(session, start_date, end_date)
                
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при сборе транзакций: {e}")
        finally:
            session.close()
    
    def _fetch_transactions_in_chunks(self, session, start_date, end_date):
        """Запросить транзакции частями по месяцам для больших периодов"""
        current_start = start_date
        total_processed = 0
        
        while current_start < end_date:
            # Определяем конец текущего месяца или end_date, если он меньше
            current_end = min(
                datetime(current_start.year, current_start.month + 1, 1) if current_start.month < 12 
                else datetime(current_start.year + 1, 1, 1),
                end_date
            )
            
            logger.info(f"Запрос транзакций за период: {current_start.strftime('%Y-%m-%d')} - {current_end.strftime('%Y-%m-%d')}")
            processed = self._fetch_transactions_for_period(session, current_start, current_end)
            total_processed += processed
            
            # Переходим к следующему месяцу
            if current_start.month == 12:
                current_start = datetime(current_start.year + 1, 1, 1)
            else:
                current_start = datetime(current_start.year, current_start.month + 1, 1)
        
        logger.info(f"Всего обработано транзакций за весь период: {total_processed}")
    
    def _fetch_transactions_for_period(self, session, start_date, end_date):
        """Запросить транзакции за конкретный период"""
        params = {
            'created_from': start_date.strftime('%Y-%m-%dT%H:%M:%S'),
            'created_to': end_date.strftime('%Y-%m-%dT%H:%M:%S'),
            'balances': 'main,vk_rub,bonus',
            'offset': 0,
            'without_removed': 'true',
            'limit': 500
        }
        
        data = self.make_request('/v2/billing/transactions', params)
        
        if not data or data.get('status') != 'success':
            logger.warning(f"Не удалось получить данные о транзакциях за период {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
            return 0
        
        transactions_data = data.get('data', [])
        processed_count = 0
        updated_count = 0
        
        for transaction_data in transactions_data:
            # Извлекаем необходимые поля
            id_list = transaction_data.get('id_meta', {}).get('id', [])
            if not id_list or not isinstance(id_list, list) or len(id_list) == 0:
                logger.warning("Пропускаем транзакцию без ID")
                continue
            
            # Берем минимальное значение из массива ID
            transaction_id = min(id_list)
            
            # Проверяем, существует ли уже транзакция с таким ID
            existing_transaction = session.query(Transaction).filter_by(id=transaction_id).first()
            
            # Извлекаем поля из server_meta.en
            service_name = None
            operation = None
            service = None
            server_meta = transaction_data.get('server_meta', {})
            if isinstance(server_meta, dict) and 'en' in server_meta:
                en_meta = server_meta['en']
                service_name = en_meta.get('full_name')
                operation = en_meta.get('operation')
                service = en_meta.get('service')
            
            # Парсим дату создания
            created_str = transaction_data.get('created')
            created_date = None
            if created_str:
                try:
                    created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Не удалось распарсить дату: {created_str}")
                    created_date = datetime.utcnow()
            
            if existing_transaction:
                # Обновляем существующую транзакцию
                existing_transaction.transaction_type = transaction_data.get('transaction_type')
                existing_transaction.transaction_group = transaction_data.get('transaction_group')
                existing_transaction.balance = transaction_data.get('balance')
                existing_transaction.price = float(transaction_data.get('price', 0))
                existing_transaction.state = transaction_data.get('state')
                existing_transaction.created = created_date
                existing_transaction.service_name = service_name
                existing_transaction.operation = operation
                existing_transaction.service = service
                existing_transaction.raw_data = transaction_data
                existing_transaction.fetched_at = datetime.utcnow()
                updated_count += 1
            else:
                # Создаем новую транзакцию
                transaction = Transaction(
                    id=transaction_id,
                    transaction_type=transaction_data.get('transaction_type'),
                    transaction_group=transaction_data.get('transaction_group'),
                    balance=transaction_data.get('balance'),
                    price=float(transaction_data.get('price', 0)),
                    state=transaction_data.get('state'),
                    created=created_date,
                    service_name=service_name,
                    operation=operation,
                    service=service,
                    raw_data=transaction_data
                )
                session.add(transaction)
            
            processed_count += 1
        
        session.commit()
        logger.info(f"Обработано {processed_count} транзакций за период: {processed_count - updated_count} новых, {updated_count} обновлено")
        return processed_count

    def fetch_project_reports(self, full_sync=False):
        """Получить отчеты по проектам за текущий год"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        session = create_session()
        try:
            # Определяем, за какие месяцы нужно запрашивать данные
            months_to_fetch = []
            
            if full_sync:
                # Полная синхронизация - запрашиваем все месяцы с начала года
                months_to_fetch = list(range(1, current_month + 1))
                logger.info(f"Полная синхронизация отчетов по проектам за {current_year} год (месяцы: {months_to_fetch})...")
            else:
                # Обычный режим - запрашиваем ТОЛЬКО текущий месяц
                months_to_fetch = [current_month]
                logger.info(f"Обновление отчетов по проектам за {current_year} год (только текущий месяц: {current_month})...")
            
            for month in months_to_fetch:
                self._fetch_project_report_for_month(session, current_year, month)
                
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при сборе отчетов по проектам: {e}")
        finally:
            session.close()
    
    def _fetch_project_report_for_month(self, session, year, month):
        """Получить отчет по проектам за конкретный месяц"""
        logger.info(f"Запрос данных по проектам за {month}/{year}...")
        
        params = {
            'year': year,
            'month': month,
            'locale': 'ru'
        }
        
        data = self.make_request('/v1/billing/report/by_project/detailed', params)
        
        if not data or data.get('status') != 'success':
            logger.warning(f"Не удалось получить данные по проектам за {month}/{year}")
            return
        
        report_data = data.get('data', {})
        projects = report_data.get('projects', [])
        
        processed_count = 0
        updated_count = 0
        
        for project in projects:
            project_name = project.get('name')
            if not project_name:
                continue
                
            paid_by_balance = project.get('paid_by_balance', [])
            
            for balance_info in paid_by_balance:
                balance_type = balance_info.get('balance')
                value = balance_info.get('value', 0)
                
                if not balance_type:
                    continue
                
                # Проверяем, существует ли уже запись
                existing_report = session.query(ProjectReport).filter_by(
                    year=year,
                    month=month,
                    project_name=project_name,
                    balance_type=balance_type
                ).first()
                
                if existing_report:
                    # Обновляем существующую запись
                    existing_report.value = float(value)
                    existing_report.raw_data = project
                    existing_report.fetched_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Создаем новую запись
                    project_report = ProjectReport(
                        year=year,
                        month=month,
                        project_name=project_name,
                        balance_type=balance_type,
                        value=float(value),
                        raw_data=project
                    )
                    session.add(project_report)
                
                processed_count += 1
        
        session.commit()
        logger.info(f"Обработано {processed_count} записей по проектам за {month}/{year}: {processed_count - updated_count} новых, {updated_count} обновлено")

    def run_etl(self, full_sync=False):
        """Запустить полный ETL-процесс"""
        logger.info("Начало ETL-процесса")
        start_time = datetime.now()
        
        try:
            self.fetch_balances()
            self.fetch_predictions()
            self.fetch_transactions(full_sync=full_sync)
            self.fetch_project_reports(full_sync=full_sync)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"ETL-процесс завершен за {duration:.2f} секунд")
            
        except Exception as e:
            logger.error(f"Критическая ошибка в ETL-процессе: {e}")

def main():
    """Основная функция для запуска ETL"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Selectel Billing ETL')
    parser.add_argument('--run-once', action='store_true', help='Запустить ETL один раз и завершить')
    args = parser.parse_args()
    
    # Настройка логирования
    logger.add(
        "logs/selectel_etl.log",
        rotation="1 day",
        retention="30 days",
        level=os.getenv('LOG_LEVEL', 'INFO')
    )
    
    try:
        etl = SelectelETL()
        
        if args.run_once:
            # Однократный запуск с полной синхронизацией
            etl.run_etl(full_sync=True)
            logger.info("ETL-процесс завершен (однократный запуск)")
        else:
            # Запуск по расписанию
            interval_hours = int(os.getenv('ETL_INTERVAL_HOURS', 1))
            schedule.every(interval_hours).hours.do(etl.run_etl)
            
            # Первый запуск сразу с полной синхронизацией
            etl.run_etl(full_sync=True)
            
            logger.info(f"ETL-система запущена с интервалом {interval_hours} час(ов)")
            
            # Бесконечный цикл для работы по расписанию
            while True:
                schedule.run_pending()
                time.sleep(60)  # Проверка каждую минуту
                
    except KeyboardInterrupt:
        logger.info("ETL-система остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main() 