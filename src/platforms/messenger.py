"""Messenger Platform – Gửi tin nhắn qua Facebook Graph API"""

import os
import requests
import logging

logger = logging.getLogger(__name__)

PAGE_ACCESS_TOKEN = os.getenv('MESSENGER_PAGE_ACCESS_TOKEN', '')


def send_message(recipient_id: str, text: str) -> bool:
    """Gửi tin nhắn text đến người dùng Messenger"""
    
    if not PAGE_ACCESS_TOKEN:
        logger.warning("⚠️ MESSENGER_PAGE_ACCESS_TOKEN chưa được cấu hình!")
        logger.info(f"[Messenger MOCK] To: {recipient_id} | Message: {text}")
        return True
    
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"✅ Messenger sent to {recipient_id}")
        return True
    except requests.RequestException as e:
        logger.error(f"❌ Messenger send failed: {e}")
        return False


def send_quick_replies(recipient_id: str, text: str, options: list) -> bool:
    """Gửi tin nhắn với các nút quick reply"""
    
    quick_replies = [
        {"content_type": "text", "title": opt, "payload": f"OPTION_{i}"}
        for i, opt in enumerate(options)
    ]
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": text,
            "quick_replies": quick_replies
        }
    }
    
    if not PAGE_ACCESS_TOKEN:
        logger.info(f"[Messenger MOCK] Quick replies to {recipient_id}: {options}")
        return True
    
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    response = requests.post(url, json=payload, timeout=10)
    return response.status_code == 200
