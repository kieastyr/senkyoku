import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="選曲システム", layout="wide")

# --- Load Data ---
@st.cache_data
def load_data():
    main_df = pd.read_csv("datasource/main_list.csv")
    sub_df = pd.read_csv("datasource/sub_list.csv")
    return main_df, sub_df

main_df, sub_df = load_data()

# --- Helper Functions ---
def parse_instrument(val):
    """
    Extracts and sums player counts from strings like '3(1)', '2/1/1', '3(1)/1'.
    - Ignores content inside parentheses.
    - Sums values separated by slashes.
    """
    if pd.isna(val) or val == "-" or str(val).strip() == "":
        return 0
    
    # 1. Remove content inside parentheses (e.g., '3(1)/1' -> '3/1')
    s = re.sub(r'\(.*?\)', '', str(val))
    
    # 2. Find all digit sequences and sum them (e.g., '3/1' -> [3, 1] -> 4)
    numbers = re.findall(r'\d+', s)
    return sum(int(n) for n in numbers)

# Instrument columns to validate
INSTRUMENT_COLS = [
    "フルート", "オーボエ", "クラリネット", "ファゴット", 
    "ホルン", "トランペット", "トロンボーン", "チューバ"
]

# --- UI ---
st.title("🎼 選曲・提出システム")

st.sidebar.header("選曲")

# Main List Selection (Single Selection)
st.sidebar.subheader("メイン曲 (main_list)")

def format_main(i):
    if i is None:
        return "選択してください"
    row = main_df.iloc[i]
    return f"{row['作曲者']} / {row['曲名']} ({row['分数']}分)"

selected_main_idx = st.sidebar.selectbox(
    "メイン曲を1曲選択してください",
    options=[None] + list(main_df.index),
    format_func=format_main,
    key="main_select"
)

total_main_duration = main_df.iloc[selected_main_idx]["分数"] if selected_main_idx is not None else 0

# Sub List Selection
st.sidebar.subheader("サブ曲 (sub_list)")

def format_sub(i):
    if i is None:
        return "選択しない"
    row = sub_df.iloc[i]
    return f"{row['作曲者']} / {row['曲名']} ({row['分数']}分)"

def get_sub_options(current_duration, exclude_indices):
    remaining = 100 - current_duration
    # 分数が残り時間以下、かつ既に選択されていない曲をフィルタリング
    mask = (sub_df["分数"] <= remaining) & (~sub_df.index.isin(exclude_indices))
    available = sub_df[mask]
    return [None] + list(available.index)

# サブ曲 1
opts1 = get_sub_options(total_main_duration, [])
sub1_idx = st.sidebar.selectbox("サブ曲 1", options=opts1, format_func=format_sub, key="sub1")
sub1_dur = sub_df.iloc[sub1_idx]["分数"] if sub1_idx is not None else 0

# サブ曲 2
exclude2 = [i for i in [sub1_idx] if i is not None]
opts2 = get_sub_options(total_main_duration + sub1_dur, exclude2)
sub2_idx = st.sidebar.selectbox("サブ曲 2", options=opts2, format_func=format_sub, key="sub2")
sub2_dur = sub_df.iloc[sub2_idx]["分数"] if sub2_idx is not None else 0

# サブ曲 3
exclude3 = [i for i in [sub1_idx, sub2_idx] if i is not None]
opts3 = get_sub_options(total_main_duration + sub1_dur + sub2_dur, exclude3)
sub3_idx = st.sidebar.selectbox("サブ曲 3", options=opts3, format_func=format_sub, key="sub3")

# Combine Selections
selected_main_rows = main_df.iloc[[selected_main_idx]] if selected_main_idx is not None else pd.DataFrame()
selected_sub_indices = [i for i in [sub1_idx, sub2_idx, sub3_idx] if i is not None]
selected_sub_rows = sub_df.iloc[selected_sub_indices]
all_selected = pd.concat([selected_main_rows, selected_sub_rows])

# --- Dashboard ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("選択された曲の一覧")
    if not all_selected.empty:
        # Show table including comments
        display_cols = ["作曲者", "曲名", "分数", "提出者からのコメント"] + INSTRUMENT_COLS
        st.dataframe(all_selected[display_cols], use_container_width=True)
        
        # Detailed Comments View
        st.write("**曲ごとのコメント詳細:**")
        for _, row in all_selected.iterrows():
            comment = row.get("提出者からのコメント")
            if pd.notna(comment) and str(comment).strip() != "":
                with st.expander(f"💬 {row['作曲者']} / {row['曲名']}"):
                    st.write(comment)
    else:
        st.info("左側のサイドバーから曲を選択してください。")

with col2:
    st.subheader("集計とバリデーション")
    
    # Total Duration
    total_duration = all_selected["分数"].sum() if not all_selected.empty else 0
    
    # Instrument Aggregation
    instrument_sums = {}
    for col in INSTRUMENT_COLS:
        if not all_selected.empty:
            instrument_sums[col] = all_selected[col].apply(parse_instrument).sum()
        else:
            instrument_sums[col] = 0

    # Validation Logic
    is_duration_ok = 0 < total_duration <= 100
    is_instruments_ok = all(v > 0 for v in instrument_sums.values()) if not all_selected.empty else False
    
    # Display Stats
    st.metric("合計分数", f"{total_duration} 分")
    if total_duration > 100:
        st.error("❌ 合計分数が100分を超えています。")
    elif total_duration > 0:
        st.success("✅ 合計分数は範囲内です（100分以内）。")

    st.write("**楽器構成（各パート1名以上必要）**")
    for part, count in instrument_sums.items():
        if count > 0:
            st.write(f"✅ {part}: {count}")
        else:
            st.write(f"❌ {part}: {count}")

    if not all_selected.empty and not is_instruments_ok:
        st.error("❌ すべての楽器パートに少なくとも1名以上の奏者が必要です。")

from streamlit_gsheets import GSheetsConnection

# --- Google Sheets Connection ---
# ※ .streamlit/secrets.toml に接続設定が必要です
conn = st.connection("gsheets", type=GSheetsConnection)

# --- Submission Logic ---
def submit_to_gsheets(user_name, user_comment, selected_songs_df, total_dur):
    """
    Submits the selection data to Google Sheets.
    """
    # Create a summary row with "Composer/Song Name" format
    song_list = selected_songs_df.apply(lambda r: f"{r['作曲者']}/{r['曲名']}", axis=1).tolist()
    song_titles = " 、 ".join(song_list)
    
    instrument_details = ""
    for col in INSTRUMENT_COLS:
        count = selected_songs_df[col].apply(parse_instrument).sum()
        instrument_details += f"{col}:{count}, "
    
    new_row = pd.DataFrame([{
        "タイムスタンプ": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "提出者名": user_name,
        "選択曲": song_titles,
        "合計分数": total_dur,
        "楽器構成": instrument_details.strip(", "),
        "自由記入欄": user_comment
    }])

    try:
        # Read existing data
        try:
            existing_data = conn.read(ttl=0)
            if existing_data.empty:
                 updated_df = new_row
            else:
                 updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        except Exception:
            updated_df = new_row
            
        conn.update(data=updated_df)
        return True
    except Exception:
        return False

# --- Submission Form ---
st.divider()
st.subheader("提出フォーム")

with st.form("submission_form"):
    user_name = st.text_input("提出者名")
    user_comment = st.text_area("自由記入欄（選曲理由など）")
    
    can_submit = is_duration_ok and is_instruments_ok
    
    submit_button = st.form_submit_button("提出する", disabled=not can_submit)
    
    if submit_button:
        success = submit_to_gsheets(user_name, user_comment, all_selected, total_duration)
        if success:
            st.success(f"提出を受け付けました！スプレッドシートに保存しました。ありがとうございます、{user_name}さん。")
            st.balloons()

if not can_submit and not all_selected.empty:
    st.warning("提出するには、すべてのバリデーション条件を満たす必要があります。")
