import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from db_utils import init_site_db, insert_usage_rows, get_sites_from_db_folder, query_usage_for_day
from data_loader import normalize_df, from_excel_sheet

st.set_page_config(page_title="日本トムソン様 使用量 可視化", layout="wide")

st.title("日本トムソン様：地区別 30分毎使用量データベース & 可視化")
tabs = st.tabs(["DB作成/更新", "可視化"])

with tabs[0]:
    st.subheader("① Excelから初期化（任意）")
    st.caption("各地区シートに『日付』『時刻』『使用量』列がある場合、自動で取り込みます。")
    up = st.file_uploader("Excelファイル（.xlsx）を選択", type=["xlsx"], key="excel")
    if up is not None:
        try:
            xls = pd.ExcelFile(up)
            site_sheets = [s for s in xls.sheet_names if s not in ["需要場所リスト"]]
            imported = []
            for sheet in site_sheets:
                try:
                    df_sheet = pd.read_excel(up, sheet_name=sheet)
                    ndf = from_excel_sheet(df_sheet)
                    init_site_db(sheet)
                    rows = [(sheet, r.ts, float(r.kwh)) for r in ndf.itertuples(index=False)]
                    insert_usage_rows(sheet, rows)
                    imported.append((sheet, len(rows)))
                except Exception as e:
                    st.warning(f"{sheet}: 取り込みスキップ（{e}）")
            if imported:
                st.success("Excelからの取り込み完了: " + ", ".join([f"{s}({n}件)" for s,n in imported]))
            else:
                st.info("有効な『日付・時刻・使用量』列が見つかりませんでした。CSVアップロードをご利用ください。")
        except Exception as e:
            st.error(f"Excelの読み込みに失敗しました: {e}")

    st.markdown("---")
    st.subheader("② CSVで登録/更新")
    st.caption("列名は `date,time,kwh` または `日付,時刻,使用量` に対応。")
    col1, col2 = st.columns([1,2])
    with col1:
        site = st.selectbox("地区を選択", ["極楽寺地区","笠神地区","武芸川地区","土岐地区"])
    with col2:
        csv_up = st.file_uploader("CSVファイル（30分データ）を選択", type=["csv"], key="csv")
    if csv_up and site:
        try:
            df = pd.read_csv(csv_up)
            ndf = normalize_df(df)
            init_site_db(site)
            rows = [(site, r.ts, float(r.kwh)) for r in ndf.itertuples(index=False)]
            insert_usage_rows(site, rows)
            st.success(f"{site} に {len(rows)} 行を登録/更新しました。")
            st.dataframe(ndf.head(10))
        except Exception as e:
            st.error(f"CSVの取り込みに失敗しました: {e}")

    st.markdown("---")
    st.subheader("現在のDB一覧")
    sites = get_sites_from_db_folder()
    st.write(", ".join(sites) if sites else "まだDBがありません。上の手順で作成してください。")

with tabs[1]:
    st.subheader("30分毎の使用量を日付指定で可視化")
    sites = get_sites_from_db_folder()
    if not sites:
        st.info("DBがありません。まず『DB作成/更新』でDBを作成してください。")
    else:
        col1, col2 = st.columns(2)
        with col1:
            site = st.selectbox("地区を選択", sites, key="viz_site")
        with col2:
            d = st.date_input("日付を選択", value=date.today(), key="viz_date")

        if st.button("表示"):
            rows = query_usage_for_day(site, d.strftime("%Y-%m-%d"))
            if not rows:
                st.warning("該当日のデータが見つかりません。")
            else:
                ts = [r[0] for r in rows]
                kwh = [r[1] for r in rows]
                try:
                    from matplotlib import font_manager, rcParams
                    fonts = [f.name for f in font_manager.fontManager.ttflist]
                    if any("Noto Sans CJK JP" in f for f in fonts):
                        rcParams["font.family"] = "Noto Sans CJK JP"
                except Exception:
                    pass

                fig, ax = plt.subplots(figsize=(10,4))
                ax.plot(ts, kwh)
                ax.set_title(f"{site} / {d.strftime('%Y-%m-%d')} 30分毎使用量")
                ax.set_xlabel("時刻")
                ax.set_ylabel("使用量 [kWh]")
                ax.grid(True, linewidth=0.5, alpha=0.6)
                plt.xticks(rotation=45)
                st.pyplot(fig, clear_figure=True)
                st.dataframe(pd.DataFrame({"timestamp": ts, "kwh": kwh})) 
