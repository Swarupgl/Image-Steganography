import base64
import hashlib
from datetime import datetime, timedelta

import cv2
from cryptography.fernet import Fernet

_DELIMITER_BITS = "1111111111111110"  # 0xFF 0xFE
_DELIMITER_BYTES = b"\xff\xfe"


def derive_secure_key(user_key: str, pin: str) -> bytes:
    salt = hashlib.sha256(pin.encode()).digest()
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        user_key.encode(),
        salt,
        100000,
    )
    return base64.urlsafe_b64encode(dk)


def create_payload(secret_text: str, unlock_date: datetime) -> str:
    return f"{unlock_date.isoformat()}||{secret_text}"


def _parse_unlock_at(unlock_at):
    if isinstance(unlock_at, datetime):
        return unlock_at
    if isinstance(unlock_at, str):
        try:
            return datetime.fromisoformat(unlock_at)
        except ValueError as e:
            raise ValueError(
                "Invalid unlock_at format. Use 'YYYY-MM-DD HH:MM[:SS]' or 'YYYY-MM-DDTHH:MM[:SS]'."
            ) from e
    raise TypeError("unlock_at must be a str or datetime")


def hide_text_with_timelock(
    image_path: str,
    secret_text: str,
    user_key: str,
    pin: str,
    output_path: str,
    months=None,
    unlock_at=None,
) -> datetime:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image at path: {image_path}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    if unlock_at is not None:
        unlock_date = _parse_unlock_at(unlock_at)
    else:
        if months is None:
            raise ValueError("Provide either months or unlock_at")
        unlock_date = datetime.now() + timedelta(days=30 * float(months))

    payload = create_payload(secret_text, unlock_date)

    secure_key = derive_secure_key(user_key, pin)
    cipher = Fernet(secure_key)

    encrypted_data = cipher.encrypt(payload.encode())
    binary_data = "".join(format(b, "08b") for b in encrypted_data) + _DELIMITER_BITS

    capacity_bits = img.shape[0] * img.shape[1] * 3
    if len(binary_data) > capacity_bits:
        raise ValueError(
            f"Message too large for this image. Need {len(binary_data)} bits, have {capacity_bits} bits."
        )

    idx = 0
    for row in img:
        for pixel in row:
            for i in range(3):
                if idx < len(binary_data):
                    pixel[i] = (pixel[i] & 0xFE) | int(binary_data[idx])
                    idx += 1

    cv2.imwrite(output_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    return unlock_date


def extract_text_with_timelock(stego_image: str, user_key: str, pin: str):
    img = cv2.imread(stego_image)
    if img is None:
        raise FileNotFoundError(f"Could not read image at path: {stego_image}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    secure_key = derive_secure_key(user_key, pin)
    cipher = Fernet(secure_key)

    binary_data = ""
    for row in img:
        for pixel in row:
            for i in range(3):
                binary_data += str(pixel[i] & 1)

    bytes_data = []
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i : i + 8]
        bytes_data.append(int(byte, 2))

    data = bytes(bytes_data)
    encrypted_data = data.split(_DELIMITER_BYTES)[0]

    decrypted_payload = cipher.decrypt(encrypted_data).decode()
    unlock_time_str, message = decrypted_payload.split("||", 1)

    unlock_time = datetime.fromisoformat(unlock_time_str)
    current_time = datetime.now()

    if current_time < unlock_time:
        remaining = unlock_time - current_time
        total_seconds = int(remaining.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        return {
            "status": "locked",
            "unlock_time": unlock_time,
            "remaining": remaining,
            "remaining_human": f"{days} days {hours} hours {minutes} minutes",
        }

    return {
        "status": "unlocked",
        "unlock_time": unlock_time,
        "message": message,
    }
