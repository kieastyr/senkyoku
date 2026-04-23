import streamlit as st
import requests
import urllib.parse
import secrets
import logging

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Global Session Manager ---
# 全ユーザーで共有されるセッション管理テーブル
@st.cache_resource
def get_session_manager():
    return {}  # {line_user_id: current_session_token}

session_manager = get_session_manager()

def check_concurrent_login(line_user_id):
    """同一LINE IDでの複数ログインをチェックし、古いセッションを追い出す"""
    current_token = st.session_state.get("session_token")
    latest_token = session_manager.get(line_user_id)
    
    if latest_token and current_token != latest_token:
        # 他の端末で新しいログインがあった場合
        st.error("⚠️ 他の端末でこのLINEアカウントによるログインがあったため、このセッションは無効化されました。")
        if st.button("ログイン画面に戻る"):
            logout()
        st.stop()

# --- Page Configurations ---
st.title("🗳️ 選曲投票 (LINE認証)")

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

st.button("ログアウト", on_click=logout)

# --- LINE Login Configuration ---
LINE_CLIENT_ID = st.secrets.get("line", {}).get("client_id", "YOUR_CLIENT_ID")
LINE_CLIENT_SECRET = st.secrets.get("line", {}).get("client_secret", "YOUR_CLIENT_SECRET")
LINE_REDIRECT_URI = st.secrets.get("line", {}).get("redirect_uri", "YOUR_REDIRECT_URI")

def get_line_login_url():
    """Generates the LINE login URL."""
    state = secrets.token_urlsafe(16)
    st.session_state["line_auth_state"] = state
    params = {
        "response_type": "code",
        "client_id": LINE_CLIENT_ID,
        "redirect_uri": LINE_REDIRECT_URI,
        "state": state,
        "scope": "profile openid",
        "bot_prompt": "normal",
    }
    return f"https://access.line.me/oauth2/v2.1/authorize?{urllib.parse.urlencode(params)}"

def handle_line_callback():
    """Handles the callback from LINE Login."""
    code = st.query_params.get("code")
    state = st.query_params.get("state")
    
    if code and state:
        stored_state = st.session_state.get("line_auth_state")
        if state != stored_state:
            st.warning("セッションが切り替わった可能性があります。認証を続行します...")

        # Exchange code for access token
        token_url = "https://api.line.me/oauth2/v2.1/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": LINE_REDIRECT_URI,
            "client_id": LINE_CLIENT_ID,
            "client_secret": LINE_CLIENT_SECRET,
        }
        
        with st.spinner("LINE認証を完了しています..."):
            response = requests.post(token_url, headers=headers, data=data)
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                
                # Get user profile
                profile_url = "https://api.line.me/v2/profile"
                profile_headers = {"Authorization": f"Bearer {access_token}"}
                profile_response = requests.get(profile_url, headers=profile_headers)
                
                if profile_response.status_code == 200:
                    user_profile = profile_response.json()
                    line_id = user_profile.get("userId")
                    
                    # セッション管理テーブルを更新（最新のログインとして登録）
                    new_token = secrets.token_urlsafe(16)
                    session_manager[line_id] = new_token
                    st.session_state["session_token"] = new_token
                    st.session_state["line_user"] = user_profile
                    
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"プロフィールの取得に失敗しました: {profile_response.text}")
            else:
                st.error(f"トークン交換に失敗しました。SecretsのRedirect URIが一致しているか確認してください。\nStatus: {response.status_code}")

# --- Authentication Logic ---
if "line_user" not in st.session_state:
    if "code" in st.query_params:
        handle_line_callback()
    else:
        st.write("このページを利用するにはLINEアカウントでのログインが必要です。")
        login_url = get_line_login_url()
        
        # セキュリティ制限を回避するため、新しいタブで開く標準ボタンを使用
        st.link_button("LINEでログイン", login_url, width="stretch")
        st.info("※ブラウザのセキュリティ制限を回避するため、新しいタブが開きます。認証後はそのタブのまま操作を続けてください。")
        st.stop()

# --- Main Content (After Authentication) ---
user = st.session_state["line_user"]
# 実行のたびに他の端末でログインされていないかチェック
check_concurrent_login(user.get("userId"))

st.write(f"認証済み: **{user.get('displayName')}** さん")

st.divider()
st.header("HelloWorld!")
st.write("LINE認証が正常に完了しました。")
