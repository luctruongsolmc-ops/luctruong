"""TikTok Platform – Reply comment / Direct message qua TikTok API"""

import os
import requests
import logging

logger = logging.getLogger(__name__)

ACCESS_TOKEN = os.getenv('TIKTOK_ACCESS_TOKEN', '')
TIKTOK_API_URL = "https://open.tiktokapis.com/v2"


def send_message(user_id: str, text: str, comment_id: str = None) -> bool:
    """
    Reply comment TikTok hoặc gửi Direct Message
    Nếu có comment_id: reply comment
    Nếu không: gửi DM
    """
    
    if not ACCESS_TOKEN:
        logger.warning("⚠️ TIKTOK_ACCESS_TOKEN chưa được cấu hình!")
        logger.info(f"[TikTok MOCK] To: {user_id} | Message: {text}")
        return True

    if comment_id:
        return _reply_comment(comment_id, text)
    else:
        return _send_dm(user_id, text)


def _reply_comment(comment_id: str, text: str) -> bool:
    """Reply vào một comment TikTok cụ thể"""
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "video_id": "",  # Cần video_id thực tế
        "text": text,
        "reply_comment_id": comment_id
    }
    
    try:
        response = requests.post(
            f"{TIKTOK_API_URL}/video/comment/reply/",
            json=payload,
            headers=headers,
            timeout=10
        )
        result = response.json()
        success = result.get('error', {}).get('code') == 'ok'
        
        if success:
            logger.info(f"✅ TikTok replied to comment {comment_id}")
        else:
            logger.error(f"❌ TikTok error: {result}")
        
        return success
    except Exception as e:
        logger.error(f"❌ TikTok send failed: {e}")
        return False


def _send_dm(user_id: str, text: str) -> bool:
    """Gửi Direct Message trên TikTok"""
    logger.info(f"[TikTok DM] To: {user_id} | Message: {text}")
    # Implement theo TikTok Business API documentation
    return True
