import base64
import hashlib
import os
import sys
from cryptography.fernet import Fernet
import wmi

# Target identitas dongle mouse GAMEN
TARGET_DONGLE_ID = "VID_062A&PID_5918"

def cek_keberadaan_dongle(target_id: str) -> bool:
    """Memeriksa apakah dongle mouse GAMEN tertancap di PC"""
    c = wmi.WMI()
    for device in c.Win32_PnPEntity():
        dev_id = str(device.DeviceID)
        if target_id.lower() in dev_id.lower():
            return True
    return False

def verifikasi_lisensi_kriptografi(target_id: str) -> bool:
    """Mendekripsi file lisensi dengan kunci SHA-256 dari Hardware ID dongle"""
    if not os.path.exists("app_license.enc"):
        return False

    try:
        hash_obj = hashlib.sha256(target_id.encode('utf-8'))
        kunci = base64.urlsafe_b64encode(hash_obj.digest())
        cipher = Fernet(kunci)

        with open("app_license.enc", "rb") as f:
            encrypted_data = f.read()

        hasil_dekripsi = cipher.decrypt(encrypted_data)
        return b"STATUS_VALID" in hasil_dekripsi
    except Exception:
        return False

def main():
    print("=" * 55)
    print("     SISTEM KEAMANAN APLIKASI KRIPTOGRAFI")
    print("=" * 55)
    print("[*] Memeriksa Dongle Hardware (GAMEN Wireless Mouse)...")

    # 1. Pengecekan Fisik Hardware Dongle
    if not cek_keberadaan_dongle(TARGET_DONGLE_ID):
        print("\n[!] DONGLE TIDAK TERDETEKSI!")
        print("[!] Aplikasi terkunci. Harap pasang dongle mouse Anda.")
        sys.exit(1)

    print("[+] Dongle fisik terdeteksi di slot USB.")

    # 2. Dekripsi Kriptografi (Hash SHA-256 + AES Fernet)
    print("[*] Memvalidasi file lisensi kriptografis...")
    if not verifikasi_lisensi_kriptografi(TARGET_DONGLE_ID):
        print("\n[!] VERIFIKASI GAGAL: Lisensi tidak valid atau tidak cocok!")
        sys.exit(1)

    print("[+] Validasi Kriptografi Berhasil: Kunci Hardware Sah.")
    print("-" * 55)
    
    # 3. Lanjut ke Menu Login Biometrik
    menu_login_biometrik()

def menu_login_biometrik():
    print("\n[ SILAHKAN PILIH METODE LOGIN BIOMETRIK ]")
    print("1. Face ID (Kamera)")
    print("2. Keystroke Dynamics (Dinamika Ketikan)")
    print("3. Keluar")
    pilihan = input("Pilih [1/2/3]: ")

    if pilihan == "1":
        print("\n[*] Menjalankan modul Face ID...")
        # Integrasikan modul kamera & face recognition di sini
    elif pilihan == "2":
        print("\n[*] Menjalankan modul Keystroke Biometric...")
        # Integrasikan modul keystroke biometric di sini
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()