<<<<<<< HEAD
# Image-Steganography
=======
# Time-Locked Image Steganography (Streamlit)

## Run locally

1) Install deps

- `C:\Users\Swarup\Desktop\mini_project\.venv\Scripts\python.exe -m pip install -r requirements.txt`

2) Create users (local)

- Both encode + decode:
  - `...python.exe manage_users.py add --username alice --permissions encode decode`
- Decode only:
  - `...python.exe manage_users.py add --username bob --permissions decode`

3) Start app

- `...python.exe -m streamlit run streamlit_app.py`

## Free deployment options

### Option A: Streamlit Community Cloud (recommended)

1) Push this folder to a GitHub repo (public).
2) Go to Streamlit Community Cloud and deploy `streamlit_app.py`.
3) Add a secret named `users_json` containing your users JSON.

To generate it:
- Create users locally with `manage_users.py` (this writes `users.json`).
- Copy the full contents of `users.json` into the Cloud secret `users_json`.

Example secret (you will paste your real hashed values):

```
{
  "users": {
    "alice": {"password": "pbkdf2_sha256$...", "permissions": ["encode", "decode"]},
    "bob": {"password": "pbkdf2_sha256$...", "permissions": ["decode"]}
  }
}
```

### Option B: Hugging Face Spaces (free)

1) Create a new Space with **Streamlit** SDK.
2) Upload your files (`streamlit_app.py`, `stego_timelock.py`, `auth.py`, `requirements.txt`, etc.).
3) Set an environment variable named `USERS_JSON` with the same JSON content as above.

Notes:
- Don’t commit `users.json` publicly. Use `users_json` secret / `USERS_JSON` env var instead.
- On free hosts, writing files at runtime often won’t persist; secrets/env vars are the reliable way.
