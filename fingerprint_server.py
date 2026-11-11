import http.server
import socketserver

PORT = 8502

# URL tujuan saat dialihkan kembali ke Streamlit lengkap dengan Token Verifikasi
STREAMLIT_RETURN_URL = "http://192.168.18.91:8501/?fp_auth=VERIFIED_SUCCESS"

HTML_PAGE = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autentikasi Sidik Jari</title>
    <style>
        body {{
            background-color: #0e1117;
            color: #ffffff;
            font-family: sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }}
        .card {{
            background-color: #262730;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            max-width: 90%;
            width: 340px;
        }}
        button {{
            background-color: #00c853;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
        }}
        #backBtn {{
            background-color: #29b6f6;
            display: none;
            margin-top: 15px;
            text-decoration: none;
            padding: 14px 20px;
            border-radius: 8px;
            font-weight: bold;
            color: white;
            box-sizing: border-box;
        }}
        #status {{
            margin-top: 15px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h2>🔒 Fingerprint Auth</h2>
        <p>Sentuh tombol di bawah untuk memicu sensor sidik jari HP:</p>
        <button id="scanBtn">👆 Pindai Sidik Jari</button>
        <p id="status"></p>
        <a id="backBtn" href="{STREAMLIT_RETURN_URL}">🔓 Masuk ke Dashboard Sekarang</a>
    </div>

    <script>
    document.getElementById('scanBtn').addEventListener('click', async () => {{
        const status = document.getElementById('status');
        const backBtn = document.getElementById('backBtn');
        const scanBtn = document.getElementById('scanBtn');
        
        status.style.color = '#3399ff';
        status.innerText = "Membuka sensor biometrik...";

        try {{
            const challenge = new Uint8Array(32);
            window.crypto.getRandomValues(challenge);
            const userId = new Uint8Array(16);
            window.crypto.getRandomValues(userId);

            const credential = await navigator.credentials.create({{
                publicKey: {{
                    challenge: challenge,
                    rp: {{ 
                        name: "Kripto App", 
                        id: window.location.hostname 
                    }},
                    user: {{ 
                        id: userId, 
                        name: "pengguna", 
                        displayName: "Pemilik Perangkat" 
                    }},
                    pubKeyCredParams: [
                        {{ type: "public-key", alg: -7 }},
                        {{ type: "public-key", alg: -257 }}
                    ],
                    authenticatorSelection: {{ 
                        authenticatorAttachment: "platform", 
                        userVerification: "required" 
                    }},
                    timeout: 60000
                }}
            }});

            if (credential) {{
                status.style.color = '#00e676';
                status.innerHTML = "✅ <b>Sidik jari cocok!</b><br>Mengalihkan ke Dashboard...";
                scanBtn.style.display = "none";
                backBtn.style.display = "block";

                // Otomatis arahkan kembali ke Streamlit membawa token valid
                setTimeout(() => {{
                    window.location.href = "{STREAMLIT_RETURN_URL}";
                }}, 1000);
            }}
        }} catch (err) {{
            status.style.color = '#ff5252';
            status.innerText = "Gagal: " + err.message;
        }}
    }});
    </script>
</body>
</html>
"""

class SimpleAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

def run():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), SimpleAuthHandler) as httpd:
        print(f"[*] Auth Server aktif di port {PORT}...")
        httpd.serve_forever()

if __name__ == "__main__":
    run()