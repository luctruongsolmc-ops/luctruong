"""
Auto Reply System - Server chính
Nhận webhook từ Messenger / Zalo / TikTok
Phân tích và tạo phản hồi tự động
Hỗ trợ chuyển đổi sang chế độ Chat với người thật (Human Takeover)

Cài đặt: pip install flask requests python-dotenv
Chạy:    python src/main.py
"""

from flask import Flask, request, jsonify
from dotenv import load_dotenv
import json
import os
import logging
from datetime import datetime

# Tự động đọc file .env
load_dotenv()

from classifier import IntentClassifier
from reply_generator import ReplyGenerator
from session_manager import SessionManager

# Cấu hình logging
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(LOG_DIR, f'app-{datetime.now().strftime("%Y-%m-%d")}.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
classifier = IntentClassifier()
generator = ReplyGenerator()
session_manager = SessionManager()


@app.route('/health', methods=['GET'])
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok", 
        "service": "auto-reply-system", 
        "shop": "Shop đồ Nam",
        "human_sessions_count": len([s for s in session_manager.sessions.values() if s.get("is_human_mode")])
    }), 200


# ─── MESSENGER WEBHOOK ──────────────────────────────────────────────────────

@app.route('/webhook/messenger', methods=['GET', 'POST'])
def messenger_webhook():
    """Facebook Messenger Webhook"""
    
    # Xác thực webhook khi setup lần đầu
    if request.method == 'GET':
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if token == os.getenv('MESSENGER_VERIFY_TOKEN'):
            logger.info("✅ Messenger webhook verified!")
            return challenge, 200
        return "Forbidden", 403

    # Xử lý tin nhắn đến
    data = request.json
    logger.info(f"📨 Messenger: {json.dumps(data, ensure_ascii=False)[:200]}")
    
    try:
        for entry in data.get('entry', []):
            for event in entry.get('messaging', []):
                if 'message' in event:
                    msg_obj = event['message']
                    
                    # 1. Kiểm tra nếu Admin Page gửi tin nhắn (is_echo: true) -> Bật Human Takeover
                    if msg_obj.get('is_echo'):
                        recipient_id = event.get('recipient', {}).get('id')
                        if recipient_id:
                            logger.info(f"👨‍💼 Admin đã nhắn tin cho khách {recipient_id} -> Chuyển sang cuộc trò chuyện trực tiếp (TẮT BOT)")
                            session_manager.set_human_mode(
                                sender_id=recipient_id,
                                enabled=True,
                                reason="Admin nhắn tin từ Page Inbox",
                                platform="messenger"
                            )
                        continue
                    
                    sender_id = event['sender']['id']
                    text = msg_obj.get('text', '')
                    
                    if text:
                        _process_and_reply(
                            platform='messenger',
                            sender_id=sender_id,
                            message=text,
                            raw_data=event
                        )
    except Exception as e:
        logger.error(f"❌ Messenger error: {e}")
    
    return jsonify({"status": "ok"}), 200


# ─── ZALO WEBHOOK ───────────────────────────────────────────────────────────

@app.route('/webhook/zalo', methods=['POST'])
def zalo_webhook():
    """Zalo Official Account Webhook"""
    
    data = request.json
    logger.info(f"📨 Zalo: {json.dumps(data, ensure_ascii=False)[:200]}")
    
    try:
        event_name = data.get('event_name', '')
        
        # Chỉ xử lý tin nhắn người dùng gửi
        if event_name == 'user_send_text':
            sender_id = data['sender']['id']
            text = data['message']['text']
            
            _process_and_reply(
                platform='zalo',
                sender_id=sender_id,
                message=text,
                raw_data=data
            )
            
    except Exception as e:
        logger.error(f"❌ Zalo error: {e}")
    
    return jsonify({"error": 0}), 200


# ─── TIKTOK WEBHOOK ─────────────────────────────────────────────────────────

@app.route('/webhook/tiktok', methods=['POST'])
def tiktok_webhook():
    """TikTok Shop / Comment Webhook"""
    
    data = request.json
    logger.info(f"📨 TikTok: {json.dumps(data, ensure_ascii=False)[:200]}")
    
    try:
        event_type = data.get('type', '')
        
        # Comment trên TikTok
        if event_type == 'comment':
            user_id = data['data']['user_id']
            username = data['data'].get('username', 'bạn')
            text = data['data']['content']
            
            _process_and_reply(
                platform='tiktok',
                sender_id=user_id,
                message=text,
                raw_data=data,
                username=username
            )
            
    except Exception as e:
        logger.error(f"❌ TikTok error: {e}")
    
    return jsonify({"code": 0, "message": "success"}), 200


# ─── MANUAL TESTING & SESSION ENDPOINTS ───────────────────────────────────────

@app.route('/test', methods=['POST'])
def test_reply():
    """
    Test endpoint - gửi tin nhắn thủ công để test
    
    POST /test
    {
        "platform": "messenger",
        "message": "shop ơi cái này giá bao nhiêu vậy?",
        "sender_id": "test_user_123"
    }
    """
    data = request.json
    platform = data.get('platform', 'messenger')
    message = data.get('message', '')
    sender_id = data.get('sender_id', 'test_user')
    
    result = _process_message(platform, sender_id, message)
    return jsonify(result), 200


@app.route('/sessions', methods=['GET'])
def get_sessions():
    """Xem danh sách các phiên đang ở chế độ Human Takeover"""
    return jsonify(session_manager.sessions), 200


@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Xem danh sách các cảnh báo cần xử lý gấp (Human Takeover, Khiếu nại, Đổi trả)"""
    alert_file = os.path.join(LOG_DIR, 'alerts', 'alerts.jsonl')
    alerts = []
    if os.path.exists(alert_file):
        with open(alert_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        alerts.append(json.loads(line))
                    except Exception:
                        pass
    return jsonify({
        "total_alerts": len(alerts),
        "alerts": list(reversed(alerts))  # Mới nhất lên đầu
    }), 200


@app.route('/sessions/<sender_id>/reset', methods=['POST'])
def reset_session(sender_id):
    """Bật lại bot tự động cho khách hàng"""
    session_manager.reset_bot_mode(sender_id)
    return jsonify({"status": "ok", "message": f"Da bat lai bot cho {sender_id}"}), 200


# ─── CORE PROCESSING ────────────────────────────────────────────────────────

def _process_message(platform: str, sender_id: str, message: str, **kwargs) -> dict:
    """Phân tích tin nhắn và tạo phản hồi (có kiểm tra trạng thái Human Takeover)"""
    
    # 1. Phân loại ý định
    intent = classifier.classify(message)
    
    # 2. Kiểm tra nếu khách yêu cầu bật lại bot
    if intent['type'] == 'BOT_RESUME':
        logger.info(f"🤖 Khách {sender_id} yêu cầu bật lại Bot tự động")
        session_manager.reset_bot_mode(sender_id)
    
    # 3. Kiểm tra xem khách hàng có đang trong chế độ chat với người thật không
    if session_manager.is_human_mode(sender_id):
        logger.info(f"👨‍💼 [Human Mode - Bot tắt] Khách {sender_id}: {message}")
        _save_to_log(
            platform, 
            sender_id, 
            message, 
            {"type": "HUMAN_TAKEOVER_ACTIVE", "confidence": 1.0}, 
            {"reply": None, "escalate": False}
        )
        return {
            "platform": platform,
            "intent": "HUMAN_TAKEOVER_ACTIVE",
            "priority": "HIGH",
            "reply": None,  # Không gửi phản hồi tự động
            "is_human_mode": True
        }

    logger.info(f"🧠 Intent: {intent['type']} (confidence: {intent['confidence']:.2f})")
    
    # 4. Tạo phản hồi
    reply = generator.generate(
        message=message,
        intent=intent,
        platform=platform,
        **kwargs
    )
    
    # 5. Nếu khách yêu cầu HUMAN_HANDOVER ("Chat với người bán")
    if intent['type'] == 'HUMAN_HANDOVER':
        logger.warning(f"🚨 [HANDOVER] Khách {sender_id} yêu cầu gặp người bán -> Kích hoạt Human Takeover")
        session_manager.set_human_mode(
            sender_id=sender_id,
            enabled=True,
            reason="Khách yêu cầu chat với người bán",
            platform=platform
        )
        _send_alert(platform, sender_id, message, "[CẦN XỬ LÝ NGAY] Khách yêu cầu chat với người bán / nhân viên")
    elif reply.get('escalate'):
        _send_alert(platform, sender_id, message, reply.get('escalate_reason'))
    
    # 6. Lưu log
    _save_to_log(platform, sender_id, message, intent, reply)
    
    return reply


def _process_and_reply(platform: str, sender_id: str, message: str, raw_data: dict, **kwargs):
    """Xử lý và gửi phản hồi thực tế qua platform API"""
    result = _process_message(platform, sender_id, message, **kwargs)
    reply_text = result.get('reply')
    
    # Nếu reply_text là None (đang ở Human Takeover Mode) thì không gửi tin nhắn tự động
    if not reply_text:
        logger.info(f"🔇 [Bot không gửi tin] Đang trong cuộc trò chuyện 1-1 với Admin cho khách {sender_id}")
        return

    # Import platform-specific sender
    if platform == 'messenger':
        from platforms.messenger import send_message
    elif platform == 'zalo':
        from platforms.zalo import send_message
    elif platform == 'tiktok':
        from platforms.tiktok import send_message
    
    send_message(sender_id, reply_text)


def _save_to_log(platform, sender_id, message, intent, reply):
    """Lưu mọi cuộc hội thoại vào file log JSON"""
    os.makedirs('logs/conversations', exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform,
        "sender_id": sender_id,
        "message": message,
        "intent": intent['type'],
        "confidence": intent['confidence'],
        "reply": reply.get('reply'),
        "escalated": reply.get('escalate', False)
    }
    
    log_file = f"logs/conversations/{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


def _send_alert(platform, sender_id, message, reason):
    """Gửi cảnh báo khi cần xử lý thủ công hoặc bàn giao cho người bán"""
    alert = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform,
        "sender_id": sender_id,
        "message": message,
        "reason": reason
    }
    
    os.makedirs('logs/alerts', exist_ok=True)
    with open('logs/alerts/alerts.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(alert, ensure_ascii=False) + '\n')
    
    logger.warning(f"🚨 ALERT [{platform}] {reason}: {message[:100]}")

    # 1. Gửi thông báo đến Admin Messenger cá nhân (nếu cấu hình ADMIN_MESSENGER_PSID trong .env)
    admin_psid = os.getenv("ADMIN_MESSENGER_PSID", "")
    if admin_psid and platform == "messenger":
        try:
            from platforms.messenger import send_message
            alert_text = (
                f"🚨 [CẦN XỬ LÝ NGAY - SHOP ĐỒ NAM]\n"
                f"• Khách hàng: {sender_id}\n"
                f"• Tin nhắn: \"{message}\"\n"
                f"• Lý do: {reason}\n\n"
                f"👉 Hãy vào Meta Business Suite / Messenger Page để trả lời khách ngay nhé!"
            )
            send_message(admin_psid, alert_text)
            logger.info(f"📲 Đã gửi cảnh báo đến Admin Messenger ({admin_psid})")
        except Exception as e:
            logger.error(f"Không thể gửi alert tới Admin Messenger: {e}")

    # 2. Gửi thông báo qua Telegram (nếu cấu hình TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID trong .env)
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if tg_token and tg_chat_id:
        try:
            import requests
            tg_text = (
                f"🚨 *[CẦN XỬ LÝ NGAY - SHOP ĐỒ NAM]*\n"
                f"• *Kênh:* {platform.upper()}\n"
                f"• *Khách hàng:* `{sender_id}`\n"
                f"• *Tin nhắn:* {message}\n"
                f"• *Lý do:* {reason}\n\n"
                f"👉 _Vui lòng vào Hộp thư Page phản hồi cho khách!_"
            )
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": tg_chat_id, "text": tg_text, "parse_mode": "Markdown"},
                timeout=5
            )
            logger.info(f"📲 Đã gửi cảnh báo tới Telegram")
        except Exception as e:
            logger.error(f"Không thể gửi alert tới Telegram: {e}")


# ─── MAIN ───────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    os.makedirs('logs/conversations', exist_ok=True)
    os.makedirs('logs/alerts', exist_ok=True)
    
    logger.info("🚀 Auto Reply Server đang khởi động...")
    logger.info("📡 Endpoints:")
    logger.info("   POST /webhook/messenger")
    logger.info("   POST /webhook/zalo")
    logger.info("   POST /webhook/tiktok")
    logger.info("   POST /test  (testing)")
    logger.info("   GET  /sessions (xem danh sách Human Takeover)")
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'false').lower() == 'true'
    )
