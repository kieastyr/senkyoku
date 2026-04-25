import re

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# --- 応募終了画面・ログアウト ---
st.title("🎼 選曲組み合わせ提出ツール")


def logout():
    st.session_state["password_correct"] = False
    if "role" in st.session_state:
        del st.session_state["role"]
    if "username_logged_in" in st.session_state:
        del st.session_state["username_logged_in"]
    st.rerun()


st.button("ログアウト", on_click=logout)
st.warning(
    "現在、組み合わせ提出は受け付けていません。不明点は運営者までお問い合わせください。"
)
st.stop()  # ここで停止させることで、これ以降の元のコードは実行されません

# from streamlit_gsheets import GSheetsConnection  # This will be moved or kept below


# --- Google Sheets Connection ---
# ※ .streamlit/secrets.toml に接続設定が必要です
conn = st.connection("gsheets", type=GSheetsConnection)


# --- Load Data ---
@st.cache_data
def load_data():
    # Load from separate spreadsheets
    sheet_url = st.secrets["connections"]["gsheets"]["input_list"]
    main_df = conn.read(
        spreadsheet=sheet_url,
        worksheet="メイン曲",
        ttl="10m",  # Cache for 10 minutes
    )
    sub_df = conn.read(
        spreadsheet=sheet_url,
        worksheet="サブ曲",
        ttl="10m",
    )
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
    s = re.sub(r"\(.*?\)", "", str(val))

    # 2. Find all digit sequences and sum them (e.g., '3/1' -> [3, 1] -> 4)
    numbers = re.findall(r"\d+", s)
    return sum(int(n) for n in numbers)


def parse_percussion(val):
    """
    Extracts the required number of percussionists.
    If a range like '4~5' is provided, the first number (4) is used.
    """
    if pd.isna(val) or val == "-" or str(val).strip() == "":
        return 0
    s = str(val).split("~")[0]
    numbers = re.findall(r"\d+", s)
    return int(numbers[0]) if numbers else 0


# Instrument columns to validate
INSTRUMENT_COLS = [
    "フルート",
    "オーボエ",
    "クラリネット",
    "ファゴット",
    "ホルン",
    "トランペット",
    "トロンボーン",
    "チューバ",
]
instrument_min = {
    "フルート": 4,
    "オーボエ": 4,
    "クラリネット": 4,
    "ファゴット": 4,
    "ホルン": 8,
    "トランペット": 4,
    "トロンボーン": 3,
    "チューバ": 1,
}
instrument_max = {k: 20 for k in INSTRUMENT_COLS}


# --- Sidebar Logout ---
def logout():
    st.session_state["password_correct"] = False
    if "role" in st.session_state:
        del st.session_state["role"]
    if "username_logged_in" in st.session_state:
        del st.session_state["username_logged_in"]
    st.rerun()


st.sidebar.button("ログアウト", on_click=logout)

# --- UI ---
st.sidebar.header("選曲")

# Main List Selection (Single Selection)
st.sidebar.subheader("メイン曲")


def format_main(i):
    if i is None:
        return "選択してください"
    row = main_df.iloc[i]
    return f"{row['作曲者']} / {row['曲名']} ({int(row['分数'])}分)"


selected_main_idx = st.sidebar.selectbox(
    "メイン曲を1曲選択してください",
    options=[None] + list(main_df.index),
    format_func=format_main,
    key="main_select",
)

total_main_duration = (
    main_df.iloc[selected_main_idx]["分数"] if selected_main_idx is not None else 0
)

# Sub List Selection
st.sidebar.subheader("サブ曲")


def format_sub(i):
    if i is None:
        return "選択しない"
    row = sub_df.iloc[i]
    return f"{row['作曲者']} / {row['曲名']} ({int(row['分数'])}分)"


def get_sub_options(current_duration, exclude_indices, main_idx):
    remaining = 100 - current_duration
    # 分数が残り時間以下、かつ既に選択されていない曲をフィルタリング
    mask = (sub_df["分数"] <= remaining) & (~sub_df.index.isin(exclude_indices))

    if main_idx is not None:
        main_row = main_df.iloc[main_idx]
        # 作曲者と曲名が一致する曲をサブ曲の選択肢から除外
        mask &= ~(
            (sub_df["作曲者"] == main_row["作曲者"])
            & (sub_df["曲名"] == main_row["曲名"])
        )

    available = sub_df[mask]
    return [None] + list(available.index)


# サブ曲 1
opts1 = get_sub_options(total_main_duration, [], selected_main_idx)
sub1_idx = st.sidebar.selectbox(
    "サブ曲 1", options=opts1, format_func=format_sub, key="sub1"
)
sub1_dur = sub_df.iloc[sub1_idx]["分数"] if sub1_idx is not None else 0

# サブ曲 2
exclude2 = [i for i in [sub1_idx] if i is not None]
opts2 = get_sub_options(total_main_duration + sub1_dur, exclude2, selected_main_idx)
sub2_idx = st.sidebar.selectbox(
    "サブ曲 2", options=opts2, format_func=format_sub, key="sub2"
)
sub2_dur = sub_df.iloc[sub2_idx]["分数"] if sub2_idx is not None else 0

# サブ曲 3
exclude3 = [i for i in [sub1_idx, sub2_idx] if i is not None]
opts3 = get_sub_options(
    total_main_duration + sub1_dur + sub2_dur, exclude3, selected_main_idx
)
sub3_idx = st.sidebar.selectbox(
    "サブ曲 3", options=opts3, format_func=format_sub, key="sub3"
)

# Combine Selections
selected_main_rows = (
    main_df.iloc[[selected_main_idx]]
    if selected_main_idx is not None
    else pd.DataFrame()
)
selected_sub_indices = [i for i in [sub1_idx, sub2_idx, sub3_idx] if i is not None]
selected_sub_rows = sub_df.iloc[selected_sub_indices]
all_selected = pd.concat([selected_main_rows, selected_sub_rows])

# --- Dashboard ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("選択された曲の一覧")
    if not all_selected.empty:
        # Show table including comments
        display_cols = (
            [
                "作曲者",
                "曲名",
                "分数",
                "提出者からのコメント",
            ]
            + INSTRUMENT_COLS
            + ["打楽器", "打楽器必要人数", "その他", "備考"]
        )

        # Configure numeric columns to show as integers
        column_config = {
            col: st.column_config.NumberColumn(format="%d") for col in ["分数"]
        }

        st.dataframe(
            all_selected[display_cols],
            width="stretch",
            hide_index=True,
            column_config=column_config,
        )

        # Detailed Comments View
        st.write("**曲ごとのコメント詳細:**")
        for _, row in all_selected.iterrows():
            comment = row.get("提出者からのコメント")
            if pd.notna(comment) and str(comment).strip() != "":
                with st.expander(f"💬 {row['作曲者']} / {row['曲名']}"):
                    st.write(comment)
    else:
        st.info("左上の>>からサイドバーを開いて曲を選択してください。")

with col2:
    st.subheader("集計と条件判定")

    # Total Duration
    total_duration = int(all_selected["分数"].sum()) if not all_selected.empty else 0

    # Instrument Aggregation
    instrument_sums = {}
    for col in INSTRUMENT_COLS:
        if not all_selected.empty:
            instrument_sums[col] = int(all_selected[col].apply(parse_instrument).sum())
        else:
            instrument_sums[col] = 0

    # Validation Logic
    is_duration_ok = 0 < total_duration <= 100

    # Percussion Validation
    is_percussion_ok = True
    main_perc = 0
    if selected_main_idx is not None:
        main_perc = parse_percussion(
            main_df.iloc[selected_main_idx].get("打楽器必要人数", 0)
        )
        sub_percs = [
            parse_percussion(sub_df.iloc[i].get("打楽器必要人数", 0))
            for i in selected_sub_indices
        ]
        if main_perc <= 1:
            if not any(p >= 3 for p in sub_percs):
                is_percussion_ok = False

    is_instruments_ok = (
        all(
            (
                instrument_sums[i] >= instrument_min[i]
                and instrument_sums[i] <= instrument_max[i]
            )
            for i in INSTRUMENT_COLS
        )
        and is_percussion_ok
        if not all_selected.empty
        else False
    )

    # Display Stats
    st.metric("合計分数", f"{total_duration} 分")
    if total_duration > 100:
        st.error("❌ 合計分数が100分を超えています。")
    elif total_duration > 0:
        st.success("✅ 合計分数は範囲内です（100分以内）。")

    st.write("**楽器構成（各パート()内の人数を満たしているか）**")
    for part in INSTRUMENT_COLS:
        count = instrument_sums[part]
        min_num = instrument_min[part]
        max_num = instrument_max[part]
        if count >= min_num and count <= max_num:
            st.write(f"✅ {part}: {count} ({min_num}~{max_num})")
        else:
            st.write(f"❌ {part}: {count} ({min_num}~{max_num})")

    # Percussion special condition
    if selected_main_idx is not None:
        if is_percussion_ok:
            if main_perc <= 1:
                st.write(
                    f"✅ 打楽器: メイン{main_perc}名に対し、サブ曲で3名以上を必要とする曲を1曲以上確保しています"
                )
            else:
                st.write(
                    f"✅ 打楽器: メイン{main_perc}名のため、特別な制限はありません"
                )
        else:
            st.write(
                f"❌ 打楽器: メイン{main_perc}名の場合、サブ曲のいずれかに3名以上の曲が必要です"
            )

    if not all_selected.empty and not is_instruments_ok:
        st.error("❌ すべてのパートが条件を満たす必要があります。")


# --- Submission Logic ---
def submit_to_gsheets(
    user_name,
    user_comment,
    main_idx,
    s1_idx,
    s2_idx,
    s3_idx,
    selected_songs_df,
    total_dur,
):
    """
    Submits the selection data to Google Sheets.
    """

    def format_song(df, idx):
        if idx is None:
            return None
        row = df.iloc[idx]
        return f"{row['作曲者']}/{row['曲名']}"

    instrument_details = ""
    for col in INSTRUMENT_COLS:
        count = selected_songs_df[col].apply(parse_instrument).sum()
        instrument_details += f"{col}:{count}, "

    # Harp max
    harp_max = 0
    if "ハープ" in selected_songs_df.columns:
        harp_max = int(selected_songs_df["ハープ"].apply(parse_instrument).max())

    # Percussion union
    percussion_set = set()
    if "打楽器" in selected_songs_df.columns:
        for p_str in selected_songs_df["打楽器"].dropna():
            if str(p_str).strip() and p_str != "-":
                parts = [p.strip() for p in str(p_str).split(",")]
                percussion_set.update([p for p in parts if p])
    percussion_union = ", ".join(sorted(percussion_set))

    # Other concatenation
    other_concat = ""
    if "その他" in selected_songs_df.columns:
        others = selected_songs_df["その他"].dropna()
        other_concat = ", ".join(
            [str(o).strip() for o in others if str(o).strip() and o != "-"]
        )

    new_row = pd.DataFrame(
        [
            {
                "タイムスタンプ": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "提出者名": user_name,
                "メイン曲": format_song(main_df, main_idx),
                "サブ曲1": format_song(sub_df, s1_idx),
                "サブ曲2": format_song(sub_df, s2_idx),
                "サブ曲3": format_song(sub_df, s3_idx),
                "合計分数": total_dur,
                "楽器構成": instrument_details.strip(", "),
                "ハープ最大数": harp_max,
                "打楽器": percussion_union,
                "その他": other_concat,
                "自由記入欄": user_comment,
            }
        ]
    )

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
    user_name = st.text_input("提出者名（必須）")
    user_comment = st.text_area("自由記入欄（選曲理由など）")

    can_submit = is_duration_ok and is_instruments_ok

    submit_button = st.form_submit_button("提出する", disabled=not can_submit)

    if submit_button:
        if not user_name.strip():
            st.error("❌ 提出者名を入力してください。")
        else:
            success = submit_to_gsheets(
                user_name,
                user_comment,
                selected_main_idx,
                sub1_idx,
                sub2_idx,
                sub3_idx,
                all_selected,
                total_duration,
            )
            if success:
                st.success(
                    f"提出を受け付けました！スプレッドシートに保存しました。ありがとうございます、{user_name}さん。"
                )
                st.balloons()

if not can_submit and not all_selected.empty:
    st.warning("提出するには、すべての条件を満たす必要があります。")
    st.warning("提出するには、すべての条件を満たす必要があります。")
    st.warning("提出するには、すべての条件を満たす必要があります。")
    st.warning("提出するには、すべての条件を満たす必要があります。")
    st.warning("提出するには、すべての条件を満たす必要があります。")
