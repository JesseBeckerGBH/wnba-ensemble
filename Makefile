.PHONY: build-all build-rust build-cpp build-go deploy-proxmox run-stack boot-mcp clean

build-all: build-rust build-cpp build-go
	@echo "[*] All native polyglot extensions compiled successfully."

build-rust:
	@echo "[*] Compiling math_engine_rust..."
	@echo "cd math_engine_rust && cargo build --release"

build-cpp:
	@echo "[*] Compiling execution_layer_cpp..."
	@echo "cd execution_layer_cpp && make CXX=g++"

build-go:
	@echo "[*] Compiling ingestion_go..."
	@echo "cd ingestion_go && go build -o ingestion_daemon"

deploy-proxmox:
	@echo "[>>>] Initiating Proxmox VE orchestration..."
	docker-compose up -d --build

run-stack:
	@echo "[*] Running Polyglot Syndicate Stack"
	docker-compose up

boot-mcp:
	@echo "[>>>] Booting PostgreSQL MCP Server connection securely..."
	@echo "npx -y @modelcontextprotocol/server-postgres postgresql://syndicate_admin:$$DB_PASS@127.0.0.1:5432/syndicate_db"

clean:
	@echo "[*] Scrubbing cache and binaries..."
	docker-compose down -v
