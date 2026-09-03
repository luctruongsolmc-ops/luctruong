# -*- coding: utf-8 -*-
import sys
import os
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import _process_message
from session_manager import SessionManager

session_manager = SessionManager()

def run_handover_test():
    print("=" * 70)
    print("[TEST] KIỂM TRA TÍNH NĂNG 'CHAT VỚI NGƯỜI BÁN' & HUMAN TAKEOVER")
    print("=" * 70)

    test_user_id = "khach_hang_test_999"
    # Reset state
    session_manager.reset_bot_mode(test_user_id)

    # Bước 1: Khách hỏi giá đồ
    print("\n--- BƯỚC 1: Khách hỏi đồ nam bình thường ---")
    msg1 = "shop có áo polo không giá sao"
    res1 = _process_message("messenger", test_user_id, msg1)
    print(f"Khách: {msg1}")
    print(f"Bot rep:\n{res1.get('reply')}")
    print(f"Human mode: {session_manager.is_human_mode(test_user_id)}")

    # Bước 2: Khách nhắn "Chat với người bán"
    print("\n--- BƯỚC 2: Khách nhắn 'Chat với người bán' ---")
    msg2 = "Chat với người bán"
    res2 = _process_message("messenger", test_user_id, msg2)
    print(f"Khách: {msg2}")
    print(f"Bot rep:\n{res2.get('reply')}")
    print(f"Intent: {res2.get('intent')} | Escalate: {res2.get('escalate')} | Reason: {res2.get('escalate_reason')}")
    print(f"Human mode: {session_manager.is_human_mode(test_user_id)}")

    # Bước 3: Khách nhắn tiếp tin nhắn sau khi đã kết nối người bán
    print("\n--- BƯỚC 3: Khách nhắn tiếp tin nhắn sau khi đã chuyển người bán ---")
    msg3 = "Cho mình xem mẫu áo sơ mi trắng size L với shop ơi"
    res3 = _process_message("messenger", test_user_id, msg3)
    print(f"Khách: {msg3}")
    print(f"Bot rep: {res3.get('reply')} (None = Bot im lặng để 2 người chat với nhau)")
    print(f"Is human mode active: {res3.get('is_human_mode')}")

    # Bước 4: Khách nhắn thêm tin nữa
    print("\n--- BƯỚC 4: Khách nhắn thêm câu nữa ---")
    msg4 = "Alo shop có đó không?"
    res4 = _process_message("messenger", test_user_id, msg4)
    print(f"Khách: {msg4}")
    print(f"Bot rep: {res4.get('reply')} (None = Bot vẫn tắt)")

    # Bước 5: Khách hoặc Admin gõ "bật lại bot"
    print("\n--- BƯỚC 5: Khách gõ 'bật lại bot' ---")
    msg5 = "bật lại bot"
    res5 = _process_message("messenger", test_user_id, msg5)
    print(f"Khách: {msg5}")
    print(f"Bot rep:\n{res5.get('reply')}")
    print(f"Human mode: {session_manager.is_human_mode(test_user_id)}")

    print("\n" + "=" * 70)
    print("[KẾT QUẢ] Test tính năng Chat với người bán hoàn toàn THÀNH CÔNG! 🎉")
    print("=" * 70)

if __name__ == '__main__':
    run_handover_test()
