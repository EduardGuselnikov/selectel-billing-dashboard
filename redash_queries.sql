-- =====================================================
-- SQL-запросы для Redash дашборда Selectel Billing
-- Только используемые в дашбордах запросы
-- =====================================================

-- 1. Отчеты по проектам
-- Запрос: Расходы по проектам за текущий год
SELECT 
    year,
    month,
    project_name,
    balance_type,
    value/100 as sum,
    fetched_at
FROM project_reports 
WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
ORDER BY year DESC, month DESC, value DESC;

-- 2. Прогнозы расходов
-- Запрос: Прогнозы в днях до исчерпания баланса
SELECT
    balance_type,
    predicted_amount/24 as days,
    fetched_at
FROM predictions 
WHERE fetched_at = (SELECT MAX(fetched_at) FROM predictions)
ORDER BY predicted_amount DESC;

-- 3. Транзакции
-- Запрос: Расходы по услугам по месяцам
SELECT
    DATE_TRUNC('month', created)::date AS month,
    service,
    SUM(ABS(price))/100 AS total_spent
FROM transactions
WHERE price < 0
GROUP BY month, service
ORDER BY month, service;

-- 4. Баланс
-- Запрос: Текущий общий баланс (последние данные)
WITH t AS (
  SELECT
    amount,
    date_trunc('minute', fetched_at) AS fetched_min
  FROM balances
),
max_minute AS (
  SELECT MAX(fetched_min) AS fetched_min
  FROM (
    SELECT fetched_min
    FROM t
    GROUP BY fetched_min
    HAVING COUNT(*) > 1
  ) dups
)
SELECT 
    t.fetched_min,
    SUM(t.amount)/100 AS total_amount
FROM t
JOIN max_minute m ON t.fetched_min = m.fetched_min
GROUP BY t.fetched_min;