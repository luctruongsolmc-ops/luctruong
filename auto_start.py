# -*- coding: utf-8 -*-
"""
auto_start.py - Khởi động toàn bộ hệ thống tự động
========================================================
Script này sẽ:
  1. Khởi động Flask server (port 5000)
  2. Khởi động Cloudflare Tunnel
  3. Đọc URL public mới được tạo
  4. Tự động cập nhật Facebook Webhook subscription
  5. Hiển thị dashboard trạng thái

Chạy: python auto_start.py
"""

import subprocess
import threading
import io
import time
import re
import os
import sys
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Fix encoding Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT_DIR       = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT_DIR, '.env'))
FLASK_SCRIPT   = os.path.join(ROOT_DIR, "src", "main.py")
CLOUDFLARED    = r"C:\Users\LUC\cloudflared.exe"
PORT           = int(os.getenv("PORT", 5000))

PAGE_TOKEN     = os.getenv("MESSENGER_PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN   = os.getenv("MESSENGER_VERIFY_TOKEN", "thoitranghoa_webhook_2024")

# Cần điền vào .env để tự động update webhook
APP_ID         = os.getenv("FACEBOOK_APP_ID", "")
APP_SECRET     = os.getenv("FACEBOOK_APP_SECRET", "")

# ─── GLOBAL STATE ────────────────────────────────────────────────────────────

tunnel_url = None
flask_ready = False

def log(msg, level="INFO"):
    color = {"INFO": "", "WARN": "", "ERROR": "", "STEP": ""}.get(level, "")
    reset = "\033[0m"
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] [{level}] {msg}{reset}")

# ─── STEP 1: Khởi động Flask ─────────────────────────────────────────────────

def start_flask():
    global flask_ready
    log("Đang khởi động Flask server...", "STEP")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(ROOT_DIR, "src")
    
    proc = subprocess.Popen(
        [sys.executable, FLASK_SCRIPT],
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    
    # Đợi Flask sẵn sàng
    for line in proc.stdout:
        line = line.strip()
        if "Running on" in line:
            log(f"Flask ready: {line}", "INFO")
            flask_ready = True
        if "Error" in line or "error" in line:
            log(f"Flask: {line}", "WARN")
    
    proc.wait()

# ─── STEP 2: Khởi động Cloudflare Tunnel ─────────────────────────────────────

def start_tunnel():
    global tunnel_url
    log("Đang khởi động Cloudflare Tunnel...", "STEP")
    
    # Doi Flask thuc su san sang nhan request
    import urllib.request
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"http://localhost:{PORT}/health", timeout=1) as resp:
                if resp.status == 200:
                    log("Flask da san sang nhan connections [OK]", "INFO")
                    break
        except Exception:
            pass
        time.sleep(0.5)
    
    time.sleep(1)
    
    proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    
    for line in proc.stdout:
        line = line.strip()
        # Tìm URL trycloudflare.com
        match = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            log(f"[TUNNEL URL] {tunnel_url}", "STEP")
            # Kích hoạt cập nhật Facebook
            threading.Thread(target=update_facebook_webhook, daemon=True).start()
        
        if "Registered tunnel connection" in line:
            log("Tunnel ket noi on dinh [OK]", "INFO")

    proc.wait()

# ─── STEP 3: Cập nhật Facebook Webhook ───────────────────────────────────────

def update_facebook_webhook():
    global tunnel_url
    if not tunnel_url:
        return
    
    # Kiểm tra xem hệ thống có đang sử dụng Cloud Render vĩnh viễn không
    if os.getenv("USE_LOCAL_WEBHOOK", "false").lower() != "true":
        log("Hệ thống đang chạy Cloud 24/7 trên Render (https://shop-do-nam-dep.onrender.com). Bỏ qua ghi đè Webhook!", "INFO")
        return

    webhook_url = f"{tunnel_url}/webhook/messenger"
    log(f"Dang cap nhat Facebook Webhook -> {webhook_url}", "STEP")
    
    # Lưu URL hiện tại ra file để tham chiếu
    url_file = os.path.join(ROOT_DIR, "logs", "current_tunnel_url.txt")
    os.makedirs(os.path.join(ROOT_DIR, "logs"), exist_ok=True)
    with open(url_file, "w", encoding="utf-8") as f:
        f.write(f"Cap nhat luc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Tunnel URL:   {tunnel_url}\n")
        f.write(f"Webhook URL:  {webhook_url}\n")
        f.write(f"Verify Token: {VERIFY_TOKEN}\n")
    
    # Nếu có App credentials → tự động cập nhật qua API
    if APP_ID and APP_SECRET:
        _auto_update_via_api(webhook_url)
    else:
        # Không có App credentials → hướng dẫn thủ công
        _print_manual_instructions(webhook_url)

def _auto_update_via_api(webhook_url):
    """Tu dong cap nhat webhook qua Facebook Graph API voi retry"""
    try:
        # Lay App Access Token
        resp = requests.get(
            "https://graph.facebook.com/oauth/access_token",
            params={
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "grant_type": "client_credentials"
            },
            timeout=10
        )
        resp.raise_for_status()
        app_token = resp.json().get("access_token")
        
        log("Doi tunnel on dinh 5s truoc khi dang ky Facebook webhook...", "INFO")
        time.sleep(5)
        
        # Doi tunnel on dinh va retry toi da 6 lan
        for attempt in range(1, 7):
            try:
                resp2 = requests.post(
                    f"https://graph.facebook.com/v18.0/{APP_ID}/subscriptions",
                    data={
                        "access_token": app_token,
                        "object": "page",
                        "callback_url": webhook_url,
                        "verify_token": VERIFY_TOKEN,
                        "fields": "messages,messaging_postbacks",
                        "include_values": "true"
                    },
                    timeout=15
                )
                result = resp2.json()
                if result.get("success"):
                    log(f"[OK] Facebook Webhook da tu dong cap nhat THANH CONG (lan {attempt})!", "INFO")
                    log(f"    Webhook URL moi: {webhook_url}", "INFO")
                    return
                else:
                    log(f"[WARN] Thu lan {attempt} chua thanh cong: {resp2.text}", "WARN")
            except Exception as ex:
                log(f"[WARN] Thu lan {attempt} loi: {ex}", "WARN")
            time.sleep(4)

        _print_manual_instructions(webhook_url)
            
    except Exception as e:
        log(f"Khong the tu dong cap nhat: {e}", "WARN")
        _print_manual_instructions(webhook_url)

def _print_manual_instructions(webhook_url):
    """In hướng dẫn cập nhật thủ công"""
    print()
    print("=" * 65)
    print("  [!] CAN CAP NHAT FACEBOOK WEBHOOK (copy va dan)")
    print("=" * 65)
    print(f"  URL:          {webhook_url}")
    print(f"  Verify Token: {VERIFY_TOKEN}")
    print()
    print("  >> Vao: developers.facebook.com -> App -> Messenger")
    print("         -> Webhooks -> Edit -> dan URL tren vao")
    print("=" * 65)
    print()

# ─── DASHBOARD ───────────────────────────────────────────────────────────────

def print_banner():
    print()
    print("=" * 65)
    print("  AUTO REPLY SYSTEM - Thoi Trang Hoa")
    print("  Dang khoi dong tat ca dich vu...")
    print("=" * 65)
    print()

# ─── MAIN ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print_banner()
    
    # Kiểm tra cloudflared tồn tại
    if not os.path.exists(CLOUDFLARED):
        log(f"Khong tim thay cloudflared tai: {CLOUDFLARED}", "ERROR")
        sys.exit(1)
    
    # Chạy Flask và Tunnel song song
    flask_thread  = threading.Thread(target=start_flask,  daemon=True, name="Flask")
    tunnel_thread = threading.Thread(target=start_tunnel, daemon=True, name="Tunnel")
    
    flask_thread.start()
    time.sleep(1)  # nhường Flask khởi động trước
    tunnel_thread.start()
    
    log("Dang cho cac dich vu san sang...", "INFO")
    
    try:
        # Chạy mãi cho đến khi Ctrl+C
        while True:
            time.sleep(60)
            if tunnel_url:
                log(f"[OK] He thong hoat dong binh thuong | URL: {tunnel_url}", "INFO")
    except KeyboardInterrupt:
        log("Dang tat he thong...", "WARN")
        sys.exit(0)
