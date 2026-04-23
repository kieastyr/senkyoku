import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🗳️ 選曲投票画面")


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
@st.cache_data(ttl="5m")
def load_data():
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    # 候補の一覧
    df_combinations = conn.read(spreadsheet=sheet_url, worksheet="一覧")
    # 過去の投票データ（集計シート）
    try:
        df_votes = conn.read(spreadsheet=sheet_url, worksheet="集計")
    except Exception:
        df_votes = pd.DataFrame()
    return df_combinations, df_votes


try:
    df_combinations, df_votes = load_data()
except Exception as e:
    st.error(f"データの読み込みに失敗しました: {e}")
    st.stop()

if df_combinations.empty:
    st.warning("表示できる組み合わせがありません。")
    st.stop()

# Ensure numeric columns are int and handle IDs
if "ID" not in df_combinations.columns:
    df_combinations["ID"] = df_combinations.index.astype(int)
else:
    df_combinations["ID"] = (
        pd.to_numeric(df_combinations["ID"], errors="coerce").fillna(0).astype(int)
    )

for col in ["合計分数", "ハープ最大数"]:
    if col in df_combinations.columns:
        df_combinations[col] = (
            pd.to_numeric(df_combinations[col], errors="coerce").fillna(0).astype(int)
        )

# --- Detail View (Select to View) ---
st.subheader("📜 全候補一覧")
st.dataframe(df_combinations, width="stretch", hide_index=True)
st.divider()

st.subheader("🧐 組み合わせの詳細をチェック")
st.info("以下のリストからIDを選択して、詳しい曲構成や楽器編成を確認できます。")


# ID options with formatted labels
def format_combination_label(option_id):
    row = df_combinations[df_combinations["ID"] == option_id].iloc[0]
    label = f"ID: {option_id} | {row.get('メイン曲', '不明')}"
    for sub in ["サブ曲1", "サブ曲2", "サブ曲3"]:
        val = row.get(sub)
        if pd.notna(val) and str(val).strip() and str(val) != "None":
            label += f" | {val}"
    return label


selected_id = st.selectbox(
    "詳細を表示する組み合わせを選択",
    options=df_combinations["ID"].tolist(),
    format_func=format_combination_label,
)

# Show details in a card-like view
if selected_id is not None:
    detail_row = df_combinations[df_combinations["ID"] == selected_id].iloc[0]

    col1, col2 = st.columns([1, 1])
    with col1:
        st.write(f"### ID: {int(detail_row['ID'])}")
        st.write(f"**合計分数:** {int(detail_row.get('合計分数', 0))} 分")
        st.write(f"**ハープ最大数:** {int(detail_row.get('ハープ最大数', 0))}")

    with col2:
        st.write("**楽器構成:**")
        st.write(detail_row.get("楽器構成", "データなし"))
        st.write("**打楽器:**")
        st.write(detail_row.get("打楽器", "なし"))

    st.write("---")
    st.write("**曲目構成:**")
    st.write(f"1. **メイン曲:** {detail_row.get('メイン曲', '-')}")

    sub_count = 2
    for sub in ["サブ曲1", "サブ曲2", "サブ曲3"]:
        val = detail_row.get(sub)
        if pd.notna(val) and str(val).strip() and str(val) != "None":
            st.write(f"{sub_count}. **{sub}:** {val}")
            sub_count += 1

    st.write("**提出者からのコメント:**")
    st.info(detail_row.get("自由記入欄", "（コメントなし）"))

st.divider()

# --- Voting Form ---
st.subheader("🗳️ 投票フォーム")
st.write("Positiveを3つ、Negativeを1つ選択してください。")

with st.form("voting_form"):
    # user_name input removed as per request

    options = df_combinations["ID"].tolist()

    col1, col2 = st.columns(2)
    with col1:
        st.write("**👍 (各+1pt)**")
        pos1 = st.selectbox(
            "👍 1", options, format_func=format_combination_label, key="pos1"
        )
        pos2 = st.selectbox(
            "👍 2", options, format_func=format_combination_label, key="pos2"
        )
        pos3 = st.selectbox(
            "👍 3", options, format_func=format_combination_label, key="pos3"
        )

    with col2:
        st.write("**👎 (-1pt)**")
        neg1 = st.selectbox(
            "👎", options, format_func=format_combination_label, key="neg1"
        )

    comment = st.text_area("選考の理由やコメント（任意）")

    submit_button = st.form_submit_button("投票を送信", width="stretch")

    if submit_button:
        if len({pos1, pos2, pos3, neg1}) < 4:
            st.error("❌ 全て異なる組み合わせを選択してください。")
        else:
            # Prepare new votes
            timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            # Set voter name to "Anonymous" or empty since it's not required
            voter_name = "Anonymous"

            new_rows = [
                {
                    "タイムスタンプ": timestamp,
                    "投票者": voter_name,
                    "ID": pos1,
                    "Point": 1,
                    "Type": "👍",
                    "コメント": comment,
                },
                {
                    "タイムスタンプ": timestamp,
                    "投票者": voter_name,
                    "ID": pos2,
                    "Point": 1,
                    "Type": "👍",
                    "コメント": comment,
                },
                {
                    "タイムスタンプ": timestamp,
                    "投票者": voter_name,
                    "ID": pos3,
                    "Point": 1,
                    "Type": "👍",
                    "コメント": comment,
                },
                {
                    "タイムスタンプ": timestamp,
                    "投票者": voter_name,
                    "ID": neg1,
                    "Point": -1,
                    "Type": "👎",
                    "コメント": comment,
                },
            ]
            new_votes_df = pd.DataFrame(new_rows)

            try:
                # Append to '集計' worksheet
                updated_votes = pd.concat([df_votes, new_votes_df], ignore_index=True)
                conn.update(worksheet="集計", data=updated_votes)

                # Standard output logging
                print(
                    f"[{timestamp}] Vote received: Pos({pos1}, {pos2}, {pos3}), Neg({neg1})"
                )

                st.success("投票が完了しました！")
                st.balloons()
                st.cache_data.clear()  # Clear cache
            except Exception as e:
                st.error(f"投票の保存に失敗しました: {e}")
