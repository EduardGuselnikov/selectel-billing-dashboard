from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Balance(Base):
    __tablename__ = 'balances'
    
    id = Column(Integer, primary_key=True)
    balance_id = Column(String(50), nullable=False)
    balance_type = Column(String(50))
    currency = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)
    credit_limit = Column(Float)
    status = Column(String(20))
    raw_data = Column(JSON)
    fetched_at = Column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    balance_type = Column(String(50), nullable=False)  # primary, storage, vmware, vpc
    predicted_amount = Column(Float, nullable=False)
    raw_data = Column(JSON)
    fetched_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)  # id из id_meta.id[0]
    transaction_type = Column(String(50), nullable=False)
    transaction_group = Column(String(50), nullable=False)
    balance = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    state = Column(String(50), nullable=False)
    created = Column(DateTime, nullable=False)
    service_name = Column(String(255))  # из server_meta.en.full_name
    operation = Column(String(255))  # из server_meta.en.operation
    service = Column(String(255))  # из server_meta.en.service
    raw_data = Column(JSON)
    fetched_at = Column(DateTime, default=datetime.utcnow)

class ProjectReport(Base):
    __tablename__ = 'project_reports'
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    project_name = Column(String(255), nullable=False)
    balance_type = Column(String(50), nullable=False)  # main, bonus
    value = Column(Float, nullable=False)
    raw_data = Column(JSON)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Составной уникальный индекс для предотвращения дублирования
    __table_args__ = (
        {'mysql_engine': 'InnoDB'},
    )


def get_database_url():
    """Получить URL для подключения к базе данных из переменных окружения"""
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    name = os.getenv('DB_NAME', 'selectel_billing')
    user = os.getenv('DB_USER', 'selectel_user')
    password = os.getenv('DB_PASSWORD', '')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"

def create_session():
    """Создать сессию базы данных"""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    return Session()

def init_database():
    """Инициализировать базу данных и создать таблицы"""
    engine = create_engine(get_database_url())
    Base.metadata.create_all(engine) 
    # Легкая миграция: убедиться, что новые колонки существуют
    with engine.connect() as conn:
        # Добавляем колонку balance_type в balances, если её нет
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='balances' AND column_name='balance_type'
                ) THEN
                    ALTER TABLE balances ADD COLUMN balance_type VARCHAR(50);
                END IF;
            END$$;
        """))
        
        # Миграция для таблицы predictions: удаляем старые колонки и добавляем новые
        conn.execute(text("""
            DO $$
            BEGIN
                -- Проверяем, нужна ли миграция (если есть старая колонка period_start)
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='predictions' AND column_name='period_start'
                ) THEN
                    -- Удаляем данные из старой таблицы
                    DELETE FROM predictions;
                    
                    -- Удаляем старые колонки
                    ALTER TABLE predictions DROP COLUMN IF EXISTS period_start;
                    ALTER TABLE predictions DROP COLUMN IF EXISTS period_end;
                    ALTER TABLE predictions DROP COLUMN IF EXISTS confidence_level;
                    ALTER TABLE predictions DROP COLUMN IF EXISTS currency;
                    
                    -- Добавляем новую колонку balance_type, если её нет
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='predictions' AND column_name='balance_type'
                    ) THEN
                        ALTER TABLE predictions ADD COLUMN balance_type VARCHAR(50) NOT NULL DEFAULT 'primary';
                    END IF;
                END IF;
            END$$;
        """))
        
        # Удаление таблицы summary_stats (статистика по проектам больше не нужна)
        conn.execute(text("""
            DROP TABLE IF EXISTS summary_stats;
        """))
        
        # Добавление новых колонок в таблицу transactions
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='transactions' AND column_name='operation'
                ) THEN
                    ALTER TABLE transactions ADD COLUMN operation VARCHAR(255);
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='transactions' AND column_name='service'
                ) THEN
                    ALTER TABLE transactions ADD COLUMN service VARCHAR(255);
                END IF;
            END$$;
        """))
        
        # Переименование колонки account_id в balance_id в таблице balances
        conn.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='balances' AND column_name='account_id'
                ) THEN
                    ALTER TABLE balances RENAME COLUMN account_id TO balance_id;
                END IF;
            END$$;
        """))