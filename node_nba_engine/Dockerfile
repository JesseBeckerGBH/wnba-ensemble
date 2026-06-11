FROM python:3.13-slim

WORKDIR /app

# Copy the NBA Python node + Rust Engine + C++ Layer
COPY node_nba_engine/ /app/node_nba_engine/
COPY math_engine_rust/ /app/math_engine_rust/
COPY execution_layer_cpp/ /app/execution_layer_cpp/

# Install Python requirements
RUN pip install --no-cache-dir -r /app/node_nba_engine/requirements.txt

# Set the entrypoint to the 24/7 inference runner
WORKDIR /app/node_nba_engine
CMD ["python", "scripts/nba_inference_loop.py"]
