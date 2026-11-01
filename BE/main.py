
"""
FILE: BE/main.py

MỤC ĐÍCH:
    Khởi chạy Backend FastAPI bằng lệnh:
        python main.py

Backend chạy tại:
    http://127.0.0.1:8000

Swagger:
    http://127.0.0.1:8000/docs
"""

# uvicorn là ASGI Server dùng để chạy ứng dụng FastAPI.
import uvicorn


# __name__ == "__main__":
# Chỉ thực thi khi chạy trực tiếp file này:
#     python main.py
#
# Nếu file được import bởi module khác,
# khối lệnh bên dưới sẽ không được thực thi.
if __name__ == "__main__":

    # uvicorn.run() khởi động HTTP Server.
    #
    # "app.main:app":
    #   app.main -> module BE/app/main.py
    #   :app     -> đối tượng FastAPI tên app
    #
    # host:
    #   127.0.0.1 nghĩa là chỉ truy cập từ máy local.
    #
    # port:
    #   Cổng TCP mà Backend sử dụng.
    #
    # reload=True:
    #   Tự động khởi động lại server khi sửa code.
    #   Chỉ nên dùng trong môi trường development.
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
