from cryptography.fernet import Fernet
from backend.core.config import get_settings

_cipher: Fernet | None = None


def get_cipher() -> Fernet:
    global _cipher
    if _cipher is None:
        _cipher = Fernet(get_settings().fernet_key.encode())
    return _cipher


def encrypt(plaintext: str) -> bytes:
    return get_cipher().encrypt(plaintext.encode())


def decrypt(token: bytes) -> str:
    return get_cipher().decrypt(token).decode()
