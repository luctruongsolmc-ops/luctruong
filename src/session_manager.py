"""
Session Manager - Quản lý trạng thái phiên trò chuyện
Theo dõi khách hàng nào đang ở chế độ Chat với người thật (Human Takeover)
"""

import os
import json
from datetime import datetime
from typing import Optional

SESSION_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'human_takeover_sessions.json')


class SessionManager:
    """Quản lý các phiên hội thoại được tiếp quản bởi Admin / Người thật"""

    def __init__(self, session_file: str = SESSION_FILE):
        self.session_file = session_file
        self.sessions = self._load_sessions()

    def _load_sessions(self) -> dict:
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_sessions(self):
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def is_human_mode(self, sender_id: str) -> bool:
        """Kiểm tra xem khách hàng có đang trong chế độ chat với người thật không"""
        session = self.sessions.get(str(sender_id))
        if not session:
            return False
        return session.get("is_human_mode", False)

    def set_human_mode(
        self, 
        sender_id: str, 
        enabled: bool = True, 
        reason: str = "Khách yêu cầu chat với người bán", 
        platform: str = "messenger"
    ):
        """Chuyển đổi trạng thái Human Takeover"""
        str_id = str(sender_id)
        if enabled:
            self.sessions[str_id] = {
                "is_human_mode": True,
                "platform": platform,
                "takeover_at": datetime.now().isoformat(),
                "reason": reason
            }
        else:
            if str_id in self.sessions:
                self.sessions[str_id]["is_human_mode"] = False
                self.sessions[str_id]["resumed_at"] = datetime.now().isoformat()
        self._save_sessions()

    def reset_bot_mode(self, sender_id: str):
        """Bật lại chế độ tự động cho bot"""
        self.set_human_mode(sender_id, False, reason="Khách hoặc Admin bật lại Bot")
