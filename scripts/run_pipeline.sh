#!/usr/bin/env bash
# 매니페스트 순서대로 전체 파이프라인을 클린 재현한다.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -f data/tracker.db
while IFS= read -r line; do
  line="${line%%#*}"; line="$(echo "$line" | xargs)"
  [ -z "$line" ] && continue
  echo "▶ $line"
  python3 "scripts/$line"
done < scripts/pipeline.txt
echo "✔ 파이프라인 완료"
