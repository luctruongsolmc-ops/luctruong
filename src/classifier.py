"""
Intent Classifier
Phân loại ý định tin nhắn khách hàng bằng regex word boundary matching (hỗ trợ cả có dấu và không dấu)
"""

import re
import unicodedata
from typing import Optional


def remove_accents(input_str: str) -> str:
    """Chuyển chuỗi tiếng Việt có dấu thành không dấu"""
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).replace('đ', 'd').replace('Đ', 'D')


class IntentClassifier:
    """
    Phân loại ý định dựa trên từ khóa tiếng Việt (có dấu + không dấu).
    Dùng word boundaries để tránh match nhầm các từ ngắn (như 'te', 'vo', 'kem').
    """

    INTENT_PATTERNS = {
        "HUMAN_HANDOVER": {
            "priority": 0,
            "keywords": [
                "chat với người bán", "chat voi nguoi ban", "gặp người bán", "gap nguoi ban",
                "nói chuyện với người bán", "noi chuyen voi nguoi ban", "gặp nhân viên", "gap nhan vien",
                "chat với nhân viên", "chat voi nhan vien", "tư vấn viên", "tu van vien", "gặp tư vấn", "gap tu van",
                "gặp admin", "gap admin", "gặp chủ shop", "gap chu shop", "gặp người thật", "gap nguoi that",
                "người thật", "nguoi that", "chuyển người bán", "chuyen nguoi ban", "chuyển nhân viên", "chuyen nhan vien",
                "nhân viên đâu", "nhan vien dau", "gọi người bán", "goi nguoi ban", "gặp hỗ trợ", "gap ho tro"
            ]
        },
        "BOT_RESUME": {
            "priority": 0,
            "keywords": [
                "bật lại bot", "bat lai bot", "bật bot", "bat bot", "trợ lý ảo", "tro ly ao", "tự động", "tu dong"
            ]
        },
        "COMPLAINT": {
            "priority": 1,
            "keywords": [
                "lỗi", "loi", "hỏng", "hong", "vỡ", "vo", "không dùng được", "khong dung duoc",
                "tệ", "kém", "thất vọng", "that vong", "tức", "bực",
                "không như mô tả", "khong nhu mo ta", "bị lừa", "bi lua", "sai hàng", "sai hang", "sai mẫu", "sai mau",
                "tệ quá", "te qua", "chán quá", "chan qua", "khiếu nại", "khieu nai", "phàn nàn", "phan nan", "rách", "rach"
            ]
        },
        "REFUND": {
            "priority": 2,
            "keywords": [
                "hoàn tiền", "hoan tien", "trả tiền", "tra tien", "refund", "đổi trả", "doi tra",
                "trả hàng", "tra hang", "đổi hàng", "doi hang", "đổi size", "doi size",
                "không muốn nữa", "khong muon nua", "hủy đơn", "huy don", "hủy order", "huy order", "cancel"
            ]
        },
        "SHIPPING_INQUIRY": {
            "priority": 3,
            "keywords": [
                "phí ship", "phi ship", "tiền ship", "tien ship", "phí vận chuyển", "phi van chuyen",
                "phí giao", "phi giao", "phí giao hàng", "phi giao hang", "ship bao nhiêu", "ship bao nhieu",
                "ship bn", "ship đắt không", "ship dat khong", "freeship", "miễn phí ship", "mien phi ship",
                "thời gian ship", "thoi gian ship", "thời gian giao", "thoi gian giao", "thời gian nhận", "thoi gian nhan",
                "bao lâu nhận được", "bao lau nhan duoc", "bao lâu tới", "bao lau toi", "bao lâu đến", "bao lau den",
                "mấy ngày tới", "may ngay toi", "mấy ngày nhận được", "may ngay nhan duoc", "mấy ngày đến", "may ngay den",
                "mấy ngày", "may ngay", "mấy hôm", "may hom", "ship mấy ngày", "ship may ngay",
                "bao giờ nhận được", "bao gio nhan duoc", "giao trong bao lâu", "giao trong bao lau",
                "hỏa tốc", "hoa toc", "ship hỏa tốc", "ship hoa toc", "giao hỏa tốc", "giao hoa toc", "ship 2h", "giao 2h",
                "ship hà nội", "ship ha noi", "ship miền nam", "ship mien nam", "ship miền bắc", "ship mien bac",
                "ship miền trung", "ship mien trung", "ship tphcm", "ship sài gòn", "ship sai gon", "ship tỉnh", "ship tinh"
            ]
        },
        "ORDER_STATUS": {
            "priority": 4,
            "keywords": [
                "đơn hàng", "don hang", "order", "tracking", "theo dõi", "theo doi",
                "tra cứu đơn", "tra cuu don", "kiểm tra đơn", "kiem tra don",
                "đang ở đâu", "dang o dau", "chờ lâu", "cho lau", "chưa nhận được", "chua nhan duoc"
            ]
        },
        "PRICE_INQUIRY": {
            "priority": 5,
            "keywords": [
                "giá", "gia", "bao nhiêu", "bao nhieu", "bn", "nhiêu", "nhieu", "chi phí", "chi phi",
                "tiền", "tien", "giá sao", "gia sao", "mua", "đặt hàng", "dat hang",
                "báo giá", "bao gia", "quote", "sale", "khuyến mãi", "khuyen mai",
                "discount", "giảm giá", "giam gia", "ưu đãi", "uu dai", "rẻ không", "re khong"
            ]
        },
        "BOOKING": {
            "priority": 6,
            "keywords": [
                "đặt lịch", "dat lich", "book", "hẹn", "hen", "demo", "tư vấn", "tu van",
                "gọi điện", "goi dien", "gọi lại", "goi lai", "gọi ngay", "goi ngay", "sđt", "sdt"
            ]
        },
        "PRODUCT_INFO": {
            "priority": 7,
            "keywords": [
                "áo thun", "ao thun", "sơ mi", "so mi", "polo", "áo khoác", "ao khoac", "hoodie", "sweatshirt",
                "quần jeans", "quan jeans", "quần jean", "quan jean", "quần kaki", "quan kaki",
                "quần short", "quan short", "quần đùi", "quan dui", "quần tây", "quan tay", "quần âu", "quan au",
                "đồ thể thao", "do the thao", "đồ mặc nhà", "do mac nha", "size", "kích thước", "kich thuoc",
                "màu", "mau", "màu sắc", "mau sac", "chất liệu", "chat lieu", "vải gì", "vai gi", "form",
                "có mẫu nào", "co mau nao", "có hàng không", "co hang khong", "còn không", "con khong",
                "quảng cáo", "quang cao", "tốt không", "tot khong"
            ]
        },
        "GREETING": {
            "priority": 8,
            "keywords": [
                "xin chào", "xin chao", "chào", "chao", "hello", "hi", "ơi", "oi", "cho hỏi", "cho hoi",
                "hey", "shop ơi", "shop oi", "ad ơi", "ad oi", "admin ơi", "admin oi"
            ]
        }
    }

    def _match_keyword(self, keyword: str, text: str, text_no_accents: str) -> bool:
        """Kiểm tra từ khóa khớp độc lập theo word boundary"""
        pattern = r'(?i)(?<!\w)' + re.escape(keyword) + r'(?!\w)'
        return bool(re.search(pattern, text) or re.search(pattern, text_no_accents))

    def classify(self, message: str) -> dict:
        """
        Phân loại tin nhắn và trả về intent + confidence
        """
        message_lower = message.lower().strip()
        message_no_accents = remove_accents(message_lower)
        
        best_intent = "UNKNOWN"
        best_priority = 999
        matched_keywords = []
        
        for intent_name, config in self.INTENT_PATTERNS.items():
            keywords = config["keywords"]
            priority = config["priority"]
            
            matches = [
                kw for kw in keywords 
                if self._match_keyword(kw, message_lower, message_no_accents)
            ]
            
            if matches and priority < best_priority:
                best_intent = intent_name
                best_priority = priority
                matched_keywords = matches
        
        confidence = self._calculate_confidence(
            matched_keywords, 
            message_lower,
            best_intent
        )
        
        return {
            "type": best_intent,
            "confidence": confidence,
            "matched_keywords": matched_keywords
        }

    def _calculate_confidence(
        self, 
        matched_keywords: list, 
        message: str,
        intent: str
    ) -> float:
        """Tính điểm confidence từ 0.0 đến 1.0"""
        if intent == "UNKNOWN" or not matched_keywords:
            return 0.0
        
        word_count = len(message.split())
        if word_count == 0:
            return 0.5
        
        base_score = min(len(matched_keywords) / max(word_count * 0.3, 1), 1.0)
        multi_keyword_bonus = min(len(matched_keywords) * 0.1, 0.3)
        confidence = min(base_score + multi_keyword_bonus + 0.5, 1.0)
        return round(confidence, 2)
