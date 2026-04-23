import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("📊 選曲結果表示画面")


# --- Logout Button ---
def logout():
    st.session_state["password_correct"] = False
    if "role" in st.session_state:
        del st.session_state["role"]
    if "username_logged_in" in st.session_state:
        del st.session_state["username_logged_in"]
    st.rerun()


st.button("ログアウト", on_click=logout)

# --- Google Sheets Connection ---
conn = st.connection("gsheets", type=GSheetsConnection)


# --- Load Data ---
@st.cache_data(ttl="1m")
def load_data():
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    # 一覧（内容）
    df_info = conn.read(spreadsheet=sheet_url, worksheet="一覧")
    # 集計（投票データ）
    try:
        df_votes = conn.read(spreadsheet=sheet_url, worksheet="集計")
    except Exception:
        df_votes = pd.DataFrame()
    return df_info, df_votes


df_info, df_votes = load_data()

if df_votes.empty:
    st.info("現在、投票データはありません。")
else:
    # --- Aggregate Points ---
    # IDごとにポイントを合計
    summary = df_votes.groupby("ID")["Point"].sum().reset_index()

    # 内容とマージ
    if "ID" not in df_info.columns:
        df_info["ID"] = df_info.index.astype(str)

    result_df = summary.merge(df_info, on="ID", how="left")
    result_df = result_df.sort_values(by="Point", ascending=False)

    st.subheader("🏆 投票ランキング")
    st.dataframe(
        result_df[["Point", "メイン曲", "サブ曲1", "サブ曲2", "サブ曲3"]],
        width="stretch",
        hide_index=True,
    )

    # --- Detail Views ---
    st.divider()
    st.subheader("詳細な結果")
    for idx, row in result_df.iterrows():
        with st.expander(f"【{row['Point']}pt】{row.get('メイン曲', '不明')}"):
            st.write(f"**合計分数:** {row.get('合計分数', '-')} 分")
            st.write(f"**楽器構成:** {row.get('楽器構成', '-')}")
            st.write(f"**自由記入欄:** {row.get('自由記入欄', '-')}")

            # Show comments for this combination
            combination_comments = df_votes[df_votes["ID"] == row["ID"]][
                ["投票者", "Type", "コメント"]
            ]
            if not combination_comments.empty:
                st.write("**投票者からのコメント:**")
                st.table(combination_comments.dropna(subset=["コメント"]))
