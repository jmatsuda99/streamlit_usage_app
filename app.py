import streamlit as st, pandas as pd, sys, traceback
from datetime import date

st.set_page_config(page_title="日本トムソン様 使用量 可視化", layout="wide")

# --- 診断パネル（サイドバー）---
with st.sidebar:
    st.header("Diagnostics")
    try:
        import pkg_resources
        pkgs = sorted([(d.project_name, d.version) for d in pkg_resources.working_set])
        st.caption("Top packages (excerpt)")
        st.write([p for p in pkgs if p[0] in ["streamlit","pandas","SQLAlchemy","openpyxl","matplotlib"]])
    except Exception as e:
        st.write("pkg list error:", e)
    st.write("Python:", sys.version.split()[0])

# --- 安全ガード用のラッパー ---
def safe_run(fn):
    try:
        fn()
    except Exception as e:
        st.error("例外が発生しました。詳細は以下：")
        st.exception(e)
        st.code("".join(traceback.format_exc()))

def main():
    from db_utils import init_site_db, insert_usage_rows, get_sites_from_db_folder, query_usage_for_day
    from data_loader import normalize_df, from_excel_sheet

    st.title("日本トムソン様：地区別 30分毎使用量DB & 可視化")
    tabs = st.tabs(["DB作成/更新","可視化"])

    # --- DB作成/更新 ---
    def tab_db():
        with tabs[0]:
            st.subheader("① Excelから初期化")
            up = st.file_uploader("Excelファイル(.xlsx)", type=["xlsx"], key="excel")
            if up:
                xls = pd.ExcelFile(up)
                for sheet in [s for s in xls.sheet_names if s!="需要場所リスト"]:
                    try:
                        df = pd.read_excel(up, sheet_name=sheet)
                        ndf = from_excel_sheet(df)
                        init_site_db(sheet)
                        rows=[(sheet,r.ts,float(r.kwh)) for r in ndf.itertuples(index=False)]
                        insert_usage_rows(sheet, rows)
                        st.success(f"{sheet}: {len(rows)}件登録")
                    except Exception as e:
                        st.warning(f"{sheet}: スキップ({e})")

            st.subheader("② CSVで登録/更新")
            site = st.selectbox("地区",["極楽寺地区","笠神地区","武芸川地区","土岐地区"])
            csv_up = st.file_uploader("CSVファイル", type=["csv"], key="csv")
            if csv_up:
                df=pd.read_csv(csv_up)
                ndf=normalize_df(df)
                init_site_db(site)
                rows=[(site,r.ts,float(r.kwh)) for r in ndf.itertuples(index=False)]
                insert_usage_rows(site, rows)
                st.success(f"{site}: {len(rows)}件登録")
                st.dataframe(ndf.head())

            st.subheader("DB一覧")
            st.write(get_sites_from_db_folder())

    # --- 可視化 ---
    def tab_viz():
        with tabs[1]:
            st.subheader("30分毎の使用量グラフ")
            from db_utils import get_sites_from_db_folder, query_usage_for_day
            sites=get_sites_from_db_folder()
            if sites:
                site=st.selectbox("地区",sites,key="viz_site")
                d=st.date_input("日付",value=date.today(),key="viz_date")
                if st.button("表示"):
                    rows=query_usage_for_day(site,d.strftime("%Y-%m-%d"))
                    if rows:
                        ts=[r[0] for r in rows]; kwh=[r[1] for r in rows]
                        dfp=pd.DataFrame({"timestamp":ts,"kwh":kwh}).set_index("timestamp")
                        # optional matplotlib
                        try:
                            import matplotlib.pyplot as plt
                            try:
                                from matplotlib import font_manager, rcParams
                                fonts = [f.name for f in font_manager.fontManager.ttflist]
                                if any("Noto Sans CJK JP" in f for f in fonts):
                                    rcParams["font.family"] = "Noto Sans CJK JP"
                            except Exception:
                                pass
                            fig,ax=plt.subplots(figsize=(10,4))
                            ax.plot(dfp.index, dfp["kwh"])
                            ax.set_title(f"{site}/{d} 30分毎使用量")
                            ax.set_xlabel("時刻"); ax.set_ylabel("使用量[kWh]")
                            ax.grid(True,alpha=0.6)
                            st.pyplot(fig, clear_figure=True)
                        except Exception:
                            st.line_chart(dfp, height=320)
                        st.dataframe(dfp.reset_index())
                    else:
                        st.warning("データなし")
            else:
                st.info("DBが未作成")

    safe_run(tab_db)
    safe_run(tab_viz)

if __name__ == "__main__":
    main()
