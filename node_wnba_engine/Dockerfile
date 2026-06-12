FROM python:3.13-slim

WORKDIR /app

# Copy the entire WNBA Python node, Rust Engine, and C++ Layer
# We assume the docker context is the scratch workspace root.
COPY node_wnba_engine/ /app/node_wnba_engine/
COPY math_engine_rust/ /app/math_engine_rust/
COPY execution_layer_cpp/ /app/execution_layer_cpp/

# Install Python requirements
RUN pip install --no-cache-dir -r /app/node_wnba_engine/requirements.txt
RUN pip install python-dotenv duckdb xgboost lightgbm

# Set the entrypoint to the 24/7 inference runner
WORKDIR /app/node_wnba_engine
CMD ["python", "scripts/wnba_inference_loop.py"]
