import streamlit as st
import secrets
import logging

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Global Session Manager ---
@st.cache_resource
def get_session_manager():
    return {}  # {line_user_id: current_session_token}

session_manager = get_session_manager()

def check_concurrent_login(line_user_id):
    """同一LINE IDでの複数ログインをチェックし、古いセッションを追い出す"""
    current_token = st.session_state.get("session_token")
    latest_token = session_manager.get(line_user_id)
    
    if latest_token and current_token != latest_token:
        st.error("⚠️ 他の端末でこのLINEアカウントによるログインがあったため、このセッションは無効化されました。")
        if st.button("ログイン画面に戻る"):
            logout()
        st.stop()

# --- Logout Button ---
def logout():
    st.session_state["password_correct"] = False
    if "role" in st.session_state:
        del st.session_state["role"]
    if "username_logged_in" in st.session_state:
        del st.session_state["username_logged_in"]
    if "line_user" in st.session_state:
        del st.session_state["line_user"]
    if "session_token" in st.session_state:
        del st.session_state["session_token"]
    st.rerun()

# --- Main Page UI ---
st.title("📱 選曲投票 (LINE認証済み)")

if "line_user" not in st.session_state:
    st.error("LINE認証情報が見つかりません。トップページからログインし直してください。")
    if st.button("トップページへ"):
        logout()
    st.stop()

user = st.session_state["line_user"]

# 二重ログインチェック
check_concurrent_login(user.get("userId"))

# ログイン成功時のトークン発行（まだない場合）
if "session_token" not in st.session_state:
    new_token = secrets.token_urlsafe(16)
    session_manager[user.get("userId")] = new_token
    st.session_state["session_token"] = new_token

# UI
st.button("ログアウト", on_click=logout)
st.write(f"認証済み: **{user.get('displayName')}** さん")

st.divider()
st.header("HelloWorld!")
st.write("LINE認証済みユーザー専用の投票ページです。")
