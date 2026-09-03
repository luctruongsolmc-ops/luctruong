"""Zalo Platform – Gửi tin nhắn qua Zalo OA API"""

import os
import requests
import logging

logger = logging.getLogger(__name__)

OA_ACCESS_TOKEN = os.getenv('ZALO_OA_ACCESS_TOKEN', '')
ZALO_API_URL = "https://openapi.zalo.me/v3.0/oa/message/cs"


def send_message(recipient_id: str, text: str) -> bool:
    """Gửi tin nhắn text đến người dùng Zalo OA"""
    
    if not OA_ACCESS_TOKEN:
        logger.warning("⚠️ ZALO_OA_ACCESS_TOKEN chưa được cấu hình!")
        logger.info(f"[Zalo MOCK] To: {recipient_id} | Message: {text}")
        return True
    
    headers = {
        "access_token": OA_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    payload = {
        "recipient": {"user_id": recipient_id},
        "message": {"text": text}
    }
    
    try:
        response = requests.post(ZALO_API_URL, json=payload, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('error') == 0:
            logger.info(f"✅ Zalo sent to {recipient_id}")
            return True
        else:
            logger.error(f"❌ Zalo error: {result.get('message')}")
            return False
    except requests.RequestException as e:
        logger.error(f"❌ Zalo send failed: {e}")
        return False
