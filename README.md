## Image Steganography with Time-Lock (Streamlit)

A Streamlit web app for hiding an encrypted, time-locked message inside an image (LSB steganography), with per-user access control for Encode/Decode.

### Key files

- `streamlit_app.py` — Streamlit UI (login + Encode/Decode)
- `stego_timelock.py` — core steganography + crypto logic
- `auth.py` — user auth helpers (PBKDF2 password hashing + verify)
- `manage_users.py` — CLI to add/remove/list users
- `requirements.txt` — Python dependencies

## Run locally (Windows)

1) Create/activate a virtual environment (optional if you already have one)

- `python -m venv .venv`
- `.\.venv\Scripts\Activate.ps1`

2) Install dependencies

- `python -m pip install -r requirements.txt`

3) Create users (local)

This writes `users.json` locally (this file is intentionally ignored by git).

- Encode + Decode:
  - `python manage_users.py add --username demo --permissions encode decode`
- Decode only:
  - `python manage_users.py add --username viewer --permissions decode`
- List users:
  - `python manage_users.py list`

4) Start the app

- `python -m streamlit run streamlit_app.py`

Open the local URL shown in the terminal (usually `http://localhost:8501`).

## Deploy for free (Streamlit Community Cloud)

### 1) Push code to GitHub

- Push the project to a GitHub repo.
- Do not commit `users.json` (it is already in `.gitignore`).

### 2) Create the app on Streamlit Cloud

1) Go to Streamlit Community Cloud
2) Create a new app
3) Select your GitHub repo + branch
4) Set the main file to `streamlit_app.py`
5) Deploy

### 3) Configure users via Streamlit Secrets (TOML)

Streamlit Cloud Secrets uses TOML format.

1) On Streamlit Cloud: App → Settings → Secrets
2) Add a key named `users_json` that contains the *entire* JSON from your local `users.json`.

Example:

```toml
users_json = """
{
  "users": {
    "demo": {
      "password": "pbkdf2_sha256$...",
      "permissions": ["encode", "decode"]
    },
    "viewer": {
      "password": "pbkdf2_sha256$...",
      "permissions": ["decode"]
    }
  }
}
"""
```

Save the secrets and wait about a minute for changes to propagate.

## Troubleshooting

### Streamlit Cloud error: `ImportError: libGL.so.1`

This happens when using GUI OpenCV wheels on a headless Linux server.
This project uses `opencv-python-headless` in `requirements.txt` to avoid that.

### Mobile upload works sometimes

Common causes:

- HEIC/HEIF photos (common on iPhone) are not reliably supported
- Very large photos can fail on mobile data

Fixes:

- iPhone: Settings → Camera → Formats → **Most Compatible** (JPG)
- Try converting the photo to JPG/PNG before uploading
- Use Wi‑Fi for large images

Important: for Decode, stego images are saved as raw bytes (no re-encoding) to preserve hidden LSB data.

## Security notes (important)

- Do not publish `users.json` publicly.
- Even with time-lock logic, anyone who has the encrypted data *and* the correct key+PIN could bypass the UI checks by modifying their own copy of the code. If you need a non-bypassable time-lock, it requires a different design (server-controlled key release or a cryptographic timelock puzzle).
