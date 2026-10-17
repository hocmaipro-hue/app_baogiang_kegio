FROM debian:bullseye-slim

# Cài đặt môi trường đồ họa ảo, Python, Tkinter và noVNC
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    x11vnc \
    xvfb \
    novnc \
    websockify \
    openbox \
    fonts-liberation \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/

# Đặt thư mục làm việc
WORKDIR /app

# Copy toàn bộ 43 file code vào máy chủ
COPY . /app

# Cài đặt các thư viện Python cần thiết
RUN pip3 install --no-cache-dir psycopg2-binary openpyxl

# Thiết lập cổng web (HuggingFace dùng cổng 7860)
EXPOSE 7860

# Script khởi động màn hình ảo và chạy thẳng main.py
CMD Xvfb :1 -screen 0 1280x800x24 & \
    export DISPLAY=:1 && \
    openbox & \
    x11vnc -display :1 -nopw -listen localhost -xkb & \
    websockify --web /usr/share/novnc 7860 localhost:5900 & \
    python3 main.py