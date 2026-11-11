"""Builds the SQLite database, runs the SQL in sql/ and exports results. Python standard library only.

Run:  python run.py
"""
import csv
import re
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "credit_risk.db"
RAW_CSV = HERE / "data" / "credit_card_default.csv"


def load_raw(con):
    con.executescript((HERE / "sql" / "01_create_raw.sql").read_text())
    with RAW_CSV.open(newline="") as f:
        rows = list(csv.reader(f))
    header, data = rows[0], rows[1:]
    assert len(header) == 25 and header[0] == "ID", f"unexpected columns: {header}"
    con.executemany(f"INSERT INTO raw_clients VALUES ({','.join('?' * 25)})", data)
    con.commit()


def export(cur, path):
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([d[0] for d in cur.description])
        w.writerows(cur)


def main():
    DB.unlink(missing_ok=True)
    con = sqlite3.connect(DB)
    load_raw(con)
    con.executescript((HERE / "sql" / "02_clean.sql").read_text())

    # Sanity checks against the published dataset (Yeh & Lien, 2009): 30,000 clients, 6,636 defaults.
    n, d = con.execute("SELECT COUNT(*), SUM(default_next_month) FROM clients").fetchone()
    assert (n, d) == (30000, 6636), (n, d)
    # Bands must cover every client exactly once, and the watch list must equal the two "late" status bands.
    for band in ("status_band", "utilisation_band", "limit_band", "age_band", "payment_band"):
        assert con.execute(f"SELECT SUM(c) FROM (SELECT COUNT(*) c FROM clients GROUP BY {band})").fetchone()[0] == n
    late = con.execute("SELECT COUNT(*) FROM clients WHERE status_band LIKE '3%' OR status_band LIKE '4%'").fetchone()[0]
    assert late == con.execute("SELECT SUM(watch_list) FROM clients").fetchone()[0]

    # Run every named query in 03_analysis.sql and save it as results/<name>.csv
    text = (HERE / "sql" / "03_analysis.sql").read_text()
    for name, sql in re.findall(r"-- name: (\w+)\n(.*?;)", text, re.S):
        cur = con.execute(sql)
        export(cur, HERE / "results" / f"{name}.csv")
        print(f"\n== {name}")
        print(open(HERE / "results" / f"{name}.csv").read().strip())

    export(con.execute("SELECT * FROM clients"), HERE / "powerbi" / "clients_clean.csv")
    con.close()
    print("\nExported powerbi/clients_clean.csv for Power BI.")


if __name__ == "__main__":
    main()
