-- Raw table: one row per credit card client, exactly as in the UCI file.
-- Source columns PAY_0..PAY_6 are renamed pay_1..pay_6 (1 = September 2005, 6 = April 2005).
DROP TABLE IF EXISTS raw_clients;
CREATE TABLE raw_clients (
    id                 INTEGER PRIMARY KEY,
    limit_bal          REAL,     -- credit limit, NT$
    sex                INTEGER,  -- 1 male, 2 female
    education          INTEGER,  -- 1 graduate school, 2 university, 3 high school, 4 other, 0/5/6 unknown
    marriage           INTEGER,  -- 1 married, 2 single, 3 other, 0 unknown
    age                INTEGER,
    pay_1 INTEGER, pay_2 INTEGER, pay_3 INTEGER, pay_4 INTEGER, pay_5 INTEGER, pay_6 INTEGER,
    -- repayment status: -2 no consumption, -1 paid in full, 0 revolving (minimum paid), 1..9 months late
    bill_amt1 REAL, bill_amt2 REAL, bill_amt3 REAL, bill_amt4 REAL, bill_amt5 REAL, bill_amt6 REAL,
    pay_amt1  REAL, pay_amt2  REAL, pay_amt3  REAL, pay_amt4  REAL, pay_amt5  REAL, pay_amt6  REAL,
    default_next_month INTEGER   -- 1 = defaulted in October 2005
);
