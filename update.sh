#!/usr/bin/env bash
# 데이터 갱신 후 재빌드 → 커밋 → 배포
set -e
python3 scripts/02_seed_step2_3.py
python3 scripts/04_positions.py
python3 scripts/06_update_0829.py
python3 scripts/07_update_0830.py
python3 scripts/08_update_0831.py
python3 scripts/09_update_0901.py
python3 scripts/10_update_0902.py
python3 scripts/03_build_dashboard.py
python3 scripts/05_cards.py
python3 scripts/11_build_handoff.py

git add -A
git commit -m "data update $(date +%Y-%m-%d)"
git push
