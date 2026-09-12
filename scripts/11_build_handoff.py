#!/usr/bin/env python3
"""HANDOFF.md 생성기.

다른 시스템·팀이 이 프로젝트를 이어받아 자동화할 수 있도록
설계 원칙 · 스키마 · 스코어링 모델 · 데이터 현황 · 남은 작업 · 함정을
단일 파일로 출력한다.

DB에서 직접 읽으므로 갱신 후 다시 실행하면 수치가 자동 반영된다.
반드시 파이프라인의 마지막에 실행할 것.
"""
import sqlite3, math, os, datetime

DB = "data/tracker.db"
OUT = "HANDOFF.md"
con = sqlite3.connect(DB)
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
con.row_factory = sqlite3.Row
cur = con.cursor()

def q1(sql, *a):
    r = cur.execute(sql, a).fetchone()
    return r[0] if r else 0

def rows(sql, *a):
    return cur.execute(sql, a).fetchall()

TODAY = "2026-09-10"
ELECTION = datetime.date(2026, 11, 3)
DDAY = (ELECTION - datetime.date(2026, 9, 10)).days

# ---------------------------------------------------------------- 수집 현황
TABLES = ["source","state_political_structure","election_race","candidate","race_rating",
          "polling","governor_race_detail","politician","politician_dc_position",
          "position_evidence","position_axis_score","dc_project","dc_vendor_count",
          "state_dc_context","dc_public_opinion","dc_election_risk","scenario",
          "grid_capacity_price","change_log","source_conflict"]
counts = {t: q1(f"SELECT COUNT(*) FROM {t}") for t in TABLES}

house_races  = q1("SELECT COUNT(*) FROM election_race WHERE office='U.S. House'")
sen_races    = q1("SELECT COUNT(*) FROM election_race WHERE office='U.S. Senate'")
gov_races    = q1("SELECT COUNT(*) FROM election_race WHERE office='Governor'")
leg_filled   = q1("SELECT COUNT(*) FROM state_political_structure WHERE state_senate_total IS NOT NULL")
ctrl_filled  = q1("SELECT COUNT(*) FROM state_political_structure WHERE political_control IS NOT NULL")
pos_states   = q1("""SELECT COUNT(DISTINCT state_code) FROM politician
                     WHERE politician_id IN (SELECT politician_id FROM politician_dc_position)""")
polled       = q1("SELECT COUNT(*) FROM v_poll_coverage WHERE poll_count>0")
total_races  = q1("SELECT COUNT(*) FROM v_poll_coverage")

DELIVERABLES = [
 ("1","전체 데이터베이스 스키마","DONE", f"{len(TABLES)}+ 테이블 · 9 뷰 · 4 트리거"),
 ("2","50개 주 기본 데이터 테이블","PARTIAL",
  f"주지사·연방의석 50/50 · 주의회 의석 {leg_filled}/50 · 정당통제 판정 {ctrl_filled}/50"),
 ("3","2026 상원 선거 대상 의석","DONE", f"{sen_races}석 (정규 33 + 보궐 2)"),
 ("4","2026 하원 선거 전체 구조","NOT_STARTED", f"{house_races}/435"),
 ("5","2026 주지사 선거 대상 주","DONE", f"{gov_races}개 주"),
 ("6","각 주별 데이터센터 현황","NOT_STARTED",
  f"프로젝트 원장 {counts['dc_project']}건 · 벤더 집계 {counts['dc_vendor_count']}행"),
 ("7","데이터센터 규모 Top 20 주","NOT_STARTED","6번 선행 필요"),
 ("8","영향 Top 10 주","NOT_STARTED","7번 선행 필요"),
 ("9","정치인 정책 비교표","PARTIAL",
  f"{counts['politician_dc_position']}명 / {pos_states}개 주 · 근거 {counts['position_evidence']}건"),
 ("10","Data Center Political Risk Score","NOT_STARTED",
  f"dc_election_risk {counts['dc_election_risk']}행"),
 ("11","Election Scenario Analysis","NOT_STARTED", f"scenario {counts['scenario']}행"),
 ("12","자동 업데이트 구조","DONE", f"change_log {counts['change_log']}건 · 트리거 자동 적재"),
]
done = sum(1 for d in DELIVERABLES if d[2] == "DONE")
partial = sum(1 for d in DELIVERABLES if d[2] == "PARTIAL")

# ---------------------------------------------------------------- 스키마 덤프
schema = rows("""SELECT type, name, sql FROM sqlite_master
                 WHERE name NOT LIKE 'sqlite_%' AND sql IS NOT NULL
                 ORDER BY CASE type WHEN 'table' THEN 1 WHEN 'view' THEN 2
                          WHEN 'trigger' THEN 3 ELSE 4 END, name""")

def cols(t):
    return [r["name"] for r in rows(f"PRAGMA table_info({t})")]

# ---------------------------------------------------------------- 가중치
W = {}
for r in rows("SELECT scheme, component, weight, rationale FROM scoring_weight ORDER BY scheme"):
    W.setdefault(r["scheme"], []).append(r)
BIND = rows("SELECT binding_code,label_ko,weight,note FROM binding_force ORDER BY weight DESC")
SCOPE = rows("SELECT scope_code,label_ko,weight,note FROM regulation_scope ORDER BY weight DESC")
OFF = rows("SELECT office,weight,note FROM office_power ORDER BY weight DESC")

LEV = rows("""SELECT state_code,full_name,party,office,leverage_score,support_score,
              top_binding_label,top_scope_label,confidence_level,evidence_count
              FROM v_effective_position ORDER BY leverage_score DESC""")
SRC = rows("SELECT tier,publisher,title,url,published_date,is_primary FROM source ORDER BY tier,publisher")
CONF = rows("SELECT target_field,value_a,value_b,resolution,note FROM source_conflict")

# ================================================================ 문서 작성
L = []
A = L.append

A(f"""# HANDOFF — U.S. Midterm × Data Center Political Risk Tracker

**이 파일은 자동 생성됩니다.** `python3 scripts/11_build_handoff.py`
수치는 전부 `data/tracker.db`에서 직접 읽습니다. 손으로 고치지 마세요.

| | |
|---|---|
| 데이터 기준일 | {TODAY} |
| 선거일 | 2026-11-03 (D-{DDAY}) |
| 요구 산출물 진행 | 완료 {done}/12 · 부분 {partial}/12 |
| 저장소 | https://github.com/uouohmk/dc_01 |
| 대시보드 | https://uouohmk.github.io/dc_01/ |

---

## 0. 이 프로젝트가 하는 일

선거가 특정 산업에 미칠 규제 리스크를 추적한다. 두 가지 통념을 구조적으로 배제하는 것이 설계 목표다.

1. **정당으로 입장을 추론하는 것** — 실제 데이터에서 반복적으로 깨진다
2. **말의 강도로 순위를 매기는 것** — 광고에서 가장 세게 말하는 후보와 실제로 규제에 서명한 후보는 다르다

핵심 산출물은 후보별 **규제 레버리지** = 구속력 × 범위 × 직위권한.

---

## 1. 현재 완성도 (정직한 감사)

| # | 산출물 | 상태 | 실측 |
|---|---|---|---|""")
for n, name, st, note in DELIVERABLES:
    mark = {"DONE":"완료","PARTIAL":"**부분**","NOT_STARTED":"**미착수**"}[st]
    A(f"| {n} | {name} | {mark} | {note} |")

A(f"""
### 진행이 막힌 지점

`dc_project`가 비어 있어 사슬이 끊겨 있다.

```
STEP 4 데이터센터 프로젝트 원장  ← 여기가 비어 있음
   ↓
STEP 5 Top 20 주 선정 (v_dc_exposure_score)
   ↓
STEP 7 리스크 점수 (dc_election_risk)
   ↓
STEP 11 시나리오 분석 (scenario)
```

STEP 6(정치인 입장)만 선행돼 있어 대시보드의 "데이터센터 규모" 모드가 전 주 빗금이고
리스크 점수가 미산출 상태다. **다음 작업은 반드시 STEP 4부터 시작해야 한다.**

### 테이블별 적재 현황

| 테이블 | 행 |
|---|---|""")
for t in TABLES:
    flag = " ← 비어 있음" if counts[t] == 0 else ""
    A(f"| `{t}` | {counts[t]}{flag} |")

A(f"""
여론조사 커버리지: {polled}/{total_races} 레이스 (공백 {total_races-polled})

---

## 2. 절대 원칙 4개

자동화하는 쪽에서 이 넷을 깨면 프로젝트의 의미가 사라진다.

### P1. 사실과 분석을 물리적으로 분리
Fact 레이어(선거 일정·후보·발언·법령)에는 분석값을 넣지 않는다.
파생값은 `data_type='AI Analysis'` CHECK가 걸린 테이블 또는 `v_` 뷰에만 존재한다.
UI에서 배지로 구분 표시한다.

### P2. 모르는 값은 0이 아니다
`NULL` + `status_code` (`UNKNOWN` / `NOT_AVAILABLE` / `NO_CLEAR_PUBLIC_POSITION` /
`DISPUTED` / `NOT_YET_COLLECTED` / `INSUFFICIENT_DATA`).
점수 계산 시 NULL은 **분모에서 제외**하고 커버리지를 함께 출력한다.

### P3. 근거 없이는 점수를 넣을 수 없다
DB 트리거로 강제된다. `evidence_type` 허용값에 **"정당 소속"이 존재하지 않는다.**

```sql
CREATE TRIGGER trg_axis_requires_evidence
BEFORE INSERT ON position_axis_score FOR EACH ROW
WHEN NEW.axis_score IS NOT NULL
     AND (SELECT COUNT(*) FROM position_evidence WHERE position_id=NEW.position_id)=0
BEGIN SELECT RAISE(ABORT,'P3 violation'); END;
```

### P4. 정의가 다른 수치를 합치지 않는다
벤더별 병렬 저장, 순위는 단일 벤더 내부에서만 계산.
실측: "미국 데이터센터 수"가 출처별 1,208 / 3,698 / 4,713 / 7,759 — 최대 6배 차이.

---

## 3. 스코어링 모델 (전부 DB 테이블에 있음)

### 3-1. 구속력 `binding_force`

| 코드 | 라벨 | 가중치 | 비고 |
|---|---|---|---|""")
for r in BIND:
    A(f"| `{r['binding_code']}` | {r['label_ko']} | {r['weight']:.2f} | {r['note'] or ''} |")

A("""
### 3-2. 범위 `regulation_scope`

| 코드 | 라벨 | 가중치 | 비고 |
|---|---|---|---|""")
for r in SCOPE:
    A(f"| `{r['scope_code']}` | {r['label_ko']} | {r['weight']:.2f} | {r['note'] or ''} |")

A("""
### 3-3. 직위 권한 `office_power`

| 직위 | 가중치 | 근거 |
|---|---|---|""")
for r in OFF:
    A(f"| {r['office']} | {r['weight']:.2f} | {r['note']} |")

A("""
### 3-4. 5개 축 가중치 `scoring_weight`

| 스킴 | 컴포넌트 | 가중치 |
|---|---|---|""")
for scheme in ["SUPPORT_SCORE","EXPOSURE","ELECTION_RISK","DC_POLICY_RISK","OVERALL"]:
    for r in W.get(scheme, []):
        A(f"| {scheme} | `{r['component']}` | {r['weight']:.2f} |")

A("""
### 3-5. 계산식

```
레버리지     = MAX(구속력 × 범위)_규제근거 × 직위권한 × 100
               → 근거 1건만 있어도 산출된다. 항상 표시.

방향 종합    = Σ(축점수 × 가중치) / Σ(가중치)   [NULL 축은 분모에서 제외]
               → 5개 축 중 3개 이상 확보된 경우에만 산출. 아니면 NULL.

실효 영향치  = 방향 종합 × MAX(구속력 × 범위) × 직위권한

노출도       = 0.40×N(운영MW) + 0.30×N(건설중MW) + 0.20×N(계획MW) + 0.10×N(시설수)
               N(x) = 100 × log(1+x) / log(1+max)
               ※ 단순 max 정규화는 쓰지 않는다. 최대값 주가 나머지를 뭉개버린다.
```

**두 지표를 반드시 분리한다.** 방향 종합은 데이터 요구량이 커서 절반이 비게 되는데
레버리지는 근거 1건으로도 나온다. 하나로 합치면 순위 자체가 사라진다.

---

## 4. 현재 레버리지 산출 결과

| 주 | 이름 | 당 | 직위 | 레버리지 | 방향 | 최고 근거 | 신뢰도 |
|---|---|---|---|---|---|---|---|""")
for r in LEV:
    d = f"{r['support_score']:.0f}" if r['support_score'] is not None else "미확정"
    off = {"Governor":"주지사","U.S. Senate":"연방상원"}.get(r["office"], r["office"])
    A(f"| {r['state_code']} | {r['full_name']} | {r['party']} | {off} | "
      f"**{r['leverage_score']:.1f}** | {d} | {r['top_binding_label']} / {r['top_scope_label']} | "
      f"{r['confidence_level']} |")

A(f"""
`v_bipartisan_convergence` — 양당 후보 support_score가 모두 음수인 주.
이 플래그가 켜지면 **선거 결과와 무관하게 규제가 진행되므로** 시나리오 A/B/C가 수렴한다.
선거 결과를 맞히는 것보다 이 플래그를 찾는 게 리스크 판단에 유용하다.

---

## 5. 파일 구조와 실행 순서

```
index.html              단일 파일 대시보드 (외부 의존성: 폰트 CDN만)
data/tracker.db         SQLite 원본
data/01_schema.sql      스키마 DDL
scripts/
  02_seed_step2_3.py    최초 시드 — 50개 주 · 상원 35 · 주지사 36
  04_positions.py       입장 초기 적재 + 3차원 스키마 확장 + v_effective_position
  06_update_0829.py     등급 · 여론조사 · 데이터센터 여론
  07_update_0830.py     NY 모라토리엄 · ME 후보 교체 · PJM 요금
  08_update_0831.py     OR 쟁점 · 근거 수정
  09_update_0901.py     여론조사 공백 뷰
  10_update_0902.py     노출도 상위 주 조사
  03_build_dashboard.py 대시보드 생성   ← 항상 갱신 스크립트 뒤
  05_cards.py           카드뉴스 생성
  11_build_handoff.py   이 문서 생성   ← 항상 마지막
cards/*.png             1080×1350
```

### 실행

```bash
rm -f data/tracker.db
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
```

`./update.sh` 가 위 순서를 그대로 실행하고 커밋·푸시까지 한다.

### 환경 주의

- SQLite에 `log()`가 없다. 파이썬에서 등록해야 `v_dc_exposure_score`가 동작한다.
  `con.create_function('log',1,lambda x: math.log(x) if x and x>0 else None)`
- 카드뉴스는 `/usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc` **index=1**(KR)을 쓴다.
- PostgreSQL 이식 시: `log(x)` → `ln(x)`, `INTEGER PRIMARY KEY` → IDENTITY,
  트리거는 PL/pgSQL로 재작성.

---

## 6. 갱신 프로토콜 (자동화 시 반드시 지킬 것)

### 6-1. 기존 스크립트를 수정하지 않는다
날짜별 스크립트를 새로 만들어 누적한다. `race_rating` 등은 **날짜별 이력이 쌓여야**
등급 변화 추적이 된다. 기존 파일을 고치면 이전 스냅샷이 사라진다.

### 6-2. 매 갱신마다 클린 재현 검증
```bash
rm -f data/tracker.db && for f in scripts/0*.py scripts/1*.py; do python3 $f || exit 1; done
```
대화 중 임시로 만든 뷰가 스크립트에 반영되지 않는 사고가 실제로 발생했다.

### 6-3. 매 갱신마다 확인할 4가지
1. **기존 기록의 구속력이 과소평가돼 있지 않은가** — "발표 예정"으로 적은 게 이미 성립된 법률인 사례 있었음(Kotek, 0.25 → 1.00)
2. **후보가 바뀌지 않았는가** — 사퇴·교체를 5주간 놓친 사고 있었음(ME)
3. **새 근거로 축이 늘어나지 않는가** — 축 1개→4개가 되면 방향 종합이 처음 산출됨(Rogers)
4. **분류가 뒤집히지 않는가** — 공격받은 후보가 방어 법안을 내면 Supportive → Mixed(Husted)

### 6-4. 추적 이벤트 (`change_log.event_type`)
`NEW_CANDIDATE` `CANDIDATE_WITHDRAWAL` `POLLING_CHANGE` `RACE_RATING_CHANGE`
`GOVERNOR_ELECTION_CHANGE` `NEW_DC_ANNOUNCEMENT` `DC_CANCELLATION` `NEW_LEGISLATION`
`TAX_INCENTIVE_CHANGE` `ELECTRICITY_RATE_CHANGE` `COMMUNITY_OPPOSITION`
`WATER_REGULATION` `DC_STAGE_TRANSITION`

---

## 7. 남은 작업 — 실행 지침

### STEP 4 — 데이터센터 프로젝트 원장 (최우선, 사슬의 첫 고리)

`dc_project`를 채운다. 그레인은 **프로젝트 1건**.

필수 컬럼: `state_code` `project_name` `primary_operator` `stage_code` `stage_as_of`
`capacity_mw` `capacity_basis` `source_id`

`stage_code`는 5단계로 분리한다.
`OPERATIONAL` / `UNDER_CONSTRUCTION` / `APPROVED` / `PLANNED` / `ANNOUNCED`

`capacity_basis`를 반드시 기록한다. `IT_LOAD` / `GROSS` / `UTILITY_CONTRACT` / `UNKNOWN`.
IT 부하와 계약 용량을 섞으면 MW 합계가 무의미해진다.

수집 우선순위: 하이퍼스케일 사업자 공식 발표(Tier 7) → 주 PUC 접속 신청(Tier 2) →
지역 언론 인허가 보도(Tier 9) → 산업 리서치(Tier 8)

**대안 경로:** 프로젝트 단위가 과중하면 `dc_vendor_count`를 50개 주로 먼저 채워
Top 20과 노출도를 산출할 수 있다. 단 프로젝트 단위 분석과 상태 전이 추적은 포기하게 된다.

### STEP 5 — Top 20 주
`v_dc_exposure_score`가 자동 계산한다. STEP 4만 끝나면 코드 작업 없음.
단, 단일 벤더 내부에서만 순위를 낸다(P4).

### STEP 7 — 리스크 점수
`dc_election_risk`를 채운다. 계산식은 `scoring_weight`의 `ELECTION_RISK` /
`DC_POLICY_RISK` / `OVERALL` 스킴에 이미 있다.
`coverage_pct` 60 미만이면 점수를 내지 말고 `INSUFFICIENT_DATA`.

### STEP 11 — 시나리오
`scenario` 테이블. `driver_evidence_ids`가 비면 트리거가 INSERT를 막는다.
근거가 없으면 `overall_risk_direction='INSUFFICIENT_EVIDENCE'`로 저장.
**정당 고정관념으로 시나리오를 쓰지 말 것.** PA는 양당 후보가 모두 규제 방향이라
Scenario A와 B의 결과가 수렴한다.

### 하원 435석
전체를 넣을지 접전 지역구만 넣을지 결정 필요.
전체는 `election_race`에 435행 + 후보 900명 이상. 접전만이면 Cook Toss-up 18석 + Lean.

### 주의회 의석 (`state_political_structure`)
현재 0/50. `political_control`(Trifecta 판정)이 여기 의존한다.
출처: Ballotpedia, Plural, NCSL. 네브래스카는 단원제·비당파라 별도 처리 필요.

---

## 8. 함정 (실제로 걸린 것들)

| # | 함정 | 대응 |
|---|---|---|
| 1 | 집계 사이트 발췌에 이전 사이클 대진이 섞여 나옴 | 연도·후보명 대조 필수 |
| 2 | 실존하지 않는 대진의 여론조사 유통 (GA: Kemp는 후보 아님) | 후보 명단과 대조 후 적재 |
| 3 | 같은 지표의 정의 불일치 (최대 6배) | 벤더별 병렬 저장 |
| 4 | 요약 수치의 내부 정합성 붕괴 (공화 방어 22 vs 23) | `source_conflict`에 양쪽 기록 |
| 5 | 날짜 없는 등급 | 적재하지 않고 비워둠 |
| 6 | 후보 교체 누락 (5주간 오류) | 갱신마다 후보 상태 재확인 |
| 7 | JS 렌더링 페이지는 본문이 비어서 옴 | 검색 발췌로 우회 |
| 8 | 유료벽 (Cook 원문) | 집계 사이트의 변동 기록으로 대체 |

### 검색 인프라에 대한 정확한 서술
웹 검색과 웹 페치 두 가지만 사용했다. **어떤 검색엔진 사업자를 경유하는지는 확인할 수 없다.**
페치는 직전 검색 결과에 등장한 URL만 열린다.
코드 실행 환경 네트워크는 화이트리스트라 `api.open.fec.gov` 등 외부 API는 막혀 있다.
선거자금 자동 수집은 로컬에서 실행해야 한다.

**지역 언론이 전국 언론보다 유용했다.** 후보의 구체적 정책 문구는 주 단위 매체에만 있다.

---

## 9. 출처 대장 ({len(SRC)}건)

⭐ = 1차 출처

| Tier | 발행처 | 자료 | 일자 |
|---|---|---|---|""")
for r in SRC:
    star = " ⭐" if r["is_primary"] else ""
    A(f"| {r['tier']} | {r['publisher']}{star} | [{r['title']}]({r['url']}) | {r['published_date'] or '—'} |")

if CONF:
    A("\n### 기록된 출처 충돌\n")
    A("| 필드 | A | B | 판정 |")
    A("|---|---|---|---|")
    for r in CONF:
        A(f"| {r['target_field']} | {r['value_a']} | {r['value_b']} | {r['resolution']} |")

A("""
---

## 10. 검증 쿼리

```sql
-- 수집 진행률
SELECT * FROM v_coverage_audit;

-- 레버리지 순위
SELECT state_code, full_name, party, leverage_score, support_score,
       top_binding_label, top_scope_label
FROM v_effective_position ORDER BY leverage_score DESC;

-- 근거 없는 점수가 있는가 (0이어야 정상)
SELECT COUNT(*) FROM position_axis_score a
WHERE a.axis_score IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM position_evidence e WHERE e.position_id=a.position_id);

-- 특정 근거의 출처 추적
SELECT e.summary, e.binding_code, e.scope_code, e.direction,
       s.publisher, s.url, e.evidence_date
FROM position_evidence e JOIN source s ON s.source_id=e.source_id
ORDER BY e.evidence_date DESC;

-- 양당 수렴 주
SELECT * FROM v_bipartisan_convergence WHERE bipartisan_convergence_flag=1;

-- 여론조사 사각지대
SELECT * FROM v_polling_blind_spot WHERE blind_spot_flag=1;

-- 최근 변동
SELECT changed_at, event_type, state_code, note
FROM change_log ORDER BY changed_at DESC LIMIT 20;
```

---

## 11. 다른 산업으로 이식

바꿀 것은 **5개 축과 `policy_category` 12행뿐**이다. 나머지 구조는 그대로 쓴다.

| 산업 | 5개 축 |
|---|---|
| 데이터센터 | 산업성장 · 전력 · 전기요금 · 물사용 · 세제혜택 |
| 반도체 | 산업성장 · 수출통제 · 보조금 · 인력비자 · 환경규제 |
| 제약 | 신약승인 · 약가규제 · 특허 · 보험수가 · 리베이트 |
| 암호화폐 | 산업성장 · 증권성분류 · 스테이블코인 · 조세 · 자금세탁 |

`position_axis_score.axis_code`의 CHECK 제약과 `scoring_weight`의 `SUPPORT_SCORE` 스킴을 교체한다.
`binding_force` · `regulation_scope` · `office_power`는 산업과 무관하므로 그대로 둔다.

---

## 12. Antigravity 에이전트 연동

| 파일 | 층 | 역할 |
|---|---|---|
| `AGENTS.md` | Rule | 절대 원칙 · 함정 5가지 · 커밋 전 검증 |
| `.agents/skills/poll-update/SKILL.md` | Skill | 여론조사·등급 수집 |
| `.agents/skills/policy-update/SKILL.md` | Skill | 후보 정책 입장 수집 |
| `.agents/workflows/weekly-tracker-update.md` | Workflow | 주간 갱신 절차 |
| `scripts/99_validate.py` | 게이트 | 원칙 위반 시 exit 1 |

방어 3겹: 지시(AGENTS.md) → 코드(DB 트리거) → 검증(99_validate.py).
에이전트가 지시를 무시해도 트리거가 막고, 트리거를 피해가도 검증이 잡는다.
설정 절차는 `AUTOMATION.md` 참조.

---

## 13. 자동화하는 쪽에 주는 지시문

이 프로젝트를 이어받는 에이전트·팀에게 그대로 전달할 수 있는 규칙.

```
1. 근거 없이 점수를 만들지 마라. DB 트리거가 막지만, 트리거를 우회하지도 마라.
2. 정당 소속을 입장 추론의 근거로 쓰지 마라. evidence_type에 그 값은 없다.
3. 모르면 NULL + status_code로 남겨라. 0으로 채우지 마라.
4. 정의가 다른 수치를 합치지 마라. 벤더별로 나눠 저장하고 벤더 내부에서만 비교하라.
5. 기존 스크립트를 수정하지 마라. 날짜별 파일을 새로 만들어라.
6. 갱신 후 반드시 DB를 지우고 전체 파이프라인을 다시 돌려 검증하라.
7. 등급·조사는 날짜가 특정되지 않으면 적재하지 마라.
8. 후보 명단과 대조하지 않은 여론조사는 적재하지 마라.
9. Fact와 분석을 같은 컬럼에 넣지 마라.
10. 이 문서는 손으로 고치지 말고 11_build_handoff.py로 재생성하라.
```
""")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
con.close()
print(f"{OUT} 생성 — {len(''.join(L)):,}자 · 출처 {len(SRC)}건 · 후보 {len(LEV)}명")
print(f"진행: 완료 {done}/12 · 부분 {partial}/12 · 미착수 {12-done-partial}/12")
