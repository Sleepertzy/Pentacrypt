import base64
import hashlib
import json
import os
import sqlite3
import time
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import cv2
import mysql.connector
import io
import numpy as np
from PIL import Image
import subprocess
import pythoncom
import streamlit as st
import streamlit.components.v1 as components
import psutil  # pip install psutil
import wmi  # pip install wmi

st.set_page_config(
    page_title="Sistem Kriptografi Terintegrasi", page_icon="🛡️", layout="wide"
)

TARGET_DONGLE_ID = "VID_062A&PID_5918"

# =========================================================
# 1. GERBANG DONGLE HARDWARE & LISENSI (DUAL-KEY: DONGLE / FLASHDISK)
# =========================================================
# Target ID Hardware Mouse GAMEN (Receiver USB Asli)
TARGET_DONGLE_ID = "VID_062A&PID_5918"

# Konfigurasi Token Kunci Rahasia untuk Flashdisk
FLASHDISK_KEY_FILENAME = "license.key"
SECRET_LICENSE_TOKEN = "KRIPTO_SECURE_TOKEN_2026"


def verify_physical_keys():
  has_dongle = False
  has_flashdisk = False
  detected_drive = None

  # --- OPSI 1: DETEKSI DONGLE MOUSE USB (METODE KODE LAMA ANDA) ---
  try:
    pythoncom.CoInitialize()
    c = wmi.WMI()

    # Bersihkan target string agar pencocokan fleksibel
    target_clean = TARGET_DONGLE_ID.lower().replace("&", "")

    for device in c.Win32_PnPEntity():
      dev_id = str(device.DeviceID or "").lower().replace("&", "")
      pnp_id = str(device.PNPDeviceID or "").lower().replace("&", "")
      status = str(device.Status or "").upper()

      # Cek kecocokan ID dongle
      if target_clean in dev_id or target_clean in pnp_id:
        # Verifikasi status operasional peranti saat ini
        if status == "OK":
          has_dongle = True
          break
  except Exception as e:
    has_dongle = False
  finally:
    try:
      pythoncom.CoUninitialize()
    except Exception:
      pass

  # --- OPSI 2: DETEKSI FLASHDISK (MEMINDAI SELURUH DRIVE KECUALI C:) ---
  try:
    for p in psutil.disk_partitions(all=True):
      if p.mountpoint.upper().startswith("C"):
        continue

      key_candidates = [
          os.path.join(p.mountpoint, FLASHDISK_KEY_FILENAME),
          os.path.join(p.mountpoint, "license.key.txt"),
      ]

      for candidate in key_candidates:
        if os.path.isfile(candidate):
          try:
            with open(candidate, "r", encoding="utf-8") as f:
              token_content = f.read().strip()
              if token_content == SECRET_LICENSE_TOKEN:
                has_flashdisk = True
                detected_drive = p.mountpoint
                break
          except Exception:
            continue
      if has_flashdisk:
        break
  except Exception:
    has_flashdisk = False

  access_granted = has_dongle or has_flashdisk
  return access_granted, has_dongle, has_flashdisk, detected_drive


# Jalankan verifikasi kunci fisik
is_unlocked, dongle_status, flashdisk_status, flashdisk_drive = (
    verify_physical_keys()
)

# Tampilkan status di Sidebar
with st.sidebar:
  st.markdown("### 🔑 Status Kunci Fisik (Hardware)")
  if dongle_status:
    st.success("🟢 **Dongle Mouse:** Terpasang")
  else:
    st.info("⚪ **Dongle Mouse:** Tidak Terdeteksi")

  if flashdisk_status:
    st.success(f"🟢 **Flashdisk Kunci:** Aktif ({flashdisk_drive})")
  else:
    st.info("⚪ **Flashdisk Kunci:** Tidak Terdeteksi")
  st.markdown("---")

# Kunci sistem jika belum lolos verifikasi fisik
if not is_unlocked:
  st.error("🚨 **AKSES DITOLAK: KUNCI PERANGKAT KERAS TIDAK DITEMUKAN**")
  st.warning(
      "Aplikasi ini membutuhkan validasi fisik tingkat perangkat. Silakan"
      " hubungkan salah satu kunci berikut ke laptop:\n"
      "1. **Dongle USB Mouse GAMEN** pada port USB laptop, **ATAU**\n"
      f"2. **Flashdisk** yang berisi file `{FLASHDISK_KEY_FILENAME}` dengan"
      " token lisensi yang valid."
  )

  if st.button(
      "🔄 Pindai Ulang Perangkat",
      key="btn_recheck_keys_retry",
      use_container_width=True,
  ):
    st.rerun()

  st.stop()
  
# =========================================================
# 2. GERBANG BIOMETRIK FACE ID (LBPH)
# =========================================================


def verify_face(uploaded_img_bytes):
  if not os.path.exists("face_model.yml"):
    return (
        False,
        "Model 'face_model.yml' belum ada! Jalankan setup_auth.py dahulu.",
    )

  recognizer = cv2.face.LBPHFaceRecognizer_create()
  recognizer.read("face_model.yml")

  file_bytes = np.asarray(bytearray(uploaded_img_bytes.read()), dtype=np.uint8)
  img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
  gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

  cascade_path = "haarcascade_frontalface_default.xml"
  if not os.path.exists(cascade_path):
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

  face_cascade = cv2.CascadeClassifier(cascade_path)
  faces = face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(80, 80))

  if len(faces) == 0:
    return False, "Wajah tidak terdeteksi. Posisikan wajah tepat di kamera."

  x, y, w, h = faces[0]
  face_roi = cv2.resize(gray[y : y + h, x : x + w], (200, 200))
  label, confidence = recognizer.predict(face_roi)

  if label == 1 and confidence < 68:
    return (
        True,
        f"Autentikasi Berhasil! Tingkat deviasi biometrik: {int(confidence)}",
    )
  else:
    return (
        False,
        f"Akses Ditolak: Wajah tidak cocok! Tingkat deviasi: {int(confidence)}",
    )




st.sidebar.success("🔑 Lisensi Terdekripsi")

# =========================================================
# GERBANG 3: AUTENTIKASI BIOMETRIK (FACE ID ATAU FINGERPRINT)
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Login Biometrik")
    st.info("Dongle Hardware terverifikasi. Silakan pilih metode autentikasi biometrik:")

    tab_face, tab_finger = st.tabs(["📷 Face ID (Kamera)", "👆 Fingerprint (Sensor HP)"])

    # --- PILIHAN 1: FACE ID ---
    with tab_face:
        st.subheader("Login Wajah")
        cam_shot = st.camera_input("Arahkan wajah Anda ke kamera:")
        if cam_shot:
            with st.spinner("Mencocokkan biometrik wajah..."):
                is_valid, msg = verify_face(cam_shot)
                if is_valid:
                    st.success(msg)
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error(msg)

# --- PILIHAN 2: FINGERPRINT SENSOR HP (WEBAUTHN STANDALONE) ---
    with tab_finger:
        st.subheader("Login Sidik Jari (Fingerprint)")
        st.write("Gunakan sensor sidik jari bawaan HP Anda untuk memvalidasi identitas.")

        # Periksa apakah ada token lolos autentikasi dari URL
        token = st.query_params.get("fp_auth", None)

        if token == "VERIFIED_SUCCESS":
            st.success("✅ Sidik Jari Berhasil Divalidasi!")
            if st.button("🔓 Buka Dashboard Utama", key="btn_enter_fp", use_container_width=True):
                # Bersihkan parameter dari URL agar bersih dan kunci sesi login
                st.query_params.clear()
                st.session_state.authenticated = True
                st.rerun()
        else:
            st.warning("⚠️ Akses Terkunci: Silakan pindai sidik jari Anda melalui tautan aman HTTPS.")

            # Tautan HTTPS Localtunnel Anda
            auth_url = "https://gutter-amnesty-perplexed.ngrok-free.dev"

            st.markdown(
                f"""
                <div style="text-align: center; margin: 15px 0;">
                    <a href="{auth_url}" target="_self" style="
                        background-color: #00c853;
                        color: white;
                        padding: 14px 24px;
                        text-decoration: none;
                        font-weight: bold;
                        border-radius: 8px;
                        display: inline-block;
                        font-size: 16px;
                    ">👆 Buka Pemindai Sidik Jari HP (HTTPS)</a>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Kunci tampilan dashboard agar tidak bocor sebelum autentikasi selesai (Inden 4 spasi)
    st.stop()
    
# =========================================================
# FUNGSI MODUL 1: SUPER ENKRIPSI TEKS (VIGENERE + AES)
# =========================================================


def vigenere_encrypt(plaintext, key):
  res = []
  key = key.upper()
  ki = 0
  for c in plaintext:
    if c.isalpha():
      base = ord("A") if c.isupper() else ord("a")
      shift = ord(key[ki % len(key)]) - ord("A")
      res.append(chr((ord(c) - base + shift) % 26 + base))
      ki += 1
    else:
      res.append(c)
  return "".join(res)


def vigenere_decrypt(ciphertext, key):
  res = []
  key = key.upper()
  ki = 0
  for c in ciphertext:
    if c.isalpha():
      base = ord("A") if c.isupper() else ord("a")
      shift = ord(key[ki % len(key)]) - ord("A")
      res.append(chr((ord(c) - base - shift) % 26 + base))
      ki += 1
    else:
      res.append(c)
  return "".join(res)


def super_encrypt(plaintext, vig_key, aes_key_str):
  step1 = vigenere_encrypt(plaintext, vig_key)
  aes_key = hashlib.sha256(aes_key_str.encode()).digest()
  fernet_key = base64.urlsafe_b64encode(aes_key)
  f = Fernet(fernet_key)
  return f.encrypt(step1.encode("utf-8")).decode("utf-8")


def super_decrypt(ciphertext, vig_key, aes_key_str):
  aes_key = hashlib.sha256(aes_key_str.encode()).digest()
  fernet_key = base64.urlsafe_b64encode(aes_key)
  f = Fernet(fernet_key)
  step1 = f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
  return vigenere_decrypt(step1, vig_key)


# =========================================================
# FUNGSI MODUL 2: ENKRIPSI FILE (CHACHA20-POLY1305)
# =========================================================


def encrypt_file_chacha(file_bytes: bytes, original_filename: str, password: str) -> bytes:
  """
  Format file terenkripsi:
  [4 byte panjang header JSON] + [Header JSON metadata] + [12 byte Nonce] + [Ciphertext]
  """
  # Turunkan kunci 256-bit (32 bytes) menggunakan SHA-256
  key = hashlib.sha256(password.encode('utf-8')).digest()
  chacha = ChaCha20Poly1305(key)
  nonce = os.urandom(12)

  # Simpan metadata nama file asli
  metadata = json.dumps({'filename': original_filename}).encode('utf-8')
  meta_len = len(metadata).to_bytes(4, byteorder='big')

  # Enkripsi data biner file
  ciphertext = chacha.encrypt(nonce, file_bytes, None)

  # Gabungkan struktur file
  return meta_len + metadata + nonce + ciphertext


def decrypt_file_chacha(encrypted_bytes: bytes, password: str):
  """Mendekripsi file dan mengembalikan byte data asli beserta nama file aslinya"""
  key = hashlib.sha256(password.encode('utf-8')).digest()
  chacha = ChaCha20Poly1305(key)

  # 1. Baca panjang header metadata
  meta_len = int.from_bytes(encrypted_bytes[:4], byteorder='big')

  # 2. Ekstrak metadata
  meta_end = 4 + meta_len
  metadata = json.loads(encrypted_bytes[4:meta_end].decode('utf-8'))
  original_filename = metadata.get('filename', 'restored_file.dat')

  # 3. Ekstrak Nonce dan Ciphertext
  nonce = encrypted_bytes[meta_end : meta_end + 12]
  ciphertext = encrypted_bytes[meta_end + 12 :]

  # 4. Dekripsi
  decrypted_bytes = chacha.decrypt(nonce, ciphertext, None)
  return decrypted_bytes, original_filename


# =========================================================
# FUNGSI MODUL 3: DATABASE TERENKRIPSI (MYSQL)
# =========================================================


# --- KONEKSI KE MYSQL (XAMPP) ---
def get_db_connection():
  return mysql.connector.connect(
      host="localhost",
      user="root",
      password="",  # Kosongkan jika menggunakan XAMPP default
      database="db_kripto",
  )


# Inisialisasi tabel jika belum ada
def init_mysql_table():
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS encrypted_vault (
                id INT AUTO_INCREMENT PRIMARY KEY,
                label VARCHAR(255) NOT NULL,
                encrypted_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    cursor.close()
    conn.close()
  except Exception as e:
    st.error(f"Gagal koneksi ke MySQL: {e}")


# --- FUNGSI DERIVASI KUNCI & ENKRIPSI/DEKRIPSI AES (FERNET) ---
def get_fernet_cipher(password: str):
  # Hash SHA-256 password agar pas 32-byte untuk Fernet (AES-128 CBC + HMAC)
  key = hashlib.sha256(password.encode()).digest()
  return Fernet(base64.urlsafe_b64encode(key))


def encrypt_data(plain_text: str, secret_key: str) -> str:
  cipher = get_fernet_cipher(secret_key)
  return cipher.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_data(cipher_text: str, secret_key: str) -> str:
  cipher = get_fernet_cipher(secret_key)
  return cipher.decrypt(cipher_text.encode("utf-8")).decode("utf-8")


# --- OPERASI DATABASE MYSQL ---
def save_secret_record(label: str, raw_secret: str, secret_key: str):
  encrypted_blob = encrypt_data(raw_secret, secret_key)
  conn = get_db_connection()
  cursor = conn.cursor()
  query = (
      "INSERT INTO encrypted_vault (label, encrypted_data) VALUES (%s, %s)"
  )
  cursor.execute(query, (label, encrypted_blob))
  conn.commit()
  cursor.close()
  conn.close()


def fetch_all_records():
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)
  cursor.execute(
      "SELECT id, label, encrypted_data FROM encrypted_vault ORDER BY id DESC"
  )
  rows = cursor.fetchall()
  cursor.close()
  conn.close()
  return rows


# =========================================================
# FUNGSI MODUL 4: STEGANOGRAFI GAMBAR LSB
# =========================================================

def lsb_encode(image: Image.Image, message: str) -> Image.Image:
  """Menyisipkan pesan ke bit paling tidak signifikan (LSB) pada kanal RGB"""
  # Konversi ke RGB murni (menghilangkan channel alpha RGBA bila ada)
  img_rgb = image.convert('RGB')
  pixels = np.array(img_rgb, dtype=np.uint8)

  # Ubah pesan teks menjadi representasi biner UTF-8
  msg_bytes = message.encode('utf-8')
  msg_len = len(msg_bytes)

  # 32 bit pertama untuk menyimpan panjang pesan (dalam byte)
  len_bits = format(msg_len, '032b')
  msg_bits = ''.join(format(b, '08b') for b in msg_bytes)
  total_bits = len_bits + msg_bits

  flat_pixels = pixels.flatten()

  if len(total_bits) > len(flat_pixels):
    raise ValueError(
        f'Ukuran pesan terlalu besar ({len(total_bits)} bit). Kapasitas gambar'
        f' hanya {len(flat_pixels)} bit!'
    )

  # Modifikasi LSB: gunakan & 254 (0xFE / 11111110) agar aman untuk uint8
  for i in range(len(total_bits)):
    bit = int(total_bits[i])
    flat_pixels[i] = (flat_pixels[i] & 254) | bit

  reshaped = flat_pixels.reshape(pixels.shape)
  return Image.fromarray(reshaped, mode='RGB')


def lsb_encode_image(cover_img: Image.Image, secret_img_bytes: bytes, secret_filename: str) -> Image.Image:
    """
    Menyisipkan byte gambar rahasia ke dalam bit LSB cover image.
    Struktur payload: [4 byte panjang metadata JSON] + [JSON Metadata] + [Data Biner Gambar]
    """
    cover_rgb = cover_img.convert("RGB")
    pixels = np.array(cover_rgb, dtype=np.uint8)
    flat_pixels = pixels.flatten()

    # Siapkan metadata (nama file & ukuran gambar rahasia)
    metadata = json.dumps({
        "filename": secret_filename,
        "size": len(secret_img_bytes)
    }).encode("utf-8")

    meta_len = len(metadata)
    meta_len_bits = format(meta_len, "032b")  # 32 bit pertama untuk panjang header JSON
    meta_bits = "".join(format(b, "08b") for b in metadata)
    secret_bits = "".join(format(b, "08b") for b in secret_img_bytes)

    total_bits = meta_len_bits + meta_bits + secret_bits

    if len(total_bits) > len(flat_pixels):
        raise ValueError(
            f"Ukuran gambar rahasia terlalu besar ({len(total_bits)} bit dibutuhkan)! "
            f"Kapasitas gambar penampung hanya {len(flat_pixels)} bit. "
            f"Gunakan cover image dengan resolusi piksel lebih tinggi."
        )

    # Sisipkan bit ke LSB menggunakan mask 254 (0xFE)
    for i in range(len(total_bits)):
        flat_pixels[i] = (flat_pixels[i] & 254) | int(total_bits[i])

    reshaped = flat_pixels.reshape(pixels.shape)
    return Image.fromarray(reshaped, mode="RGB")


def lsb_decode_image(stego_img: Image.Image):
    """Mengekstrak data byte gambar rahasia dari stego image LSB"""
    stego_rgb = stego_img.convert("RGB")
    pixels = np.array(stego_rgb, dtype=np.uint8)
    flat_pixels = pixels.flatten()

    if len(flat_pixels) < 32:
        raise ValueError("Gambar terlalu kecil atau bukan stego-image yang valid.")

    # 1. Baca 32 bit pertama untuk mengetahui panjang metadata JSON
    meta_len_bits = "".join(str(flat_pixels[i] & 1) for i in range(32))
    meta_len = int(meta_len_bits, 2)

    meta_bit_end = 32 + (meta_len * 8)
    if meta_bit_end > len(flat_pixels):
        raise ValueError("Gambar ini tidak memuat data steganografi yang sah.")

    # 2. Ekstrak metadata JSON
    meta_bits = [str(flat_pixels[i] & 1) for i in range(32, meta_bit_end)]
    meta_bytes = bytearray()
    for i in range(0, len(meta_bits), 8):
        meta_bytes.append(int("".join(meta_bits[i:i+8]), 2))
    
    metadata = json.loads(meta_bytes.decode("utf-8"))
    secret_filename = metadata.get("filename", "extracted_secret.png")
    secret_size = metadata.get("size", 0)

    # 3. Ekstrak data biner gambar rahasia
    secret_bit_end = meta_bit_end + (secret_size * 8)
    if secret_bit_end > len(flat_pixels):
        raise ValueError("Data gambar rahasia terpotong atau rusak.")

    payload_bits = [str(flat_pixels[i] & 1) for i in range(meta_bit_end, secret_bit_end)]
    secret_bytes = bytearray()
    for i in range(0, len(payload_bits), 8):
        secret_bytes.append(int("".join(payload_bits[i:i+8]), 2))

    return bytes(secret_bytes), secret_filename

# =========================================================
# FUNGSI STEGANOGRAFI TEKS (LSB)
# =========================================================

def lsb_encode(image: Image.Image, message: str) -> Image.Image:
    """Menyisipkan pesan teks ke dalam LSB cover image PNG"""
    img_rgb = image.convert("RGB")
    pixels = np.array(img_rgb, dtype=np.uint8)
    
    msg_bytes = message.encode("utf-8")
    msg_len = len(msg_bytes)
    
    # 32 bit pertama menyimpan panjang pesan dalam byte
    len_bits = format(msg_len, "032b")
    msg_bits = "".join(format(b, "08b") for b in msg_bytes)
    total_bits = len_bits + msg_bits
    
    flat_pixels = pixels.flatten()
    if len(total_bits) > len(flat_pixels):
        raise ValueError(
            f"Pesan terlalu panjang ({len(total_bits)} bit). "
            f"Kapasitas gambar hanya {len(flat_pixels)} bit!"
        )
        
    for i in range(len(total_bits)):
        flat_pixels[i] = (flat_pixels[i] & 254) | int(total_bits[i])
        
    reshaped = flat_pixels.reshape(pixels.shape)
    return Image.fromarray(reshaped, mode="RGB")


def lsb_decode(image: Image.Image) -> str:
    """Mengekstrak pesan teks dari LSB gambar PNG"""
    img_rgb = image.convert("RGB")
    pixels = np.array(img_rgb, dtype=np.uint8)
    flat_pixels = pixels.flatten()
    
    if len(flat_pixels) < 32:
        return "Gambar terlalu kecil untuk memuat data steganografi."
        
    # 1. Baca 32 bit awal untuk panjang data
    len_bits = "".join(str(flat_pixels[i] & 1) for i in range(32))
    msg_len = int(len_bits, 2)
    
    total_msg_bits = msg_len * 8
    if 32 + total_msg_bits > len(flat_pixels):
        return "Tidak ditemukan pesan rahasia yang valid pada gambar ini."
        
    # 2. Baca isi payload teks
    bits = [str(flat_pixels[i] & 1) for i in range(32, 32 + total_msg_bits)]
    byte_list = bytearray()
    
    for i in range(0, len(bits), 8):
        byte_list.append(int("".join(bits[i:i+8]), 2))
        
    try:
        return byte_list.decode("utf-8")
    except UnicodeDecodeError:
        return "Gagal memproses pesan: data bukan representasi teks valid."


# =========================================================
# FUNGSI MODUL 5: BLOCKCHAIN ASET SEDERHANA
# =========================================================


class Block:

  def __init__(self, index, timestamp, data, previous_hash):
    self.index = index
    self.timestamp = timestamp
    self.data = data
    self.previous_hash = previous_hash
    self.hash = self.compute_hash()

  def compute_hash(self):
    block_string = (
        f"{self.index}{self.timestamp}{json.dumps(self.data)}{self.previous_hash}"
    )
    return hashlib.sha256(block_string.encode()).hexdigest()


def load_blockchain():
  if not os.path.exists("blockchain.json"):
    genesis = Block(0, time.time(), {"info": "Genesis Block"}, "0")
    chain = [genesis.__dict__]
    with open("blockchain.json", "w") as f:
      json.dump(chain, f, indent=4)
    return chain
  with open("blockchain.json", "r") as f:
    return json.load(f)


def add_block_to_chain(asset_data):
  chain = load_blockchain()
  prev_block = chain[-1]
  new_block = Block(
      index=len(chain),
      timestamp=time.time(),
      data=asset_data,
      previous_hash=prev_block["hash"],
  )
  chain.append(new_block.__dict__)
  with open("blockchain.json", "w") as f:
    json.dump(chain, f, indent=4)
  return new_block


# =========================================================
# NAVIGASI FITUR UTAMA
# =========================================================
st.title("🛡️ Dashboard Aplikasi Kriptografi Terintegrasi")
st.markdown("---")

menu = st.sidebar.selectbox(
    "Pilih Modul Tugas:",
    [
        "Super Enkripsi Teks",
        "Enkripsi File",
        "Steganografi Gambar LSB",
        "Database Sensitif Terenkripsi",
        "Ledger Blockchain Aset",
    ],
)

# ----------------- MODUL 1 -----------------
if menu == "Super Enkripsi Teks":
  st.subheader(
      "🔤 Super Enkripsi Teks (Klasik Vigenère + Modern AES-256)"
  )  #
  tab1, tab2 = st.tabs(["Enkripsi Teks", "Dekripsi Teks"])

  with tab1:
    txt_input = st.text_area("Masukkan Plaintext:")
    k_vig = st.text_input("Kunci Vigenere (Abjad):", "KRIPTO")
    k_aes = st.text_input("Kunci AES (Password):", "RAHASIA")
    if st.button("Jalankan Super Enkripsi"):
      if txt_input and k_vig and k_aes:
        cipher = super_encrypt(txt_input, k_vig, k_aes)
        st.success("Teks Berhasil Dienkripsi Berlapis!")
        st.code(cipher, language="text")
      else:
        st.warning("Lengkapi seluruh input.")

  with tab2:
    cip_input = st.text_area("Masukkan Ciphertext:")
    k_vig_d = st.text_input("Kunci Vigenere Dekripsi:", "KRIPTO")
    k_aes_d = st.text_input("Kunci AES Dekripsi:", "RAHASIA")
    if st.button("Jalankan Super Dekripsi"):
      try:
        recovered = super_decrypt(cip_input, k_vig_d, k_aes_d)
        st.success("Teks Berhasil Didekripsi:")
        st.info(recovered)
      except Exception:
        st.error("Kunci salah atau ciphertext rusak!")

# ----------------- MODUL 2 -----------------
elif menu == "Enkripsi File":
  st.subheader("📁 Enkripsi Dokumen & File (ChaCha20-Poly1305)")
  tab1, tab2 = st.tabs(["🔒 Enkripsi File", "🔓 Dekripsi File"])

  with tab1:
    f_upload = st.file_uploader(
        "Pilih File Asli (PDF, DOCX, ZIP, Gambar, dll):", key="uploader_enc"
    )
    f_pass = st.text_input(
        "Kunci Sandi Enkripsi File:", "RahasiaFile123", type="password", key="pass_enc"
    )

    if st.button("Mulai Enkripsi File", key="btn_enc"):
      if f_upload is not None and f_pass:
        with st.spinner("Sedang mengenkripsi data biner file..."):
          # Pastikan membaca dari byte awal
          f_upload.seek(0)
          data_mentah = f_upload.read()

          hasil_enkripsi = encrypt_file_chacha(
              file_bytes=data_mentah,
              original_filename=f_upload.name,
              password=f_pass,
          )

          st.success(
              f"File '{f_upload.name}' ({len(data_mentah)} bytes) berhasil dienkripsi!"
          )
          st.download_button(
              label=f"⬇️ Unduh {f_upload.name}.enc",
              data=hasil_enkripsi,
              file_name=f"{f_upload.name}.enc",
              mime="application/octet-stream",
          )
      else:
        st.warning("Silakan unggah file dan tentukan kunci sandi terlebih dahulu.")

  with tab2:
    f_dec_upload = st.file_uploader(
        "Pilih File Terenkripsi (.enc):", type=["enc"], key="uploader_dec"
    )
    f_dec_pass = st.text_input(
        "Kunci Sandi Dekripsi File:", "RahasiaFile123", type="password", key="pass_dec"
    )

    if st.button("Mulai Dekripsi File", key="btn_dec"):
      if f_dec_upload is not None and f_dec_pass:
        try:
          with st.spinner("Mendekripsi file..."):
            f_dec_upload.seek(0)
            data_terenkripsi = f_dec_upload.read()

            data_asli, nama_file_asli = decrypt_file_chacha(
                encrypted_bytes=data_terenkripsi, password=f_dec_pass
            )

            st.success(
                f"Dekripsi Berhasil! File dipulihkan sebagai: **{nama_file_asli}**"
            )
            st.download_button(
                label=f"⬇️ Unduh File Asli ({nama_file_asli})",
                data=data_asli,
                file_name=nama_file_asli,
                mime="application/octet-stream",
            )
        except Exception as e:
          st.error("Gagal mendekripsi: Kunci sandi salah atau file .enc rusak/tidak valid!")
      else:
        st.warning("Unggah file .enc dan masukkan kata sandi yang cocok.")

# ----------------- MODUL 3 -----------------
elif menu == "Steganografi Gambar LSB":
    st.subheader("🖼️ Steganografi Gambar LSB (Least Significant Bit)")
    st.write("Modul untuk menyembunyikan pesan teks atau file gambar rahasia ke dalam piksel gambar lain.")

    tipe_stego = st.radio(
        "Pilih Jenis Data Rahasia yang Ingin Disisipkan / Diekstrak:",
        ["Gambar di dalam Gambar", "Teks di dalam Gambar"],
        horizontal=True
    )

    tab1, tab2 = st.tabs(["🔒 Sisipkan Data (Encode)", "🔓 Ekstrak Data (Decode)"])

    # ==========================
    # PILIHAN: GAMBAR DALAM GAMBAR
    # ==========================
    if tipe_stego == "Gambar di dalam Gambar":
        with tab1:
            st.markdown("#### Sisipkan Gambar Rahasia ke Cover Image")
            cover_file = st.file_uploader("1. Pilih Gambar Penampung / Cover (Wajib PNG):", type=["png"], key="cover_img_upload")
            secret_file = st.file_uploader("2. Pilih Gambar Rahasia yang Akan Disembunyikan (PNG/JPG/BMP):", type=["png", "jpg", "jpeg", "bmp"], key="secret_img_upload")

            if cover_file and secret_file:
                c1, c2 = st.columns(2)
                with c1:
                    st.image(cover_file, caption="Gambar Penampung (Cover)", use_container_width=True)
                with c2:
                    st.image(secret_file, caption="Gambar Rahasia yang Disisipkan", use_container_width=True)

            if st.button("Jalankan Steganografi Gambar", key="btn_hide_img"):
                if cover_file is not None and secret_file is not None:
                    try:
                        with st.spinner("Menyisipkan piksel gambar rahasia ke dalam LSB cover image..."):
                            cover_pil = Image.open(cover_file)
                            secret_bytes = secret_file.read()
                            
                            stego_res = lsb_encode_image(
                                cover_img=cover_pil,
                                secret_img_bytes=secret_bytes,
                                secret_filename=secret_file.name
                            )

                            buf = io.BytesIO()
                            stego_res.save(buf, format="PNG")
                            byte_data = buf.getvalue()

                            st.success("✅ Gambar rahasia berhasil disembunyikan di dalam Cover Image!")
                            st.download_button(
                                label="⬇️ Unduh Stego-Image Hasil (PNG)",
                                data=byte_data,
                                file_name="stego_image_output.png",
                                mime="image/png"
                            )
                    except Exception as e:
                        st.error(f"Gagal menyisipkan gambar: {e}")
                else:
                    st.warning("Harap unggah kedua file gambar terlebih dahulu.")

        with tab2:
            st.markdown("#### Ekstrak Gambar Rahasia dari Stego Image")
            stego_upload = st.file_uploader("Unggah Stego Image (Format PNG):", type=["png"], key="stego_img_extract")

            if st.button("Ekstrak Gambar Rahasia", key="btn_extract_img"):
                if stego_upload is not None:
                    try:
                        with st.spinner("Membaca dan merekonstruksi gambar rahasia..."):
                            stego_pil = Image.open(stego_upload)
                            recovered_bytes, filename = lsb_decode_image(stego_pil)

                            st.success(f"✅ Gambar rahasia berhasil ditemukan: **{filename}**")
                            st.image(recovered_bytes, caption=f"Gambar Rahasia Hasil Ekstraksi: {filename}", use_container_width=True)
                            
                            st.download_button(
                                label=f"⬇️ Unduh File Gambar Rahasia ({filename})",
                                data=recovered_bytes,
                                file_name=filename,
                                mime="application/octet-stream"
                            )
                    except Exception as e:
                        st.error(f"Gagal mengekstrak: {e}")
                else:
                    st.warning("Silakan unggah gambar stego terlebih dahulu.")

    # ==========================
    # PILIHAN: TEKS DALAM GAMBAR
    # ==========================
    else:
        with tab1:
            st.markdown("#### Sisipkan Pesan Teks ke Gambar")
            img_in = st.file_uploader("Pilih Gambar Wadah (PNG):", type=["png"], key="steg_upload_enc")
            secret_msg = st.text_area("Pesan Rahasia:", key="steg_text_in")

            if st.button("Sisipkan Teks ke Gambar", key="btn_steg_txt_enc"):
                if img_in and secret_msg:
                    try:
                        pil_img = Image.open(img_in)
                        stego_img = lsb_encode(pil_img, secret_msg)
                        buf = io.BytesIO()
                        stego_img.save(buf, format="PNG")
                        st.success("✅ Pesan teks berhasil disisipkan!")
                        st.download_button(
                            label="⬇️ Unduh Gambar (stego_text_output.png)",
                            data=buf.getvalue(),
                            file_name="stego_text_output.png",
                            mime="image/png"
                        )
                    except Exception as e:
                        st.error(f"Terjadi kesalahan: {e}")
                else:
                    st.warning("Lengkapi gambar dan pesan teks!")

        with tab2:
            st.markdown("#### Ekstrak Pesan Teks dari Gambar")
            steg_img_in = st.file_uploader("Unggah Gambar Berisi Teks (PNG):", type=["png"], key="steg_upload_txt_dec")
            if st.button("Ekstrak Teks Rahasia", key="btn_steg_txt_dec"):
                if steg_img_in:
                    extracted = lsb_decode(Image.open(steg_img_in))
                    st.success("Isi Pesan Tersembunyi:")
                    st.info(extracted)
                else:
                    st.warning("Unggah gambar PNG terlebih dahulu.")

# ------------- MODUL 4 -------------
elif menu == "Database Sensitif Terenkripsi":
    st.subheader("🗄️ Basis Data Terenkripsi (Field-Level Encryption)")
    
    import mysql.connector
    import hashlib
    import base64
    from cryptography.fernet import Fernet

    # --- FUNGSI KRIPTOGRAFI UNTUK BASIS DATA (AES via Fernet) ---
    def get_fernet_cipher(password: str):
        # Derivasi kunci 32-byte dari password menggunakan SHA-256
        key = hashlib.sha256(password.encode()).digest()
        return Fernet(base64.urlsafe_b64encode(key))

    def db_encrypt_payload(plain_text: str, secret_key: str) -> str:
        cipher = get_fernet_cipher(secret_key)
        return cipher.encrypt(plain_text.encode("utf-8")).decode("utf-8")

    def db_decrypt_payload(cipher_text: str, secret_key: str) -> str:
        cipher = get_fernet_cipher(secret_key)
        return cipher.decrypt(cipher_text.encode("utf-8")).decode("utf-8")

    # --- INISIALISASI KONEKSI MYSQL KE XAMPP ---
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",          # Kosongkan jika default XAMPP
            database="db_kripto"
        )
        c = conn.cursor()
        
        # Buat tabel otomatis jika belum ada di database
        c.execute("""
            CREATE TABLE IF NOT EXISTS confidential_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                label VARCHAR(255) NOT NULL,
                encrypted_payload LONGTEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception as e:
        st.error(f"Gagal menghubungkan ke MySQL XAMPP: {e}")
        st.info("Pastikan modul MySQL di XAMPP berstatus Running dan database 'db_kripto' sudah dibuat.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Tambah Catatan Penting Baru**")
        label = st.text_input("Label / Subjek:")
        pesan_penting = st.text_area("Data Rahasia (Password/PIN/Catatan):")
        db_pass = st.text_input("Kunci Enkripsi DB:", "VaultKey2026")
        
        if st.button("Simpan ke Basis Data"):
            if label and pesan_penting:
                payload_enc = db_encrypt_payload(pesan_penting, db_pass)
                c.execute(
                    "INSERT INTO confidential_data (label, encrypted_payload) VALUES (%s, %s)",
                    (label, payload_enc)
                )
                conn.commit()
                st.success("✅ Data berhasil dienkripsi dan disimpan di MySQL (XAMPP).")
                st.rerun()
            else:
                st.warning("Label dan Data Rahasia wajib diisi!")

    with col2:
        st.write("**Buka / Dekripsi Data Tersimpan**")
        c.execute("SELECT id, label, encrypted_payload FROM confidential_data ORDER BY id DESC")
        rows = c.fetchall()
        
        if rows:
            record_id = st.selectbox(
                "Pilih Record ID:", [f"{r[0]} - {r[1]}" for r in rows]
            )
            key_unlock = st.text_input("Kunci Dekripsi Vault:", "VaultKey2026")
            
            if st.button("Buka Data"):
                target_id = int(record_id.split(" - ")[0])
                raw_token = [r[2] for r in rows if r[0] == target_id][0]
                try:
                    hasil_buka = db_decrypt_payload(raw_token, key_unlock)
                    st.write("**Isi Asli:**")
                    st.code(hasil_buka)
                except Exception:
                    st.error("Kunci pembuka database salah atau data rusak!")
        else:
            st.info("Database masih kosong.")
            
    c.close()
    conn.close()

# ----------------- MODUL 5 -----------------
elif menu == "Ledger Blockchain Aset":
    st.subheader("⛓️ Pengamanan Aset Digital (Blockchain Sederhana)")
    st.write("Setiap pencatatan aset dirangkai menggunakan Hash SHA-256 dan terhubung dengan Hash blok sebelumnya.")

    # Form Pendaftaran Aset
    with st.form("form_aset", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            nama_aset = st.text_input("Nama Aset (Misal: Hak Cipta, Ijazah, Dokumen):")
            pemilik = st.text_input("Nama Pemilik:")
        with col_b:
            nilai = st.text_input("Nilai / Keterangan Identitas Aset:")
            
        submit = st.form_submit_button("➕ Daftarkan Aset ke Rantai Blok", use_container_width=True)

        if submit:
            if nama_aset and pemilik:
                block_data = {
                    "nama_aset": nama_aset,
                    "pemilik": pemilik,
                    "keterangan": nilai
                }
                baru = add_block_to_chain(block_data)
                st.success(f"✅ Blok #{baru.index} berhasil ditambang dan dirangkai ke dalam Ledger!")
                st.rerun()
            else:
                st.warning("Harap lengkapi nama aset dan pemilik.")

    st.markdown("---")
    
    # Header & Tombol Cek Validitas
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.write("### 📜 Visualisasi Rantai Blok (Ledger)")
    with col_t2:
        cek_valid = st.button("🔍 Verifikasi Keaslian Rantai", use_container_width=True)

    rantai = load_blockchain()

    # Fitur Cek Integritas Kriptografis Rantai
    if cek_valid:
        is_chain_valid = True
        for i in range(1, len(rantai)):
            b_prev = rantai[i - 1]
            b_curr = rantai[i]
            
            # Verifikasi keterhubungan hash
            if b_curr["previous_hash"] != b_prev["hash"]:
                is_chain_valid = False
                st.error(f"🚨 INTEGRITAS RUSAK! Blok #{b_curr['index']} tidak cocok dengan Hash Blok #{b_prev['index']}")
                break
        
        if is_chain_valid:
            st.success("✅ Seluruh Rantai Blok Valid! Tidak ada data yang dimanipulasi secara ilegal.")

    # Menampilkan Blok dalam Bentuk Kartu Rantai Terhubung
    for i, b in enumerate(rantai):
        waktu = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(b['timestamp']))
        
        with st.container(border=True):
            col_b1, col_b2 = st.columns([1, 3])
            
            with col_b1:
                if b['index'] == 0:
                    st.markdown("### 🧱 Blok #0")
                    st.caption("*(Genesis Block)*")
                else:
                    st.markdown(f"### 📦 Blok #{b['index']}")
                st.write(f"⏱️ **Waktu:** `{waktu}`")
            
            with col_b2:
                # Tampilkan Data Aset
                st.write(f"📄 **Data Aset:** `{json.dumps(b['data'], ensure_ascii=False)}`")
                
                # Tampilkan Hash Kriptografi
                st.markdown(f"⬅️ **Previous Hash:** `{b['previous_hash']}`")
                st.markdown(f"🔑 **Current Hash:** `{b['hash']}`")
        
        # Gambar simbol rantai penghubung antar blok
        if i < len(rantai) - 1:
            st.markdown(
                "<div style='text-align: center; font-size: 24px; margin: -5px 0;'>⬇️ ⛓️ <i>(Hash Terhubung)</i> ⬇️</div>", 
                unsafe_allow_html=True
            )