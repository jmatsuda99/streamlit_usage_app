import pandas as pd

JP_COLUMNS = {"date":"date","time":"time","kwh":"kwh"}
JP_COLUMNS_JA = {"日付":"date","時刻":"time","使用量":"kwh"}

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    cols = {str(c).strip():c for c in df.columns}
    if set(["date","time","kwh"]).issubset(cols):
        rename_map = JP_COLUMNS
    elif set(["日付","時刻","使用量"]).issubset(cols):
        rename_map = JP_COLUMNS_JA
    else:
        rename_map = {}
        for c in df.columns:
            cs = str(c).strip()
            if cs in ["date","DATE","日付"]: rename_map[c] = "date"
            elif cs in ["time","TIME","時刻"]: rename_map[c] = "time"
            elif "kwh" in cs.lower() or cs in ["使用量","電力量"]: rename_map[c] = "kwh"
    ndf = df.rename(columns=rename_map)
    for col in ["date","time","kwh"]:
        if col not in ndf.columns:
            raise ValueError("必要な列（date/time/kwh または 日付/時刻/使用量）が見つかりません") 
    ndf = ndf[["date","time","kwh"]].copy()
    ndf["date"] = pd.to_datetime(ndf["date"]).dt.date.astype(str)
    ndf["time"] = ndf["time"].astype(str).str.slice(0,5)
    ndf["kwh"] = pd.to_numeric(ndf["kwh"], errors="coerce")
    ndf = ndf.dropna(subset=["kwh"])
    ndf["ts"] = pd.to_datetime(ndf["date"]+" "+ndf["time"], errors="coerce")
    ndf = ndf.dropna(subset=["ts"])
    ndf["ts"] = ndf["ts"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return ndf[["ts","kwh"]]

def from_excel_sheet(df_sheet: pd.DataFrame)->pd.DataFrame:
    return normalize_df(df_sheet)
