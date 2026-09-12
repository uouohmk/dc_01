# 주간 트래커 갱신

주 1회 또는 사용자 요청 시 실행. 예상 소요 20~40분.

## 0. 사전 확인

```bash
cd <저장소>
git pull
./scripts/run_pipeline.sh && python3 scripts/99_validate.py
```

시작 시점에 이미 실패하면 데이터 문제이므로 갱신하지 말고 보고한다.

## 1. 후보 명단 재확인 (먼저 한다)

사퇴·교체·예비선거 결과를 확인한다. 과거에 5주간 놓친 적이 있다.

```bash
sqlite3 data/tracker.db "SELECT r.state_code, r.office, c.candidate_name, \
  c.candidate_party, c.current_status FROM candidate c \
  JOIN election_race r ON r.race_id=c.race_id ORDER BY r.state_code;"
```

격전지부터 검색: `[주] Senate nominee 2026 withdrew replaced primary results`

## 2. 여론조사 — `poll-update` 스킬

STALE/AGING 레이스와 격전지 우선.

## 3. 정책 입장 — `policy-update` 스킬

새 행정명령·법안·정책안 중심. 특히 주지사의 서명 건.

## 4. 파이프라인

```bash
./scripts/run_pipeline.sh
python3 scripts/99_validate.py
```

`11_build_handoff.py` 가 마지막에 돌면서 HANDOFF.md 가 자동 갱신된다.
`05_cards.py` 는 한글 폰트가 필요하다 (`fonts-noto-cjk`).

## 5. 커밋

검증 통과 시에만.

```bash
git add -A
git commit -m "data: YYYY-MM-DD 갱신 — 조사 N건 · 근거 M건"
git push
```

## 6. 보고

- 적재 항목 수
- **거부 항목과 이유**
- 레버리지 순위 변동
- 리드가 바뀐 레이스
- 기존 기록 중 수정 필요 건
