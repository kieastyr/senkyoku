import logging
import secrets

import streamlit as st

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --- Logout Button ---
def logout():
    st.session_state["password_correct"] = False
    if "role" in st.session_state:
        del st.session_state["role"]
    if "username_logged_in" in st.session_state:
        del st.session_state["username_logged_in"]
    if "line_user" in st.session_state:
        del st.session_state["line_user"]
    st.rerun()


# --- Main Page UI ---
st.title("📱 選曲投票 (LINE認証済み)")

if "line_user" not in st.session_state:
    st.error("LINE認証情報が見つかりません。トップページからログインし直してください。")
    if st.button("トップページへ"):
        logout()
    st.stop()

user = st.session_state["line_user"]

# UI
st.button("ログアウト", on_click=logout)
st.write(f"認証済み: **{user.get('displayName')}** さん")

st.divider()
st.header("HelloWorld!")
st.write("LINE認証済みユーザー専用の投票ページです。")
st.write("LINE認証済みユーザー専用の投票ページです。")
st.write("LINE認証済みユーザー専用の投票ページです。")
