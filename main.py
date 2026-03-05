import threading
import http.server
import socketserver
import os
from app.bot import run_bot

# Hàm để chạy Web Server ảo
def run_dummy_server():
    PORT = int(os.environ.get("PORT", 10000))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Dummy server đang chạy tại port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Chạy Web Server ở một luồng (thread) riêng
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # Chạy Bot Telegram chính
    run_bot()
