import aiohttp
import os
import json
import re
import asyncio
from app.config import HEADERS

# --- Lấy thông tin từ ENV Render ---
GIST_URL = os.environ.get("GIST_URL")
EMAIL = os.environ.get("EMAIL_ACC")
PASSWORD = os.environ.get("PASSWORD_ACC")

async def get_credentials_from_gist():
    """Lấy mã fetch_token và app_transaction từ link Gist RAW"""
    if not GIST_URL:
        return None, None
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(GIST_URL, timeout=10) as res:
                if res.status == 200:
                    data = await res.json()
                    return data.get("fetch_token"), data.get("app_transaction")
        except Exception as e:
            print(f"Lỗi đọc Gist: {e}")
            return None, None

async def login_admin():
    """Đăng nhập bằng Email/Pass của bạn để lấy Session Token chính chủ"""
    if not EMAIL or not PASSWORD:
        return None
        
    url = "https://api.locket.cam/v1/auth/login"
    payload = {"email": EMAIL, "password": PASSWORD}
    
    # Giả lập Header của App Locket thật
    login_headers = {
        "User-Agent": "Locket/1.51.0 (com.locket.Locket; build:1; iOS 17.0.0) Alamofire/5.7.1",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=login_headers, timeout=15) as res:
                if res.status == 200:
                    data = await res.json()
                    return data.get("session_token")
                return None
        except Exception:
            return None

async def resolve_uid(input_data):
    """Phân giải UID từ Username hoặc Link. Hỗ trợ xử lý lỗi quét HTML."""
    if not input_data:
        return None
        
    # 1. Nếu người dùng nhập thẳng UID 28 ký tự
    clean_input = input_data.strip()
    if len(clean_input) == 28 and re.match(r'^[A-Za-z0-9]+$', clean_input):
        return clean_input

    # 2. Xử lý lấy username từ link (locket.cam/@abc hoặc locket.cam/abc)
    username = clean_input.split('/')[-1].replace('@', '').split('?')[0]
    url = f"https://locket.cam/{username}"
    
    # Dùng User-Agent của Safari iPhone để Locket nhả HTML đầy đủ
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as res:
                if res.status != 200:
                    return None
                
                html = await res.text()
                
                # Tìm mã invite (UID) trong các thẻ meta hoặc script link
                # Pattern 1: Link invite chuẩn
                match = re.search(r'/invites/([A-Za-z0-9]{28})', html)
                if match:
                    return match.group(1)
                
                # Pattern 2: Deep link trong script
                match_deep = re.search(r'auth_user_id=([A-Za-z0-9]{28})', html)
                if match_deep:
                    return match_deep.group(1)
                    
                return None
        except:
            return None

async def inject_gold(target_uid, token_config=None, log_callback=None):
    """Quy trình kích hoạt Gold chính: Login -> Lấy Token Gist -> Bơm RevenueCat"""
    def log(msg): 
        if log_callback: log_callback(msg)

    # 1. Lấy mã Gold từ Gist (Đọc từ ENV GIST_URL)
    fetch, trans = await get_credentials_from_gist()
    
    # 2. Lấy Session của tài khoản Admin (Đọc từ ENV EMAIL/PASS)
    admin_token = await login_admin()

    if not fetch or not admin_token:
        error_msg = "Lỗi: Không lấy được mã từ Gist hoặc Login thất bại."
        log(f"🔴 {error_msg}")
        return False, error_msg

    # 3. Gửi Payload tới RevenueCat
    url = "https://api.revenuecat.com/v1/receipts"
    
    # Header quan trọng nhất: Phải có Session Token của bạn (Bearer)
    headers = HEADERS.copy()
    headers['Authorization'] = f'Bearer {admin_token}'
    
    body = {
        "product_id": "locket_199_1m",
        "fetch_token": fetch,
        "app_transaction": trans,
        "app_user_id": target_uid, # UID của người cần kích hoạt
        "is_restore": True,
        "store_country": "VNM"
    }

    async with aiohttp.ClientSession() as session:
        try:
            log(f"[*] Đang thực hiện Exploit cho Target: {target_uid}")
            async with session.post(url, headers=headers, json=body, timeout=20) as res:
                if res.status == 200:
                    log(f"✅ Kích hoạt thành công trên Server RevenueCat!")
                    return True, "SUCCESS"
                
                resp_text = await res.text()
                log(f"🔴 RevenueCat từ chối: {res.status}")
                return False, f"Error {res.status}: {resp_text[:50]}"
        except Exception as e:
            log(f"🔴 Lỗi kết nối: {str(e)}")
            return False, str(e)
