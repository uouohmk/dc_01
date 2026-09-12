---
name: poll-update
description: 2026 미국 중간선거 여론조사와 레이스 등급을 수집해 dc_01 트래커 DB에 적재한다. 사용자가 '여론조사 갱신', '격전지 조사 확인', '등급 변동', 'poll update', '새 조사 반영'을 언급하거나 주기적 갱신 작업을 요청하면 사용한다. 필드 기간이 명시된 조사만 적재하며 후보 명단과 대조해 실존하지 않는 대진을 걸러낸다.
---

# 여론조사 갱신

## 1. 현재 상태 확인

```bash
sqlite3 data/tracker.db "SELECT state_code, office, poll_count, last_poll_date, \
  latest_margin, poll_age_days, coverage_status FROM v_poll_coverage \
  WHERE poll_count>0 ORDER BY last_poll_date DESC;"
```

우선순위: `coverage_status` 가 STALE/AGING 인 레이스 → 격전지(Toss-up/Lean) → 나머지.

현재 후보 명단을 반드시 먼저 뽑는다. 이후 모든 조사를 이 명단과 대조한다.

```bash
sqlite3 data/tracker.db "SELECT r.state_code, r.office, c.candidate_name, c.candidate_party \
  FROM candidate c JOIN election_race r ON r.race_id=c.race_id \
  WHERE c.current_status <> 'Withdrawn' ORDER BY r.state_code;"
```

## 2. 검색

질의는 고유명 + 월 + 연도로 좁힌다.
`Ohio Senate poll September 2026 Brown Husted` 형태가 가장 잘 걸린다.

브라우저로 원문을 연다. 검색 요약만으로 적재하지 않는다.
집계 사이트는 연도와 후보명을 대조한 뒤에만 쓴다.

## 3. 추출 항목

조사 1건마다 아래를 모두 확보한다. 하나라도 없으면 적재하지 않는다.

| 항목 | 비고 |
|---|---|
| 주 · 직위 | office 는 'U.S. Senate' 또는 'Governor' |
| 조사기관 | 당파 스폰서면 표기 (예: `Susquehanna (R)`) |
| 필드 시작·종료 | **필수.** 없으면 적재 금지 |
| 표본 수 · 모집단 | RV / LV / A |
| 민주 % · 공화 % | 마진은 민주 − 공화. 민주 우세면 양수 |
| 출처 URL · 발행일 | **필수** |

집계기관의 공식 평균(Pollsmax, Decision Desk HQ 등)은 `is_average=1` 로 적재한다.
직접 평균을 계산해서 넣지 않는다.

## 4. 스크립트 작성

`scripts/NN_polls_MMDD.py` 를 새로 만든다. 기존 파일을 고치지 않는다.
번호는 `scripts/` 의 최대값 + 1.

```python
import sqlite3, math
con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x>0 else None)
cur = con.cursor()
NOW = "YYYY-MM-DD"

# 1) source 등록 (tier: 대학·공공 6, 조사기관 8, 언론 9)
cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
    published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", (...))

# 2) polling 적재
#    margin_d_minus_r : 민주 − 공화
cur.execute("""INSERT INTO polling(poll_id,race_id,pollster,field_start,field_end,
    sample_size,population,margin_d_minus_r,is_average,polling_source,source_id)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (...))

# 3) race_rating (등급이 있을 때만)
#    rating_code: SAFE_D LIKELY_D LEAN_D TILT_D TOSSUP TILT_R LEAN_R LIKELY_R SAFE_R
#    rater: Cook Political Report / Sabato Crystal Ball / Inside Elections /
#           Almanac of American Politics / Fox News / DDHQ / 270toWin Consensus / Other

# 4) change_log — 리드가 바뀌거나 등급이 이동하면 반드시 기록
```

`scripts/pipeline.txt` 의 `# --- 이하 빌드` 앞에 파일명을 추가한다.

## 5. 검증

```bash
./scripts/run_pipeline.sh && python3 scripts/99_validate.py
```

둘 다 통과해야 커밋한다. 실패하면 원인을 보고하고 멈춘다.

## 거부 기준

- 필드 기간 없음
- 후보 명단에 없는 인물 등장 (동명이인·구 대진 가능성)
- 원문 접근 불가 (유료벽·robots 차단)
- 종료일이 미래

거부한 항목은 **개수와 이유를 반드시 보고**한다. 조용히 빼지 않는다.
