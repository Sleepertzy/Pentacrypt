# Pentacrypt - Multi-Layered Cryptographic Dashboard

Aplikasi Dashboard Kriptografi Terintegrasi berbasis Streamlit dengan arsitektur keamanan bertingkat (*Multi-Layered Security*), menggabungkan penguncian perangkat keras fisik, autentikasi biometrik, super enkripsi teks, enkripsi berkas, basis data terenkripsi (MySQL), steganografi gambar, dan blockchain ledger.

---

## Fitur Utama

1. **Layer 1 - Kunci Fisik (*Dual-Key Hardware*):**
   - Dongle USB Mouse (`VID_062A&PID_5918`) via WMI COM Threading, **ATAU**
   - Flashdisk Lisensi berisi token terverifikasi (`license.key`).
2. **Layer 2 - Autentikasi Biometrik:**
   - **Face ID:** Verifikasi pengenalan wajah menggunakan OpenCV.
   - **Fingerprint HP:** Sensor biometrik mobile via WebAuthn API dan HTTPS Tunneling (Ngrok).
3. **Super Enkripsi Teks:** Kombinasi kriptografi klasik (Vigenère Cipher) dan modern (AES-256).
4. **Enkripsi File:** Pengamanan berkas menggunakan algoritma berbeda dari modul teks.
5. **Basis Data Terenkripsi (*Field-Level Encryption*):** Penyimpanan data rahasia ke MySQL (XAMPP) dalam wujud *ciphertext* AES (Fernet).
6. **Steganografi Gambar:** Penyisipan pesan ataupun gambar tersembunyi ke dalam citra menggunakan metode LSB (*Least Significant Bit*).
7. **Blockchain Ledger:** Pencatatan aset dan riwayat transaksi dengan hash berantai (SHA-256).

---

## Panduan Menjalankan Secara Lokal

### 1. Prasyarat Sistem
- Windows OS (untuk deteksi modul hardware WMI)
- Python 3.10+
- XAMPP (Apache & MySQL)

### 2. Kloning Repositori & Dependensi
```bash
git clone [https://github.com/Sleepertzy/Pentacrypt.git](https://github.com/Sleepertzy/Pentacrypt.git)
cd Pentacrypt
pip install streamlit cryptography mysql-connector-python psutil wmi pypiwin32 opencv-python pillow webauthn flask requests
```

### 3. Konfigurasi Basis Data (MySQL)
1. Aktifkan modul **Apache** dan **MySQL** di XAMPP Control Panel.
2. Buka `http://localhost/phpmyadmin` dan buat database baru bernama `db_kripto`.
3. Tabel `confidential_data` akan otomatis diinisialisasi saat aplikasi pertama kali dijalankan.

### 4. Konfigurasi Kunci Fisik (Pilih Salah Satu)
- Hubungkan Dongle USB Mouse yang terdaftar ke laptop, **ATAU**
- Siapkan Flashdisk dengan file `license.key` berisi:
  ```text
  KRIPTO_SECURE_TOKEN_2026
  ```

### 5. Menjalankan Aplikasi
- **Jalankan Server Sidik Jari (Terminal 1):**
  ```bash
  python fingerprint_server.py
  ```
- **Jalankan Dashboard Streamlit (Terminal 2):**
  ```bash
  streamlit run app.py
  ```
Akses dashboard pada peramban di alamat `http://localhost:8501`.
