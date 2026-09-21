#!/bin/bash
# scripts/daily_refresh.sh를 매일 자동 실행하도록 launchd(macOS)에 등록한다.
# 어디에 clone했든 그대로 실행하면 경로가 자동으로 채워진다.
set -euo pipefail

LABEL="com.career-copilot.daily-refresh"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$PROJECT_DIR/scripts/${LABEL}.plist.template"
TARGET="$HOME/Library/LaunchAgents/${LABEL}.plist"

if [ ! -f "$TEMPLATE" ]; then
  echo "템플릿을 찾을 수 없습니다: $TEMPLATE"
  exit 1
fi

mkdir -p "$PROJECT_DIR/logs" "$HOME/Library/LaunchAgents"

sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$TEMPLATE" > "$TARGET"
chmod +x "$PROJECT_DIR/scripts/daily_refresh.sh"

# 이미 등록되어 있으면 내려받고 새로 올린다 (경로가 바뀐 경우 대비, 실패해도 무시).
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$TARGET"

echo "등록 완료: $TARGET"
echo "  - 지금 로드되면서 1회 즉시 실행되고, 이후 24시간마다 반복됩니다."
echo "  - 로그: $PROJECT_DIR/logs/daily_refresh.log"
echo "  - 끄려면: launchctl bootout gui/\$(id -u)/$LABEL"
