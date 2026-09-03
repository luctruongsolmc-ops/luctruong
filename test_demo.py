"""
Test tất cả các loại tin nhắn – chạy để kiểm tra hệ thống
"""

import sys
import os
import json

# Fix encoding cho Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Thêm src vào path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from classifier import IntentClassifier
from reply_generator import ReplyGenerator

classifier = IntentClassifier()
generator  = ReplyGenerator()

# ── Danh sách tin nhắn test thực tế ─────────────────────────────────────

TEST_MESSAGES = [
    # Messenger
    ("messenger", "shop ơi cái áo này giá bao nhiêu vậy??", "Lan Anh"),
    ("messenger", "mình order rồi mà sao chưa thấy ship vậy shop?", None),
    ("messenger", "hàng giao bị lỗi hết rồi, thất vọng quá 😠", "Minh"),
    ("messenger", "phí ship bên mình tính sao vậy shop? ở hà nội thì bao lâu nhận được", "Tuấn Anh"),
    ("messenger", "mình ở sài gòn thì phí ship với mấy ngày nhận được", "Quốc Bảo"),
    ("messenger", "mình ở hải phòng thì ship bao nhiêu và mấy ngày tới?", "Hải Yến"),
    ("messenger", "ship ve nghe an ton bao nhieu tien ship va bao lau co hang", "Đức Huy"),

    # Zalo
    ("zalo", "Chào shop, tôi muốn hỏi về bảng giá sản phẩm", "Nguyễn Văn An"),
    ("zalo", "Tôi muốn đặt lịch tư vấn, bạn có slot nào không?", None),
    ("zalo", "Sản phẩm không như mô tả, tôi muốn đổi trả và hoàn tiền", "Thu Hà"),
    ("zalo", "Shop có giao hỏa tốc không? Phí vận chuyển miền Trung bao nhiêu?", "Hoàng"),
    ("zalo", "Tôi ở Cần Thơ muốn mua quần tây, giao hàng mấy ngày tới?", "Bác Nam"),
    ("zalo", "Em ở Cầu Giấy Hà Nội cần gấp 1 áo sơ mi có ship hỏa tốc không ạ?", "Trọng"),

    # TikTok
    ("tiktok", "giá bao nhiêu vậy mn ơi 👀", "user_tiktok_123"),
    ("tiktok", "shop ơi cho hỏi có size XL không ạ", None),
    ("tiktok", "sp có tốt không hay quảng cáo không 😅", "user_456"),
    ("tiktok", "ship miền bắc mấy ngày tới ạ", "viet_nam_99"),
    ("tiktok", "em ở đà nẵng ship mấy ngày vậy shop", "da_nang_boy"),
]

# ── Chạy test ────────────────────────────────────────────────────────────

def run_tests():
    print("=" * 70)
    print("[TEST] AUTO REPLY SYSTEM - DEMO TEST")
    print("=" * 70)

    for i, (platform, message, username) in enumerate(TEST_MESSAGES, 1):
        print(f"\n{'-'*60}")
        print(f"[#{i}] Platform: {platform.upper()}")
        print(f"[Khach]   {username or 'An danh'}")
        print(f"[Tin nhan] {message}")
        
        # Phân loại
        intent = classifier.classify(message)
        print(f"[Intent]  {intent['type']} (confidence: {intent['confidence']:.0%})")
        
        # Tạo phản hồi
        result = generator.generate(
            message=message,
            intent=intent,
            platform=platform,
            username=username
        )
        
        print(f"[Priority] {result['priority']}")
        print(f"[Reply]\n   {result['reply']}")
        
        if result.get('escalate'):
            print(f"*** ESCALATE: {result['escalate_reason']} ***")

    print(f"\n{'='*70}")
    print("[DONE] Test hoan thanh! Kiem tra logs/ de xem chi tiet.")


if __name__ == '__main__':
    run_tests()
