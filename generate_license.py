import base64
import hashlib
from cryptography.fernet import Fernet

# Hardware ID spesifik dari dongle mouse GAMEN Anda
DONGLE_HARDWARE_ID = "VID_062A&PID_5918"

def generate_key(hardware_id: str) -> bytes:
    """Membuat kunci AES-256 menggunakan SHA-256 dari ID dongle"""
    hash_obj = hashlib.sha256(hardware_id.encode('utf-8'))
    return base64.urlsafe_b64encode(hash_obj.digest())

def buat_lisensi():
    kunci = generate_key(DONGLE_HARDWARE_ID)
    cipher = Fernet(kunci)
    
    # Payload lisensi rahasia
    payload = b"STATUS_VALID:DONGLE_MOUSE_GAMEN_TERVERIFIKASI"
    data_terenkripsi = cipher.encrypt(payload)
    
    with open("app_license.enc", "wb") as f:
        f.write(data_terenkripsi)
        
    print("[+] File lisensi 'app_license.enc' berhasil dibuat menggunakan AES & SHA-256!")

if __name__ == "__main__":
    buat_lisensi()