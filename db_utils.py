import os, sqlite3
from contextlib import closing

def db_path_for_site(site: str) -> str:
    os.makedirs("db", exist_ok=True)
    safe = site.replace("/", "_")
    return os.path.join("db", f"{safe}.db")

def init_site_db(site: str):
    path = db_path_for_site(site)
    with closing(sqlite3.connect(path)) as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                site TEXT NOT NULL,
                ts   TEXT NOT NULL,
                kwh  REAL NOT NULL,
                PRIMARY KEY (site, ts)
            )""")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage(ts)")
        con.commit()
    return path

def insert_usage_rows(site: str, rows):
    path = db_path_for_site(site)
    with closing(sqlite3.connect(path)) as con:
        cur = con.cursor()
        cur.executemany("INSERT OR REPLACE INTO usage (site, ts, kwh) VALUES (?, ?, ?)", rows)
        con.commit()

def get_sites_from_db_folder():
    if not os.path.isdir("db"):
        return []
    return sorted([os.path.splitext(f)[0] for f in os.listdir("db") if f.endswith(".db")])

def query_usage_for_day(site: str, date_str: str):
    path = db_path_for_site(site)
    if not os.path.exists(path):
        return []
    start, end = f"{date_str}T00:00:00", f"{date_str}T23:59:59"
    with closing(sqlite3.connect(path)) as con:
        cur = con.cursor()
        cur.execute(
            "SELECT ts, kwh FROM usage WHERE site=? AND ts BETWEEN ? AND ? ORDER BY ts ASC",
            (site, start, end))
        return cur.fetchall()
