#!/bin/bash
# 로컬 data/ (SQLite DB + Chroma 벡터스토어)를 Fly.io 볼륨(/data)으로 업로드한다.
# 크롤링/요약/RAG ingest는 로컬에서만 돌리고, 결과만 클라우드 봇에 올려주는 용도.
#
# 사용법: ./scripts/sync_to_fly.sh <fly-app-name>
set -euo pipefail

APP_NAME="${1:?사용법: ./scripts/sync_to_fly.sh <fly-app-name>}"
ARCHIVE_NAME="career_copilot_data.tar.gz"
LOCAL_ARCHIVE="/tmp/${ARCHIVE_NAME}"

cd "$(dirname "$0")/.."

if [ ! -d data ]; then
  echo "data/ 디렉토리가 없습니다. 먼저 로컬에서 크롤링/요약을 한 번 이상 실행해주세요."
  exit 1
fi

echo "1/3 로컬 data/ 를 압축합니다..."
tar czf "$LOCAL_ARCHIVE" data

echo "2/3 Fly.io 볼륨으로 업로드합니다 (앱: $APP_NAME)..."
flyctl ssh sftp shell -a "$APP_NAME" <<EOF
put ${LOCAL_ARCHIVE} /data/${ARCHIVE_NAME}
EOF

echo "3/3 원격에서 압축을 해제합니다..."
# -C 인자는 셸 연산자(&&)를 해석하지 않고 통째로 한 명령의 인자로 넘어가므로
# tar 실행과 정리(rm)를 각각 별도의 ssh console 호출로 나눈다.
flyctl ssh console -a "$APP_NAME" -C "tar xzf /data/${ARCHIVE_NAME} -C /"
flyctl ssh console -a "$APP_NAME" -C "rm /data/${ARCHIVE_NAME}"

rm "$LOCAL_ARCHIVE"
echo "동기화 완료. 봇을 재시작하면(fly apps restart $APP_NAME) 새 데이터가 반영됩니다."
