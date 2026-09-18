#!/bin/bash
# 크롤링 -> LLM 요약 -> RAG ingest -> Fly.io 동기화 -> 봇 재시작을 순서대로 실행.
# launchd(macOS)에서 매일 자동 실행되도록 등록해서 쓴다.
set -uo pipefail

PROJECT_DIR="/Users/uzinee/project/career-copilot"
FLY_APP="career-copilot-bot"

cd "$PROJECT_DIR" || exit 1
mkdir -p logs

echo "===== $(date '+%Y-%m-%d %H:%M:%S') 시작 ====="

echo "--- 1. 크롤링 ---"
.venv/bin/python -m crawler.run

echo "--- 2. LLM 요약 ---"
.venv/bin/python -m llm.run

echo "--- 3. RAG ingest (경력 코퍼스 변경분만 처리) ---"
.venv/bin/python -m rag.run_ingest

echo "--- 4. Fly.io로 데이터 동기화 ---"
./scripts/sync_to_fly.sh "$FLY_APP"

echo "--- 5. 봇 재시작 ---"
/opt/homebrew/bin/flyctl apps restart "$FLY_APP"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') 종료 ====="
