import os
import threading
import http.server
import socketserver
from app.bot import run_bot

def start_dummy_server():
    """Mở cổng HTTP để vượt qua kiểm tra Port của Render"""
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"✅ Dummy server started on port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Chạy server giả lập trong luồng riêng
    threading.Thread(target=start_dummy_server, daemon=True).start()
    # Khởi chạy bot chính
    run_bot()
