import wmi

def scan_semua_usb():
    c = wmi.WMI()
    print("=== MEMINDAI SELURUH PERANGKAT USB & HID ===\n")
    ditemukan = False

    # Memindai seluruh entitas PnP
    for device in c.Win32_PnPEntity():
        device_id = str(device.DeviceID)
        name = str(device.Name)

        # Cek apakah perangkat terhubung via USB atau HID
        if "VID_" in device_id and ("USB" in device_id or "HID" in device_id):
            print(f"Nama Perangkat : {name}")
            print(f"Device ID      : {device_id}")
            print(f"Status         : {device.Status}")
            print("-" * 60)
            ditemukan = True

    if not ditemukan:
        print("[!] Tidak ada perangkat USB/HID dengan pola VID/PID yang terdeteksi.")

if __name__ == "__main__":
    scan_semua_usb()