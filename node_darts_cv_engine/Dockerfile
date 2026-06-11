# --- STAGE 1: Compile Rust Math Engine ---
FROM rust:1.80-slim-bookworm as rust-builder
WORKDIR /usr/src/math_engine
COPY math_engine_rust/Cargo.toml .
COPY math_engine_rust/src ./src
RUN cargo build --release

# --- STAGE 2: Compile C++ Execution Layer ---
FROM debian:bookworm-slim as cpp-builder
RUN apt-get update && apt-get install -y g++ 
WORKDIR /usr/src/execution_engine
COPY execution_layer_cpp/execution_bin.cpp .
RUN g++ -O3 execution_bin.cpp -o execution_bin

# --- STAGE 3: Final Python Computer Vision + Polyglot Container ---
FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OpenCV dependencies, Tesseract OCR, and Xvfb (Headless Display), and ML dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    tesseract-ocr \
    xvfb \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/node_darts_cv_engine

# Copy dependencies
COPY darts_ml/requirements.txt ./req_ensemble.txt
RUN pip install --no-cache-dir -r req_ensemble.txt || true
RUN pip install --no-cache-dir opencv-python pytesseract mss

# Copy Compiled Binaries
COPY --from=rust-builder /usr/src/math_engine/target/release/math_engine ./math_engine_rust/target/release/
COPY --from=cpp-builder /usr/src/execution_engine/execution_bin ./execution_layer_cpp/

# Copy Python Logic
COPY vision/ ./vision/
COPY scripts/ ./scripts/
# Copy the actual ML ensemble logic
COPY darts_ml/ ./darts_ml/

# We use Supervisor or a custom entrypoint to start Xvfb AND the Python bots
RUN echo '#!/bin/bash\n\
rm -f /tmp/.X99-lock \n\
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 & \n\
export DISPLAY=:99 \n\
sleep 1 \n\
python3 scripts/darts_inference.py & \n\
python3 vision/cv_panopticon.py \n\
' > /app/start_relativistic_engine.sh && chmod +x /app/start_relativistic_engine.sh

CMD ["/app/start_relativistic_engine.sh"]
