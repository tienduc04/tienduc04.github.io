-- Cleaned, analysis-ready table with derived risk features and bands.
-- Dialect: SQLite. On SQL Server, replace the multi-argument MAX(...) with GREATEST(...) (SQL Server 2022+).
DROP TABLE IF EXISTS clients;
CREATE TABLE clients AS
WITH base AS (
    SELECT
        id,
        limit_bal,
        age,
        CASE education WHEN 1 THEN 'Graduate school' WHEN 2 THEN 'University'
                       WHEN 3 THEN 'High school' ELSE 'Other / unknown' END          AS education,
        pay_1                                                                     AS status_latest,
        MAX(pay_1, pay_2, pay_3, pay_4, pay_5, pay_6, 0)                          AS max_delay_6m,
        (pay_1 >= 1) + (pay_2 >= 1) + (pay_3 >= 1)
          + (pay_4 >= 1) + (pay_5 >= 1) + (pay_6 >= 1)                            AS months_late_6m,
        bill_amt1                                                                 AS balance_latest,
        MAX(bill_amt1, 0) / limit_bal                                             AS utilisation,
        -- payment made in September against the August bill; NULL when there was nothing to pay
        CASE WHEN bill_amt2 > 0 THEN pay_amt1 / bill_amt2 END                     AS payment_ratio,
        default_next_month
    FROM raw_clients
)
SELECT
    *,
    CASE WHEN status_latest <= -1 THEN '1 Paid in full / no use'
         WHEN status_latest = 0   THEN '2 Revolving (minimum paid)'
         WHEN status_latest = 1   THEN '3 1 month late'
         ELSE                          '4 2+ months late' END                       AS status_band,
    CASE WHEN utilisation < 0.3 THEN '1 <30%'
         WHEN utilisation < 0.7 THEN '2 30-70%'
         WHEN utilisation < 1.0 THEN '3 70-100%'
         ELSE                        '4 100%+' END                                  AS utilisation_band,
    CASE WHEN limit_bal < 50000  THEN '1 <50k'
         WHEN limit_bal < 100000 THEN '2 50-100k'
         WHEN limit_bal < 200000 THEN '3 100-200k'
         WHEN limit_bal < 500000 THEN '4 200-500k'
         ELSE                         '5 500k+' END                                 AS limit_band,
    CASE WHEN age < 30 THEN '1 21-29' WHEN age < 40 THEN '2 30-39'
         WHEN age < 50 THEN '3 40-49' ELSE '4 50+' END                              AS age_band,
    CASE WHEN payment_ratio IS NULL THEN '0 No bill'
         WHEN payment_ratio < 0.1   THEN '1 <10% of bill'
         WHEN payment_ratio < 0.5   THEN '2 10-50%'
         WHEN payment_ratio < 1.0   THEN '3 50-100%'
         ELSE                            '4 Paid in full' END                       AS payment_band,
    -- early-warning watch list: any late payment this month (behaviour only, no demographic inputs)
    CASE WHEN status_latest >= 1 THEN 1 ELSE 0 END                                  AS watch_list
FROM base;
