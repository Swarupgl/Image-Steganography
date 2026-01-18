import os
import tempfile
from datetime import datetime

import streamlit as st

from auth import load_users, load_users_from_json_string, load_users_from_mapping, verify_password
from stego_timelock import extract_text_with_timelock, hide_text_with_timelock


def _save_upload_to_temp(uploaded_file) -> str:
    suffix = os.path.splitext(uploaded_file.name)[1] or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return tmp.name


def _read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


st.set_page_config(page_title="Time-Locked Steganography", layout="centered")
st.title("Time-Locked Image Steganography")

USERS_FILE = "users.json"

# Deployment-friendly user loading:
# - Prefer env var USERS_JSON (works on Hugging Face Spaces, Render, etc.)
# - Then Streamlit secrets (Streamlit Community Cloud): users_json or users mapping
# - Finally local users.json for development
users = {}
users_json_env = os.getenv("USERS_JSON")
if users_json_env:
    users = load_users_from_json_string(users_json_env)
elif hasattr(st, "secrets"):
    try:
        if "users_json" in st.secrets:
            users = load_users_from_json_string(st.secrets["users_json"])
        elif "users" in st.secrets:
            users = load_users_from_mapping({"users": dict(st.secrets["users"])})
    except Exception:
        users = {}

if not users:
    users = load_users(USERS_FILE)

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None
if "auth_perms" not in st.session_state:
    st.session_state.auth_perms = []

with st.sidebar:
    st.header("Access")
    if st.session_state.auth_user:
        st.write(f"Signed in as: {st.session_state.auth_user}")
        if st.button("Logout"):
            st.session_state.auth_user = None
            st.session_state.auth_perms = []
            st.rerun()
    else:
        st.caption("Sign in to use the app")

if not users:
    st.error(
        "No users are configured. Provide USERS_JSON (env var) or Streamlit secrets (users_json), or create users.json with manage_users.py."
    )
    st.stop()

if not st.session_state.auth_user:
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        record = users.get(username)
        if record and verify_password(record.password, password):
            st.session_state.auth_user = record.username
            st.session_state.auth_perms = record.permissions
            st.rerun()
        else:
            st.error("Invalid username or password")
    st.stop()

allowed_modes = []
if "encode" in st.session_state.auth_perms:
    allowed_modes.append("Hide (Encode)")
if "decode" in st.session_state.auth_perms:
    allowed_modes.append("Extract (Decode)")

if not allowed_modes:
    st.error("Your account has no permissions assigned (encode/decode).")
    st.stop()

mode = allowed_modes[0] if len(allowed_modes) == 1 else st.radio("Mode", allowed_modes, horizontal=True)

if mode == "Hide (Encode)":
    uploaded = st.file_uploader("Cover image", type=["png", "jpg", "jpeg", "bmp"])
    secret_text = st.text_area("Secret text")

    user_key = st.text_input("User key", type="password")
    pin = st.text_input("PIN", type="password")

    lock_mode = st.radio(
        "Unlock time",
        ["Months from now", "Specific date/time"],
        horizontal=True,
    )

    months = None
    unlock_at = None

    if lock_mode == "Months from now":
        months = st.number_input("Months", min_value=0.0, value=1.0, step=0.5)
    else:
        col1, col2 = st.columns(2)
        with col1:
            unlock_date = st.date_input("Unlock date")
        with col2:
            unlock_time = st.time_input("Unlock time")
        unlock_at = datetime.combine(unlock_date, unlock_time)

    if st.button("Generate stego image", type="primary"):
        if uploaded is None:
            st.error("Please upload an image.")
        elif not secret_text.strip():
            st.error("Please enter secret text.")
        elif not user_key.strip() or not pin.strip():
            st.error("Please enter both User key and PIN.")
        else:
            input_path = None
            output_path = None
            try:
                input_path = _save_upload_to_temp(uploaded)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as out:
                    output_path = out.name

                unlock_dt = hide_text_with_timelock(
                    image_path=input_path,
                    secret_text=secret_text,
                    user_key=user_key,
                    pin=pin,
                    output_path=output_path,
                    months=months,
                    unlock_at=unlock_at,
                )

                out_bytes = _read_file_bytes(output_path)

                st.success(f"Image locked until: {unlock_dt.isoformat(sep=' ', timespec='seconds')}")
                st.image(out_bytes, caption="Stego image", width="stretch")
                st.download_button(
                    "Download stego image",
                    data=out_bytes,
                    file_name="time_locked_image.png",
                    mime="image/png",
                )
            except Exception as e:
                st.error(str(e))
            finally:
                # Best-effort cleanup of temp files
                for p in [input_path, output_path]:
                    if p and os.path.exists(p):
                        try:
                            os.remove(p)
                        except OSError:
                            pass

else:
    uploaded = st.file_uploader("Stego image", type=["png", "jpg", "jpeg", "bmp"])
    user_key = st.text_input("User key", type="password")
    pin = st.text_input("PIN", type="password")

    if st.button("Extract", type="primary"):
        if uploaded is None:
            st.error("Please upload a stego image.")
        elif not user_key.strip() or not pin.strip():
            st.error("Please enter both User key and PIN.")
        else:
            input_path = None
            try:
                input_path = _save_upload_to_temp(uploaded)
                result = extract_text_with_timelock(
                    stego_image=input_path,
                    user_key=user_key,
                    pin=pin,
                )

                if result.get("status") == "locked":
                    st.warning("Access denied (still locked)")
                    st.write("Unlock time:")
                    st.code(result["unlock_time"].isoformat(sep=" ", timespec="seconds"))
                    st.write("Time remaining:")
                    st.code(result["remaining_human"])
                else:
                    st.success("Access granted")
                    st.write("Unlock time:")
                    st.code(result["unlock_time"].isoformat(sep=" ", timespec="seconds"))
                    st.write("Message:")
                    st.text_area(
                        "Message",
                        value=result.get("message", ""),
                        height=180,
                        label_visibility="collapsed",
                    )
            except Exception:
                st.error("Wrong KEY, PIN, or corrupted image")
            finally:
                if input_path and os.path.exists(input_path):
                    try:
                        os.remove(input_path)
                    except OSError:
                        pass
