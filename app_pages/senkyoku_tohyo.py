import streamlit as st
import requests
import urllib.parse
import secrets
import logging

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

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
            st.warning(f"State mismatch (Expected: {stored_state}, Got: {state}). Proceeding anyway for debugging...")

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
                    st.session_state["line_user"] = user_profile
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"プロフィールの取得に失敗しました: {profile_response.text}")
            else:
                st.error(f"トークン交換に失敗しました。Redirect URIが一致しているか確認してください。\nStatus: {response.status_code}\nResponse: {response.text}")

# --- Authentication Logic ---
if "line_user" not in st.session_state:
    if "code" in st.query_params:
        handle_line_callback()
    else:
        st.write("このページを利用するにはLINEアカウントでのログインが必要です。")
        login_url = get_line_login_url()
        
        # モバイル・iframe対応: target="_top" で親ウィンドウごと遷移させる
        # これによりリンクが反応し、かつ COOP 制限を回避します
        st.markdown(
            f"""
            <a href="{login_url}" target="_top" style="text-decoration: none;">
                <div style="
                    background-color: #06C755;
                    color: white;
                    padding: 0.6rem 1rem;
                    border-radius: 0.5rem;
                    text-align: center;
                    font-weight: bold;
                    cursor: pointer;
                    border: none;
                    display: inline-block;
                    width: 100%;
                    font-size: 1rem;
                ">
                    LINEでログイン
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )
        st.stop()

# --- Main Content (After Authentication) ---
user = st.session_state["line_user"]
st.write(f"認証済み: **{user.get('displayName')}** さん (LINE ID: {user.get('userId')})")

st.divider()
st.header("HelloWorld!")
st.write("LINE認証が正常に完了しました。")
