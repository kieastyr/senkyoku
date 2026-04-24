import streamlit as st
import bcrypt
import requests
import urllib.parse
import secrets
import logging

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_client_info():
    """Gathers identification info for logging."""
    try:
        headers = st.context.headers
        # Get IP address (considering potential proxies)
        ip = headers.get("X-Forwarded-For", headers.get("Remote-Addr", "unknown")).split(",")[0]
        user_agent = headers.get("User-Agent", "unknown")
        username = st.session_state.get("username_logged_in", "unknown")
        return f"[User: {username}] [IP: {ip}] [UA: {user_agent}]"
    except Exception:
        return "[Client Info: unknown]"


# Log access
logger.info(f"App accessed: {get_client_info()}")

# --- Page Configurations ---
st.set_page_config(page_title="選曲ツール", layout="wide")

# --- LINE Login Configuration ---
LINE_CLIENT_ID = st.secrets.get("line", {}).get("client_id", "YOUR_CLIENT_ID")
LINE_CLIENT_SECRET = st.secrets.get("line", {}).get(
    "client_secret", "YOUR_CLIENT_SECRET"
)
LINE_REDIRECT_URI = st.secrets.get("line", {}).get("redirect_uri", "YOUR_REDIRECT_URI")


def get_line_login_url():
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
    return (
        f"https://access.line.me/oauth2/v2.1/authorize?{urllib.parse.urlencode(params)}"
    )


def handle_line_callback():
    code = st.query_params.get("code")
    state = st.query_params.get("state")
    if code and state:
        stored_state = st.session_state.get("line_auth_state")
        # Exchange code for access token
        token_url = "https://api.line.me/oauth2/v2.1/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": LINE_REDIRECT_URI,
            "client_id": LINE_CLIENT_ID,
            "client_secret": LINE_CLIENT_SECRET,
        }
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            profile_response = requests.get(
                "https://api.line.me/v2/profile",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if profile_response.status_code == 200:
                user_profile = profile_response.json()
                # ユーザー情報のログ出力
                logger.info(
                    f"LINE Login Success: {user_profile.get('displayName')} (ID: {user_profile.get('userId')})"
                )
                
                st.session_state["line_user"] = user_profile
                st.session_state["password_correct"] = True
                st.session_state["role"] = "tohyo"
                st.session_state["username_logged_in"] = (
                    f"LINE:{user_profile.get('displayName')}"
                )
                st.query_params.clear()
                st.rerun()


# --- Authentication Configuration ---
USER_ROLES = {
    "senkyoku_user": "user",
    "senkyoku_voter": "voter",
    "senkyoku_result": "result",
    "senkyoku_tohyo": "tohyo",
}


def check_password():
    # Handle LINE Callback first
    if "code" in st.query_params:
        handle_line_callback()

    if "password_correct" in st.session_state and st.session_state["password_correct"]:
        return True

    def password_entered():
        user = st.session_state["username"]
        pwd = st.session_state["password"]
        try:
            if user in USER_ROLES:
                stored_hash = st.secrets["auth"].get(user)
                if stored_hash and bcrypt.checkpw(pwd.encode(), stored_hash.encode()):
                    st.session_state["password_correct"] = True
                    st.session_state["role"] = USER_ROLES[user]
                    st.session_state["username_logged_in"] = user
                    del st.session_state["password"]
                    del st.session_state["username"]
                else:
                    st.session_state["password_correct"] = False
            else:
                st.session_state["password_correct"] = False
        except Exception:
            st.error("認証設定（secrets.toml）が正しくありません。")
            st.session_state["password_correct"] = False

    # ID/Password Login Form
    st.text_input("ID", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Log in", on_click=password_entered)

    if (
        "password_correct" in st.session_state
        and not st.session_state["password_correct"]
    ):
        st.error("😕 IDまたはパスワードが違います")

    # --- LINE Login Option ---
    st.write("")
    st.write("")
    st.divider()
    st.write("または")
    login_url = get_line_login_url()
    # スマホ対応のため別タブ(リンク)で案内
    st.link_button("📱 LINEでログイン", login_url, width="stretch")
    st.caption("※LINE認証による本人確認が必要です。")

    return False


if not check_password():
    st.stop()

# --- Page Selection ---
role = st.session_state.get("role")

pages = {
    "user": [st.Page("app_pages/senkyoku_user.py", title="選曲・提出", icon="🎼")],
    "voter": [st.Page("app_pages/senkyoku_voter.py", title="選曲投票", icon="🗳️")],
    "result": [st.Page("app_pages/senkyoku_result.py", title="結果表示", icon="📊")],
    "tohyo": [
        st.Page("app_pages/senkyoku_tohyo.py", title="選曲投票 (LINE)", icon="📱")
    ],
}

pg = st.navigation(pages.get(role, []))
pg.run()
