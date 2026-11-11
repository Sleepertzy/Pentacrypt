import base64
import hashlib
import os
import urllib.request
import cv2
import numpy as np
from cryptography.fernet import Fernet

TARGET_DONGLE_ID = "VID_062A&PID_5918"


def generate_key_from_dongle(hardware_id: str) -> bytes:
  h = hashlib.sha256(hardware_id.encode('utf-8'))
  return base64.urlsafe_b64encode(h.digest())


def create_dongle_license():
  key = generate_key_from_dongle(TARGET_DONGLE_ID)
  fernet = Fernet(key)
  payload = b"STATUS_VALID:DONGLE_MOUSE_GAMEN_AUTHENTICATED"
  enc_data = fernet.encrypt(payload)
  with open('app_license.enc', 'wb') as f:
    f.write(enc_data)
  print("[+] File lisensi 'app_license.enc' berhasil dibuat!")


def ensure_cascade_model():
  xml_filename = "haarcascade_frontalface_default.xml"
  if not os.path.exists(xml_filename):
    print("[*] Mengunduh model Haar Cascade...")
    url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
    urllib.request.urlretrieve(url, xml_filename)
  return xml_filename


def train_face_model():
  xml_path = ensure_cascade_model()
  face_cascade = cv2.CascadeClassifier(xml_path)

  cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
  if not cap.isOpened():
    cap = cv2.VideoCapture(0)

  print("[*] Kamera siap. Silakan lihat ke kamera.")
  print(
      "[*] Sistem akan merekam 20 sampel wajah Anda. Gerakkan kepala sedikit"
      " perlahan..."
  )

  face_samples = []
  ids = []
  count = 0

  while True:
    ret, frame = cap.read()
    if not ret:
      break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(80, 80))

    for x, y, w, h in faces:
      cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
      count += 1
      face_roi = cv2.resize(gray[y : y + h, x : x + w], (200, 200))
      face_samples.append(face_roi)
      ids.append(1)  # ID 1 untuk pemilik asli

      cv2.putText(
          frame,
          f"Sampel: {count}/20",
          (x, y - 10),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.6,
          (0, 255, 0),
          2,
      )

    cv2.imshow("Merekam Biometrik Wajah...", frame)
    cv2.waitKey(100)

    if count >= 20:
      break

  cap.release()
  cv2.destroyAllWindows()

  # Latih model pengenal wajah LBPH
  recognizer = cv2.face.LBPHFaceRecognizer_create()
  recognizer.train(face_samples, np.array(ids))
  recognizer.write("face_model.yml")
  print(
      "[+] Model biometrik wajah berhasil dilatih dan disimpan ke"
      " 'face_model.yml'!"
  )


if __name__ == "__main__":
  create_dongle_license()
  train_face_model()