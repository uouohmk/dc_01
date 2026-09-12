# HANDOFF — U.S. Midterm × Data Center Political Risk Tracker

**이 파일은 자동 생성됩니다.** `python3 scripts/11_build_handoff.py`
수치는 전부 `data/tracker.db`에서 직접 읽습니다. 손으로 고치지 마세요.

| | |
|---|---|
| 데이터 기준일 | 2026-09-10 |
| 선거일 | 2026-11-03 (D-54) |
| 요구 산출물 진행 | 완료 4/12 · 부분 2/12 |
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
|---|---|---|---|
| 1 | 전체 데이터베이스 스키마 | 완료 | 20+ 테이블 · 9 뷰 · 4 트리거 |
| 2 | 50개 주 기본 데이터 테이블 | **부분** | 주지사·연방의석 50/50 · 주의회 의석 0/50 · 정당통제 판정 0/50 |
| 3 | 2026 상원 선거 대상 의석 | 완료 | 35석 (정규 33 + 보궐 2) |
| 4 | 2026 하원 선거 전체 구조 | **미착수** | 0/435 |
| 5 | 2026 주지사 선거 대상 주 | 완료 | 36개 주 |
| 6 | 각 주별 데이터센터 현황 | **미착수** | 프로젝트 원장 0건 · 벤더 집계 8행 |
| 7 | 데이터센터 규모 Top 20 주 | **미착수** | 6번 선행 필요 |
| 8 | 영향 Top 10 주 | **미착수** | 7번 선행 필요 |
| 9 | 정치인 정책 비교표 | **부분** | 16명 / 7개 주 · 근거 46건 |
| 10 | Data Center Political Risk Score | **미착수** | dc_election_risk 0행 |
| 11 | Election Scenario Analysis | **미착수** | scenario 0행 |
| 12 | 자동 업데이트 구조 | 완료 | change_log 48건 · 트리거 자동 적재 |

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
|---|---|
| `source` | 61 |
| `state_political_structure` | 50 |
| `election_race` | 71 |
| `candidate` | 123 |
| `race_rating` | 22 |
| `polling` | 29 |
| `governor_race_detail` | 36 |
| `politician` | 124 |
| `politician_dc_position` | 16 |
| `position_evidence` | 46 |
| `position_axis_score` | 80 |
| `dc_project` | 0 ← 비어 있음 |
| `dc_vendor_count` | 8 |
| `state_dc_context` | 15 |
| `dc_public_opinion` | 17 |
| `dc_election_risk` | 0 ← 비어 있음 |
| `scenario` | 0 ← 비어 있음 |
| `grid_capacity_price` | 4 |
| `change_log` | 48 |
| `source_conflict` | 4 |

여론조사 커버리지: 11/73 레이스 (공백 62)

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
|---|---|---|---|
| `SIGNED_LAW` | 법률 서명·공포 | 1.00 | 이미 발효 |
| `SIGNED_EO` | 행정명령 서명 | 0.95 | 즉시 효력, 후임자가 뒤집을 수 있음 |
| `EXEC_DIRECTIVE` | 규제기관 지시 | 0.85 | 집행은 기관 재량 |
| `VOTE_RECORD` | 표결 기록 | 0.70 | 실제 행동이나 과거형 |
| `BILL_FILED` | 법안 발의·공동발의 | 0.60 | 통과 여부 불확실 |
| `POLICY_PLAN` | 공식 정책안 발표 | 0.45 | 문서화됐으나 미집행 |
| `CAMPAIGN_PROMISE` | 선거 공약 | 0.40 | 당선 전제 |
| `PUBLIC_STATEMENT` | 공개 발언 | 0.25 | 구속력 없음 |
| `CAMPAIGN_AD` | 선거 광고 | 0.20 | 수사(rhetoric) 중심 |

### 3-2. 범위 `regulation_scope`

| 코드 | 라벨 | 가중치 | 비고 |
|---|---|---|---|
| `NEW_TOTAL` | 신규 전면 중단 | 1.00 | 모라토리엄 |
| `EXISTING_INCLUDED` | 기존 시설 포함 규제 | 0.90 | 소급 적용 |
| `NEW_CONDITIONAL` | 신규 조건부 허용 | 0.75 | 감사·심사 통과 시 허용 |
| `SITING_BAN` | 입지 제한 | 0.70 | 특정 지역 금지 |
| `LOCAL_CONSENT` | 지역 동의 의무 | 0.65 | 사실상 거부권 |
| `INCENTIVE_REPEAL` | 세제혜택 폐지 | 0.60 | 수익성 훼손, 건설은 가능 |
| `COST_ALLOCATION` | 전력비용 부담 배분 | 0.50 | 짓되 비용을 내라 |
| `DISCLOSURE` | 사용량 공개 의무 | 0.25 | 투명성만 |

### 3-3. 직위 권한 `office_power`

| 직위 | 가중치 | 근거 |
|---|---|---|
| Governor | 1.00 | 행정명령·거부권·규제기관 지시 가능 |
| State Senate | 0.70 | 주 인허가·세제 입법권 |
| State House | 0.70 | 주 인허가·세제 입법권 |
| U.S. Senate | 0.55 | 주 인허가 직접 권한 없음. 연방 기준·세법 경유 |
| U.S. House | 0.45 | 상동, 개별 영향력 더 낮음 |

### 3-4. 5개 축 가중치 `scoring_weight`

| 스킴 | 컴포넌트 | 가중치 |
|---|---|---|
| SUPPORT_SCORE | `GROWTH` | 0.30 |
| SUPPORT_SCORE | `POWER` | 0.15 |
| SUPPORT_SCORE | `RATES` | 0.25 |
| SUPPORT_SCORE | `TAX` | 0.20 |
| SUPPORT_SCORE | `WATER` | 0.10 |
| EXPOSURE | `FACILITY_COUNT` | 0.10 |
| EXPOSURE | `OPERATIONAL_MW` | 0.40 |
| EXPOSURE | `PLANNED_MW` | 0.20 |
| EXPOSURE | `UNDER_CONSTRUCTION_MW` | 0.30 |
| ELECTION_RISK | `COMPETITIVE_RATIO` | 0.30 |
| ELECTION_RISK | `GOV_FLIP` | 0.25 |
| ELECTION_RISK | `OPEN_SEAT_RATIO` | 0.15 |
| ELECTION_RISK | `POLL_VOLATILITY` | 0.10 |
| ELECTION_RISK | `TRIFECTA_BREAK` | 0.20 |
| DC_POLICY_RISK | `CANDIDATE_STANCE` | 0.25 |
| DC_POLICY_RISK | `COMMUNITY_OPPOSITION` | 0.15 |
| DC_POLICY_RISK | `GRID_STRESS` | 0.20 |
| DC_POLICY_RISK | `REGULATORY_PIPELINE` | 0.15 |
| DC_POLICY_RISK | `TAX_INCENTIVE_RISK` | 0.15 |
| DC_POLICY_RISK | `WATER_STRESS` | 0.10 |
| OVERALL | `DC_POLICY_RISK` | 0.55 |
| OVERALL | `ELECTION_RISK` | 0.45 |

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
|---|---|---|---|---|---|---|---|
| NY | Kathy Hochul | D | 주지사 | **95.0** | -55 | 행정명령 서명 / 신규 전면 중단 | High |
| PA | Josh Shapiro | D | 주지사 | **71.2** | -50 | 행정명령 서명 / 신규 조건부 허용 | High |
| TX | Greg Abbott | R | 주지사 | **63.7** | -39 | 규제기관 지시 / 신규 조건부 허용 | High |
| OR | Tina Kotek | D | 주지사 | **60.0** | -44 | 법률 서명·공포 / 신규 조건부 허용 | High |
| TX | Gina Hinojosa | D | 주지사 | **40.0** | -71 | 선거 공약 / 신규 전면 중단 | High |
| PA | Stacy Garrity | R | 주지사 | **40.0** | 미확정 | 선거 공약 / 신규 전면 중단 | Medium |
| OH | Amy Acton | D | 주지사 | **33.8** | 미확정 | 공식 정책안 발표 / 신규 조건부 허용 | Medium |
| FL | Byron Donalds | R | 주지사 | **30.0** | 미확정 | 선거 공약 / 신규 조건부 허용 | Low |
| OH | Vivek Ramaswamy | R | 주지사 | **25.0** | 미확정 | 공개 발언 / 신규 전면 중단 | Medium |
| MI | Mike Rogers | R | 연방상원 | **22.0** | -63 | 선거 공약 / 신규 전면 중단 | High |
| MI | Abdul El-Sayed | D | 연방상원 | **22.0** | 미확정 | 선거 공약 / 신규 전면 중단 | Medium |
| TX | Ken Paxton | R | 연방상원 | **17.3** | -51 | 공식 정책안 발표 / 입지 제한 | High |
| OH | Jon Husted | R | 연방상원 | **16.5** | 39 | 법안 발의·공동발의 / 전력비용 부담 배분 | High |
| OR | Christine Drazan | R | 주지사 | **16.3** | -5 | 공개 발언 / 지역 동의 의무 | High |
| TX | James Talarico | D | 연방상원 | **16.1** | -64 | 공식 정책안 발표 / 지역 동의 의무 | High |
| OH | Sherrod Brown | D | 연방상원 | **11.0** | 미확정 | 선거 광고 / 신규 전면 중단 | Low |

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

## 9. 출처 대장 (61건)

⭐ = 1차 출처

| Tier | 발행처 | 자료 | 일자 |
|---|---|---|---|
| 1 | Maine Democratic Party ⭐ | [Maine Senate Replacement Nomination Process](https://mainedems.org/senate-race/) | 2026-07-25 |
| 1 | U.S. Senate ⭐ | [Class II - Terms Expiring 2027](https://www.senate.gov/senators/Class_II.htm) | — |
| 2 | New York State Governor's Office ⭐ | [Executive Order No. 62 — Temporary Moratorium on Data Centers](https://www.governor.ny.gov/executive-order/no-62-establishing-temporary-moratorium-data-centers-new-york-while-state-develops) | 2026-07-14 |
| 5 | NY State Legislature | [Responsible Data Center Development Act (S.10642/A.11560)](https://hselaw.com/news-and-information/legalcurrents/data-center-development-in-new-york-faces-immediate-pause-under-executive-order-62/) | 2026-06-30 |
| 6 | UT / Texas Politics Project ⭐ | [August 2026 Texas statewide poll (n=1200 RV)](https://texaspolitics.utexas.edu/blog/new-ut-texas-politics-project-poll-finds-talarico-leading-paxton-abbott-leading-hinojosa-continued-resistance-to-data-centers-2) | 2026-08-24 |
| 8 | Alaska Survey Research | [Alaska Senate poll, 1371 LV](https://www.newsweek.com/democrats-chances-of-flipping-the-senate-75-days-to-midterms-polls-12347504) | 2026-08-19 |
| 8 | Aterio | [US Data Center Database](https://www.aterio.io/insights/us-data-centers) | 2026-08-26 |
| 8 | Cook Political Report ⭐ | [2026 Senate Race Ratings](https://www.cookpolitical.com/ratings/senate-race-ratings) | 2026-08-20 |
| 8 | Data for Progress | [Alaska Senate poll, 578 LV](https://www.newsweek.com/democrats-chances-of-flipping-the-senate-75-days-to-midterms-polls-12347504) | 2026-08-19 |
| 8 | Decision Desk HQ | [2026 Senate polling averages](https://decisiondeskhq.substack.com/p/el-sayed-rogers-michigan-senate-trump-approval-generic-ballot-2026-midterms) | 2026-08-20 |
| 8 | Detroit News / WDIV / Glengariff Group ⭐ | [Michigan statewide poll, 600 LV](https://www.clickondetroit.com/news/local/2026/09/08/poll-which-us-senate-candidates-are-most-favorable-to-michigan-voters/) | 2026-09-08 |
| 8 | EPIC-MRA | [Michigan Senate poll](https://www.pollsmax.com/senate/michigan/) | 2026-08-28 |
| 8 | Emerson College Polling ⭐ | [Ohio 2026 poll — Senate & Governor](https://emersoncollegepolling.com/ohio-2026-poll-democrats-make-gains-in-races-for-governor-and-us-senate/) | 2025-12-17 |
| 8 | Emerson College Polling / Nexstar ⭐ | [Texas 2026 poll](https://emersoncollegepolling.com/texas-2026-poll-paxton-and-talarico/) | 2026-08-10 |
| 8 | Inside Elections ⭐ | [2026 Senate ratings](http://insideelections.com/ratings/senate) | 2026-08-06 |
| 8 | New York Times / Siena College | [Alaska Senate poll, 593 LV](https://www.newsweek.com/democrats-chances-of-flipping-the-senate-75-days-to-midterms-polls-12347504) | 2026-08-19 |
| 8 | Overton Insights / TPPF ⭐ | [Texas poll, 1167 LV](https://overtoninsights.com/poll/september-2026/) | 2026-09-07 |
| 8 | Pollsmax | [2026 Kentucky Senate polling average](https://www.pollsmax.com/senate/kentucky/) | 2026-08-01 |
| 8 | Pollsmax | [2026 Michigan Senate polling average (21 polls)](https://www.pollsmax.com/senate/michigan/) | 2026-08-31 |
| 8 | Pollsmax | [Michigan Senate polling average (24건)](https://www.pollsmax.com/senate/michigan/) | 2026-09-09 |
| 8 | Sabato's Crystal Ball ⭐ | [2026 Senate ratings](https://centerforpolitics.org/crystalball/2026-senate/) | 2026-08-26 |
| 8 | Sabato's Crystal Ball ⭐ | [2026 Rating Changes](https://centerforpolitics.org/crystalball/2026-rating-changes/) | 2026-08-26 |
| 8 | Wedgewood Polls | [Ohio Senate & Governor poll](https://thehill.com/homenews/campaign/6031596-brown-acton-lead-ohio-polls/) | 2026-08-14 |
| 8 | datacenterbans.com | [US Data Center Policy Landscape — end of August 2026](https://www.datacenterbans.com/) | 2026-08-28 |
| 8 | dcmap.us | [US Data Center Map](https://dcmap.us/) | 2026-02-20 |
| 9 | 270toWin | [2026 Senate Election / Cook ratings](https://www.270towin.com/2026-senate-election/cook-political-report-2026-senate) | 2026-08-20 |
| 9 | 270toWin | [2026 Governor Election forecasts](https://www.270towin.com/2026-governor-election-predictions/) | 2026-08-26 |
| 9 | 270toWin | [2026 Senate Election Forecast Maps](https://www.270towin.com/2026-senate-election-predictions/) | 2026-08-28 |
| 9 | 270toWin | [2026 Senate Polling by state — 폴링 없는 주 표기](https://www.270towin.com/content/2026-senate-polling) | 2026-08-31 |
| 9 | Axios | [Data center uproar scrambles the midterm election](https://www.axios.com/2026/08/20/data-center-uproar-2026-midterms) | 2026-08-20 |
| 9 | Brookings | [How rising electric rates could affect the 2026 midterms](https://www.brookings.edu/articles/how-rising-electric-rates-could-affect-the-2026-midterms) | 2026-03-20 |
| 9 | Brookings | [Why data centers are a top issue in the 2026 midterms](https://www.brookings.edu/articles/why-data-centers-are-a-top-issue-in-the-2026-midterms/) | 2026-08-25 |
| 9 | CBS Texas | [Data centers emerge as key issue in Texas politics](https://www.cbsnews.com/texas/news/data-centers-emerge-as-key-issue-in-texas-politics-where-candidates-for-governor-u-s-senate-stand/) | 2026-08-25 |
| 9 | CNBC | [AI data center outrage in ads and elections](https://www.cnbc.com/2026/08/20/ai-data-center-election-backlash.html) | 2026-08-20 |
| 9 | CNN | [Senate Democrats have 1 unpopular candidate. It's much worse for Republicans](https://www.cnn.com/2026/08/18/politics/republican-senate-candidates-unpopularity) | 2026-08-18 |
| 9 | Detroit News | [Republican U.S. Senate candidate backs one-year data center moratorium](https://www.detroitnews.com/story/news/politics/2026/08/20/data-center-politics-michigan-senate-mike-rogers-abdul-el-sayed/91385736007/) | 2026-08-20 |
| 9 | E&E News/Politico | [Texas governor talks tough on data centers, calls for clampdown](https://www.eenews.net/articles/texas-governor-talks-tough-on-data-centers-calls-for-clampdown/) | 2026-06-11 |
| 9 | Forbes | [Latest 2026 Senate Polls — El-Sayed leads Rogers by 4 in Michigan](https://www.forbes.com/sites/saradorn/2026/08/31/latest-2026-senate-polls-el-sayed-leads-rogers-by-4-points-in-michigan/) | 2026-08-31 |
| 9 | Fox News | [Ohio Senate poll — Beacon Research (D) / Shaw & Company (R)](https://www.foxnews.com/politics/fox-news-poll-economic-anxiety-candidate-concerns-define-ohio-senate-race) | 2026-08-12 |
| 9 | Fox News | [2026 Senate Power Rankings](https://www.foxnews.com/politics/fox-news-power-rankings-democrats-turn-left-black-voters-tap-brakes) | 2026-08-18 |
| 9 | Impact Research (D) | [Ohio governor survey, 800 LV](https://www.yahoo.com/news/articles/poll-ramaswamy-acton-dead-heat-221900719.html) | 2026-08-12 |
| 9 | KLCC / Oregon Capital Chronicle | [Data centers emerge as new flashpoint between Kotek, Drazan](https://www.klcc.org/politics-government/2026-08-31/data-centers-emerge-as-new-flashpoint-between-kotek-drazan-in-oregon-governors-race) | 2026-08-31 |
| 9 | KUT (NPR Austin) | [Texas leaders are divided on what to do about data centers](https://www.kut.org/energy-environment/2026-08-19/austin-tx-texas-data-centers-regulations-greg-abbott) | 2026-08-19 |
| 9 | NBC News | [Graham Platner officially withdraws from the Maine Senate race](https://www.nbcnews.com/politics/2026-election/graham-platner-officially-drops-maine-senate-race-rcna385842) | 2026-07-10 |
| 9 | NBC News | [Sununu and Pappas win New Hampshire Senate primaries](https://www.nbcnews.com/politics/2026-primary-elections/new-hampshire-senate-results) | 2026-09-08 |
| 9 | NPR | [Democrats in Maine formally nominate Troy Jackson](https://www.npr.org/2026/07/25/nx-s1-5902982/democrats-maine-senate-race) | 2026-07-25 |
| 9 | NPR | [With just a few primaries to go, the competitive Senate map keeps shifting](https://www.npr.org/2026/07/27/nx-s1-5907379/2026-midterm-election-senate-races) | 2026-07-27 |
| 9 | NPR | [Data centers a top issue in midterms for voters, candidates](https://www.npr.org/2026/08/08/g-s1-137853/data-centers-primaries-midterms) | 2026-08-08 |
| 9 | NPR | [Data centers are a political issue crossing party lines](https://www.npr.org/2026/08/08/g-s1-137853/data-centers-primaries-midterms) | 2026-08-08 |
| 9 | New Hampshire Public Radio | [Pappas, Sununu sweep to victory in U.S. Senate primaries](https://www.nhpr.org/politics/2026-09-08/pappas-sununu-win-senate-primaries-nh-newhampshire-elections-2026) | 2026-09-08 |
| 9 | Newsweek | [El-Sayed dealt polling blow in Michigan race against Rogers](https://www.newsweek.com/abdul-el-sayed-polling-blow-michigan-senate-mike-rogers-12421084) | 2026-09-09 |
| 9 | Philadelphia Inquirer | [The data center backlash bursts into the midterms](https://www.inquirer.com/politics/data-centers-ai-politics-votter-opposition-democrats-republicans-pivot-shapiro-20260823.html) | 2026-08-23 |
| 9 | Texas Tribune | [New Texas data center projects frozen until state audits them](https://www.texastribune.org/2026/08/03/texas-data-center-project-audit-greg-abbott/) | 2026-08-03 |
| 9 | The Hill | [Mike Rogers doubles down on push for data center moratorium](https://thehill.com/homenews/campaign/6043170-mike-rogers-data-center-pressure-michigan-senate-race/) | 2026-08-21 |
| 9 | The Hill | [Rising data center backlash shakes up midterm races](https://thehill.com/homenews/campaign/6044618-ai-data-center-backlash-michigan-ohio-pennsylvania/) | 2026-08-23 |
| 9 | The Hill / AARP | [Ohio Senate & Governor poll — Fabrizio Ward + Impact Research](https://thehill.com/homenews/campaign/5946710-ohio-voters-ramaswamy-husted/) | 2026-06-30 |
| 9 | The Hill / Texas Public Opinion Research | [Texas Senate & Governor poll (n=1000 LV)](https://thehill.com/homenews/campaign/6055357-texas-senate-poll-talarico-leading/) | 2026-08-28 |
| 9 | The Texan | [Abbott, Hinojosa spotlight data centers in gubernatorial campaigns](https://thetexan.news/elections/2026/gov-abbott-challenger-hinojosa-spotlight-data-centers-in-gubernatorial-campaigns/article_64c51f5d-db12-41e9-92ff-29643cbd3e93.html) | 2026-07-20 |
| 9 | The Texan | [New poll shows Texans split on Paxton and Talarico, opposed to data centers](https://thetexan.news/elections/2026/new-poll-shows-texans-split-on-paxton-and-talarico-opposed-to-flock-and-data-centers/article_45a2d21c-9c79-417e-b724-6070cfd03887.html) | 2026-09-02 |
| 9 | Wikipedia | [2026 United States Senate elections](https://en.wikipedia.org/wiki/2026_United_States_Senate_elections) | 2026-08-26 |
| 9 | Wikipedia | [2026 United States gubernatorial elections](https://en.wikipedia.org/wiki/2026_United_States_gubernatorial_elections) | 2026-08-26 |

### 기록된 출처 충돌

| 필드 | A | B | 판정 |
|---|---|---|---|
| total_count | 1330 (Aterio, 발표단계 포함) | 578 (dcmap, 전 상태 시설) | BOTH_VALID_DIFFERENT_DEFINITION |
| margin_d_minus_r | Kemp vs Ossoff (R+6, Club for Growth/WPA 내부조사) | 실제 대진은 Mike Collins vs Ossoff | PREFER_B |
| margin_d_minus_r | Chris Sununu(전 주지사) 53 - Pappas 44 가상대결 | 실제 공화당 후보는 John E. Sununu(전 상원의원) | PREFER_B |
| race_matchup | RealClearPolling 발췌: Brown vs Moreno / McCormick vs Casey / Hovde vs Baldwin / Rogers vs Slotkin | 모두 2024년 대진. 2026년 목록에 캐시가 섞여 노출됨 | PREFER_B |

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
