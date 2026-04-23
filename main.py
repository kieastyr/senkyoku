import streamlit as st
import bcrypt

# --- Page Configurations ---
st.set_page_config(page_title="選曲ツール", layout="wide")

# --- Authentication Configuration (Passwords can be in st.secrets) ---
# ※ 実際の運用では st.secrets に各ユーザーのハッシュ値を保存するのが安全です。
# 今回は ID とパスワードの対応関係を想定して作成します。
USER_ROLES = {
    "senkyoku_user": "user",
    "senkyoku_voter": "voter",
    "senkyoku_result": "result",
}

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        user = st.session_state["username"]
        pwd = st.session_state["password"]
        
        # st.secrets["auth"] に辞書形式でパスワードが保存されていると想定
        # 例: auth_id_map = {"senkyoku_user": "hashed_pw1", ...}
        # ここではユーザー名が有効かどうかだけチェックし、ハッシュ値は secrets から取得
        try:
            if user in USER_ROLES:
                # 特定のユーザー用のハッシュ値を secrets から取得。なければ fallback
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
            # secrets が設定されていない場合などのエラーハンドリング
            st.error("認証設定（secrets.toml）が正しくありません。")
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("ID", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Log in", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("ID", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Log in", on_click=password_entered)
        st.error("😕 IDまたはパスワードが違います")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- Page Selection ---
role = st.session_state.get("role")

# ルーティング設定
pages = {
    "user": [st.Page("app_pages/senkyoku_user.py", title="選曲・提出", icon="🎼")],
    "voter": [st.Page("app_pages/senkyoku_voter.py", title="選曲投票", icon="🗳️")],
    "result": [st.Page("app_pages/senkyoku_result.py", title="結果表示", icon="📊")],
}

# ログインしたユーザーのロールに応じたページを表示
pg = st.navigation(pages.get(role, []))
pg.run()
