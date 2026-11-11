-- Each query below is exported to results/<name>.csv by run.py.

-- name: data_quality
SELECT
    COUNT(*)                                                    AS rows_total,
    COUNT(*) - COUNT(DISTINCT id)                               AS duplicate_ids,
    SUM(education NOT IN (1, 2, 3))                             AS education_other_or_unknown,
    SUM(marriage = 0)                                           AS marriage_unknown,
    SUM(bill_amt1 < 0)                                          AS negative_latest_bill,
    SUM(limit_bal <= 0)                                         AS non_positive_limit
FROM raw_clients;

-- name: overall
SELECT
    COUNT(*)                                                    AS clients,
    SUM(default_next_month)                                     AS defaults,
    ROUND(AVG(default_next_month), 4)                           AS default_rate,
    ROUND(SUM(limit_bal) / 1e6, 1)                              AS total_limits_ntd_m,
    ROUND(SUM(CASE WHEN default_next_month = 1 THEN MAX(balance_latest, 0) END) / 1e6, 1)
                                                                AS balance_of_defaulters_ntd_m
FROM clients;

-- name: by_status
SELECT status_band, COUNT(*) AS clients, SUM(default_next_month) AS defaults,
       ROUND(AVG(default_next_month), 4) AS default_rate,
       ROUND(1.0 * COUNT(*) / (SELECT COUNT(*) FROM clients), 4) AS share_of_clients
FROM clients GROUP BY status_band ORDER BY status_band;

-- name: by_months_late
SELECT months_late_6m, COUNT(*) AS clients, ROUND(AVG(default_next_month), 4) AS default_rate
FROM clients GROUP BY months_late_6m ORDER BY months_late_6m;

-- name: by_utilisation
SELECT utilisation_band, COUNT(*) AS clients, ROUND(AVG(default_next_month), 4) AS default_rate
FROM clients GROUP BY utilisation_band ORDER BY utilisation_band;

-- name: by_payment
SELECT payment_band, COUNT(*) AS clients, ROUND(AVG(default_next_month), 4) AS default_rate
FROM clients GROUP BY payment_band ORDER BY payment_band;

-- name: by_limit
SELECT limit_band, COUNT(*) AS clients, ROUND(AVG(default_next_month), 4) AS default_rate
FROM clients GROUP BY limit_band ORDER BY limit_band;

-- name: by_age
SELECT age_band, COUNT(*) AS clients, ROUND(AVG(default_next_month), 4) AS default_rate
FROM clients GROUP BY age_band ORDER BY age_band;

-- name: risk_matrix
SELECT status_band, utilisation_band, COUNT(*) AS clients,
       ROUND(AVG(default_next_month), 4) AS default_rate
FROM clients GROUP BY status_band, utilisation_band ORDER BY status_band, utilisation_band;

-- name: watch_list
-- How well does the simple rule separate risky accounts? precision = default rate inside the list,
-- recall = share of all defaults the list catches.
SELECT
    SUM(watch_list)                                                             AS flagged_clients,
    ROUND(AVG(watch_list), 4)                                                   AS share_flagged,
    ROUND(1.0 * SUM(watch_list * default_next_month) / SUM(watch_list), 4)      AS precision,
    ROUND(1.0 * SUM(watch_list * default_next_month) / SUM(default_next_month), 4) AS recall,
    ROUND(1.0 * SUM((1 - watch_list) * default_next_month) / SUM(1 - watch_list), 4) AS default_rate_not_flagged
FROM clients;
