
"""
CHƯƠNG TRÌNH: TEST GEMINI API ĐỘC LẬP

Mục đích:
    1. Đọc Gemini API key từ file .env.
    2. Khởi tạo Gemini Client.
    3. Gửi prompt đến model Gemini.
    4. Nhận kết quả và in ra terminal.

Chạy từ thư mục gốc LLM_V1:
    python scripts/test_gemini.py
"""

# ==================================================
# 1. IMPORT THƯ VIỆN
# ==================================================

# os là thư viện chuẩn của Python.
# os.getenv("TEN_BIEN") đọc giá trị biến môi trường.
import os

# Path dùng để xây dựng đường dẫn đến file/thư mục.
# __file__ là đường dẫn của file Python đang chạy.
from pathlib import Path

# load_dotenv() đọc các cặp KEY=VALUE trong file .env
# và đưa chúng vào môi trường của chương trình.
from dotenv import load_dotenv

# genai là module thuộc SDK google-genai.
# Cung cấp Client để tương tác với Gemini API.
from google import genai


# ==================================================
# 2. HÀM ĐỌC CẤU HÌNH
# ==================================================

def load_config():
    """
    Đọc API key và tên model Gemini từ file .env.

    Đầu vào:
        Không có tham số.

    Đầu ra:
        tuple (api_key, model_name)

    Ví dụ:
        ("key_thuc_te", "gemini-3.5-flash-lite")
    """

    # __file__ trỏ tới:
    # LLM_V1/scripts/test_gemini.py
    #
    # resolve() -> chuyển thành đường dẫn tuyệt đối.
    # parents[0] -> thư mục scripts/
    # parents[1] -> thư mục LLM_V1/
    #
    # Toán tử / của Path dùng để nối đường dẫn.
    project_root = Path(__file__).resolve().parents[1]

    # Ví dụ:
    # LLM_V1/.env
    env_path = project_root / ".env"

    # Đọc file .env vào các biến môi trường.
    load_dotenv(dotenv_path=env_path)

    # Lấy API key từ biến GEMINI_API_KEY.
    # Nếu không tồn tại, os.getenv() trả về None.
    api_key = os.getenv("GEMINI_API_KEY")

    # Đọc model từ file .env.
    # Tham số thứ hai là giá trị mặc định,
    # được dùng nếu GEMINI_MODEL không tồn tại.
    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite"
    )

    # Kiểm tra API key đã được cấu hình hay chưa.
    # "not api_key" đúng nếu api_key là None hoặc "".
    if not api_key or api_key == "key_that_cua_may":
        raise ValueError(
            "Chưa cấu hình GEMINI_API_KEY hợp lệ trong .env"
        )

    # Trả về hai giá trị dưới dạng tuple.
    return api_key, model_name


# ==================================================
# 3. HÀM GỌI GEMINI API
# ==================================================

def test_gemini():
    """
    Gửi một prompt đến Gemini và in kết quả.

    Luồng:
        Đọc .env
          -> Tạo Gemini Client
          -> Gửi prompt qua API
          -> Nhận response
          -> In kết quả ra terminal
    """

    # Gọi hàm load_config().
    # Python tự unpack tuple thành hai biến riêng.
    api_key, model_name = load_config()

    # Khởi tạo đối tượng Client.
    #
    # api_key=api_key:
    # - Bên trái là tên tham số do SDK quy định.
    # - Bên phải là biến Python chứa API key.
    #
    # Client quản lý việc gửi request tới Gemini API.
    client = genai.Client(api_key=api_key)

    # Nội dung gửi cho LLM.
    # Đây chỉ là prompt thử nghiệm kết nối.
    prompt = (
        "Hãy tạo một câu hỏi trắc nghiệm về động vật "
        "dành cho trẻ 7 tuổi, có 3 phương án A, B, C "
        "và chỉ một đáp án đúng. "
        "Viết bằng tiếng Việt."
    )

    print("===== GEMINI API TEST =====")
    print("Model:", model_name)
    print("Prompt:", prompt)
    print("\nĐang gửi request...\n")

    # Gửi request đến Gemini API.
    #
    # client.interactions.create():
    # - interactions là giao diện của Gemini Interactions API.
    # - create() tạo một lượt tương tác với model.
    #
    # model: mã model muốn sử dụng.
    # input: nội dung prompt gửi đến model.
    #
    # Hàm trả về một đối tượng response của SDK.
    response = client.interactions.create(
        model=model_name,
        input=prompt
    )

    # output_text là thuộc tính chứa phần văn bản
    # mà model đã sinh ra từ lượt tương tác.
    result = response.output_text

    # Nếu model không trả ra văn bản thì báo lỗi.
    if not result:
        raise ValueError("Gemini không trả về nội dung văn bản")

    print("===== KẾT QUẢ GEMINI =====")
    print(result)

    print("\nTest Gemini API thành công!")


# ==================================================
# 4. ĐIỂM BẮT ĐẦU CHƯƠNG TRÌNH
# ==================================================

# __name__ là biến đặc biệt do Python tự cung cấp.
#
# Khi chạy trực tiếp:
#   python scripts/test_gemini.py
#
# Python đặt:
#   __name__ = "__main__"
#
# Do đó, điều kiện dưới đây đúng và test_gemini()
# được thực thi.
#
# Nếu file được import từ file khác, điều kiện sai,
# tránh tự động gọi Gemini API ngoài ý muốn.
if __name__ == "__main__":
    test_gemini()
