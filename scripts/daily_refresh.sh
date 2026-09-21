#!/bin/bash
# 크롤링 -> LLM 요약 -> RAG ingest -> Fly.io 동기화 -> 봇 재시작을 순서대로 실행.
# launchd(macOS)에서 자동 실행되도록 등록해서 쓴다 (scripts/install_launchd.sh 참고).
set -uo pipefail

# launchd는 PATH가 거의 비어있는 상태로 실행하므로, Homebrew가 흔히 설치되는
# 위치를 명시적으로 추가한다 (Apple Silicon/Intel 둘 다 커버).
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 어디에 clone했든 동작하도록 스크립트 위치 기준으로 프로젝트 루트를 계산한다.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1
mkdir -p logs

# fly.toml의 app 이름을 그대로 사용 (포크해서 앱 이름을 바꿔도 여기 수정할 필요 없음).
FLY_APP="${FLY_APP:-$(grep -m1 '^app = ' fly.toml | sed -E "s/^app = ['\"]([^'\"]+)['\"].*/\1/")}"

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
flyctl apps restart "$FLY_APP"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') 종료 ====="
