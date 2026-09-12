# U.S. Midterm Election × Data Center Political Risk Tracker
## STEP 1 — 데이터베이스 구조 및 전체 프로젝트 설계도

**문서 버전:** v1.0
**작성일:** 2026-08-27
**선거일까지:** 68일 (2026년 11월 3일)

---

## 0. 왜 이 프로젝트가 지금 유효한가 (검증된 전제)

설계에 들어가기 전, 프로젝트의 핵심 가설 — "데이터센터가 선거 변수가 된다" — 을 먼저 검증했다.
결론: **가설이 아니라 이미 발생한 사실이다.**

| 확인된 사실 | 출처 | 날짜 |
|---|---|---|
| 후보들의 데이터센터 관련 발언이 2024→2026 사이 긍정→부정으로 전환. 공화당이 민주당보다 더 부정적 | Brookings (WaPo 분석 인용) | 2026-08-25 |
| 3월 Gallup: 미국인 71%가 자기 지역 데이터센터 건설에 반대 | Gallup (2차 인용) | 2026-03 |
| PA 주지사 Shapiro(D), 데이터센터 개발자에게 전력비용 부담·지역승인 의무화 행정명령 서명 | The Hill / CNBC | 2026-08-18 |
| MI 공화당 상원 후보 Mike Rogers, 신규 데이터센터 1년 모라토리엄 지지 | 복수 언론 | 2026-08 |
| FL 공화당 주지사 후보 Byron Donalds, 데이터센터 규제 공약으로 예비선거 승리 | CNBC | 2026-08-18 |
| OH: Sherrod Brown(D)이 Husted(R)를 "데이터센터의 얼굴"로 공격하는 광고 집행 | Brookings / NPR | 2026-08 |
| NRSC가 AI 기업들에게 "데이터센터 반대가 정치적 부채가 되고 있다"고 경고 | 복수 언론 | 2026-08 |
| 28개 주에서 151건의 지역 모라토리엄이 발효 중 | ElectricChoice DC tracker | 2026-08 |

**설계적 함의 (매우 중요):**
이 이슈는 **정당 축으로 정렬되지 않는다.** 민주당 주지사가 규제를 걸고, 공화당 상원 후보가 모라토리엄을 지지한다.
→ 따라서 스키마는 **"정당 → 입장" 추론을 구조적으로 불가능하게** 만들어야 한다.
→ `politician_dc_position` 테이블은 **근거(evidence) 레코드 없이는 점수 입력이 불가능**하도록 설계했다 (§4 참조).

---

## 1. 아키텍처 개요

```
[L0] SOURCE LAYER      원문 URL / 스냅샷 / 취득일
        ↓
[L1] STAGING           벤더별 원시 데이터 (정의 불일치 그대로 보존)
        ↓
[L2] CORE (Fact)       사실만. 모든 행에 source_id 필수
        ↓
[L3] DERIVED (Analysis) 점수·시나리오. data_type='AI Analysis' 강제
        ↓
[L4] PRESENTATION      지도 / 주 상세 / 정치인 패널 (STEP 8)
```

**절대 규칙 1 — Fact/Analysis 분리**
L2에는 분석값을 저장하지 않는다. L3의 모든 산출물은 `data_type` 컬럼이 `'AI Analysis'`로 고정되며,
계산에 사용된 입력값의 `source_id` 목록을 `input_source_ids`에 남긴다. 대시보드는 두 레이어를 **다른 색으로** 렌더링한다.

**절대 규칙 2 — Unknown은 0이 아니다**
값이 없으면 `NULL` + `status_code`(`'UNKNOWN'` / `'NOT_AVAILABLE'` / `'NO_CLEAR_PUBLIC_POSITION'` / `'DISPUTED'`)를 기록한다.
점수 계산 시 NULL은 0으로 대체하지 않고, **분모에서 제외한 뒤 `coverage_pct`를 함께 출력**한다.
커버리지 60% 미만인 주는 점수를 표시하지 않고 `INSUFFICIENT_DATA`로 표기한다.

---

## 2. 원본 스펙 대비 정규화 결정 (변경 사유 명시)

원본 요구사항의 6개 테이블은 그대로 **뷰(View)로 제공**하되, 물리 테이블은 아래처럼 정규화했다.

| 원본 스펙 | 문제 | 설계 결정 |
|---|---|---|
| TABLE 2 `2026_ELECTION_TRACKER` | 레이스 속성(Seat_Status, 선거일)과 후보 속성(Candidate_Name, Incumbent)이 한 테이블에 혼재 → 후보가 3명이면 선거일이 3번 중복 저장되고 불일치 발생 | `election_race`(레이스 grain) + `candidate`(후보 grain)로 분리. 원본 형태는 `v_election_tracker` 뷰로 복원 |
| TABLE 2 `Seat_Status` 단일 컬럼 | Cook / Sabato / Inside Elections 등급이 서로 다름(예: 8월 IA·TX가 Cook에선 Toss-up, 다른 곳은 Lean R). 하나만 저장하면 정보 손실 | `race_rating` 테이블 분리 (race_id × rater × as_of_date). 스냅샷 이력이 곧 "Race Rating Change" 추적 데이터가 됨 |
| TABLE 3 `GOVERNOR_ELECTION_TRACKER` | TABLE 2와 대부분 중복 | `election_race`(office='Governor') + `governor_race_detail` 확장 테이블. 원본 형태는 `v_governor_tracker` 뷰 |
| TABLE 4 데이터센터 개수를 주 단위 컬럼으로 | 프로젝트별 MW·상태·운영사를 담을 수 없음. 상태 전이(계획→건설→운영) 추적 불가 | `dc_project`(프로젝트 grain)를 원장으로 두고, TABLE 4는 집계 뷰 `v_data_center_footprint`로 산출. 벤더 카운트는 `dc_vendor_count`에 별도 보존 |
| TABLE 5 `Policy_Category` 복수 선택 | 단일 컬럼에 콤마 저장 시 필터 불가 | `policy_category`(12행 룩업) + `position_policy_category` 정션 테이블 |
| §3 5개 평가축 | 축별 점수 없이 총점만 있으면 검증 불가 | `position_axis_score`(5행/입장)로 분해. 총점은 뷰에서 가중합으로 계산 |

---

## 3. 데이터센터 개수의 함정 (수집 전 반드시 합의할 사항)

같은 "미국 데이터센터 수"가 출처마다 이렇게 다르다:

| 출처 | 수치 | 정의 |
|---|---|---|
| Statista | 약 1,208 | 운영 중만, 사이트 단위 |
| dcmap.us (2026-02) | 4,713 (운영 3,567 / 건설 307 / 계획·승인 751) | 전 상태 포함, 시설 단위 |
| Aterio (2026-08-26) | 6,901 활성 파이프라인 (운영 2,072 / 건설 817 / 발표 4,012), 전체 7,759 | 발표 단계까지 포함 |
| C&C Tech | 3,698 운영 | 시설 단위 |

**최대 6배 차이.** 캠퍼스 1개를 1개로 세느냐, 건물 5개로 세느냐, 홀 20개로 세느냐의 문제다.

주별 순위도 정의에 따라 뒤집힌다:
- 시설 수 기준(Aterio, 전 상태): TX 1,330 > VA 1,030 > GA 477 > PA 368 > OH 349
- 시설 수 기준(dcmap, 전 상태): TX 578 > VA 484 > CA 393
- 계획 시설만(Pew/DataCenterMap, 2026-02): VA 287 > TX 170 > GA 141
- **전력 용량 기준(Aterio 파이프라인): TX 127,662MW > VA 58,xxx MW** ← 순위 역전
- 운영 중 전력 소비 비중: VA+TX가 미국 데이터센터 전력의 약 27%, 상위 5개 주가 약 절반

**→ 설계 대응:**
1. `dc_vendor_count` 테이블에 **벤더별 수치를 그대로 병렬 저장**한다. 하나로 합치지 않는다.
2. 랭킹·점수는 **단일 벤더 내부에서만** 계산한다 (`vendor_id`를 파티션 키로). 벤더 간 수치를 섞은 순위는 금지.
3. 대시보드는 벤더 선택 드롭다운을 제공하고, 기본 벤더를 명시한다.
4. **운영 중(Operational) MW와 파이프라인(전 상태) MW를 절대 같은 축에 그리지 않는다.** TX 127GW는 발표 단계를 포함한 숫자이고, VA의 운영 인벤토리 4,039MW(북버지니아, CBRE)와는 다른 층위의 수치다.

---

## 4. 정치인 입장 평가 설계 (§3 요구사항 구현)

### 4.1 증거 강제 구조

```
politician
   └─ politician_dc_position          (입장 레코드 1건)
        ├─ position_evidence          (근거 N건) ← 최소 1건 없으면 INSERT 거부 (트리거)
        ├─ position_axis_score        (5개 축 점수)
        └─ position_policy_category   (12개 정책 카테고리 다중 매핑)
```

`position_evidence.evidence_type`은 다음만 허용한다:
`Public statement` / `Campaign promise` / `Introduced bill` / `Voted for` / `Voted against` / `Signed bill` / `Vetoed bill` / `Supported legislation` / `Opposed legislation` / `Interview` / `Press release` / `Campaign ad`

**"정당 소속"은 evidence_type에 존재하지 않는다.** 이것이 §10 요구사항의 구조적 구현이다.
근거가 없으면 `dc_position = 'No Clear Public Position'`, `support_score = NULL`, `status_code = 'NO_CLEAR_PUBLIC_POSITION'`.

### 4.2 5개 축 (각 -100 ~ +100)

| 축 | axis_code | +100 방향 | -100 방향 |
|---|---|---|---|
| ① 산업 성장 | `GROWTH` | 적극 유치·인허가 간소화 | 모라토리엄·건설 제한 |
| ② 전력 | `POWER` | 발전·송전 확충 지지 | 신규 대용량 접속 제한 |
| ③ 전기요금 | `RATES` | 요금 영향 우려 없음 | 데이터센터가 망 투자비 부담해야 한다는 주장 |
| ④ 물 사용 | `WATER` | 규제·공개의무 반대 | 사용량 공개의무·취수 규제 주장 |
| ⑤ 세제 혜택 | `TAX` | 재산세 감면·판매세 면제 지지 | 감면 폐지·환수 조항 주장 |

②축은 방향성과 별개로 **발전원 선호**를 `power_source_pref`에 별도 기록한다
(`Nuclear` / `Natural Gas` / `Renewable` / `Coal` / `Storage` / `Mixed` / `Unknown` — 다중 허용).
원자력 지지와 가스 지지는 데이터센터 우호도가 같아도 정책 결과가 다르므로 점수로 뭉개지 않는다.

### 4.3 Data Center Support Score (-100 ~ +100)

```
support_score = Σ(axis_score_i × weight_i) / Σ(weight_i)     [NULL 축은 분모에서 제외]
```
기본 가중치는 `scoring_weight` 테이블에 저장 (전량 튜닝 가능):
GROWTH 0.30 / POWER 0.15 / RATES 0.25 / WATER 0.10 / TAX 0.20

RATES 가중치를 높게 잡은 이유: 2026년 사이클에서 실제 선거 쟁점이 된 축이 전기요금이기 때문(§0 근거).
5개 축 중 **3개 이상이 NULL이면 support_score는 NULL**로 남긴다.

---

## 5. Data Center Exposure Score (§4 요구사항)

```
exposure_raw = 0.40×N(Operational_MW) + 0.30×N(UnderConstruction_MW)
             + 0.20×N(Planned_MW)     + 0.10×N(Facility_Count)
```

`N()` 정규화 방식에 대한 설계 판단:
- **단순 max 정규화는 쓰지 않는다.** TX(127GW)가 1위인 순간 나머지 49개 주가 전부 0~10점으로 뭉개져 변별력이 사라진다.
- 채택: **로그 스케일 + 백분위 하이브리드** → `N(x) = 100 × log(1+x) / log(1+max)`
- 원시값·로그값·백분위값을 모두 저장해 대시보드에서 전환 가능하게 한다.

동시에 전국 비중을 별도 산출한다:
`operational_mw_share_pct`, `future_mw_share_pct`, `us_rank_operational`, `us_rank_pipeline`

비교 대상 주(스펙 §4 지정): VA, TX, AZ, GA, OH, PA, IN, NC, SC, NV, IA, OR + Top 20 확장

---

## 6. Political Risk Score (0~100)

TABLE 6의 두 축을 분리 계산한 뒤 결합한다.

**A. Election Risk Score (선거 자체의 불확실성, 0~100)**
```
= 0.30 × 접전 레이스 비율(Toss-up/Lean 의석 ÷ 해당 주 전체 선거 대상 의석)
+ 0.25 × 주지사 정권교체 가능성(Toss-up=100, Lean=65, Likely=30, Safe=5)
+ 0.20 × 트라이펙타 붕괴 가능성(주의회 다수당 마진 역산)
+ 0.15 × 오픈시트 비율(현직 은퇴/불출마)
+ 0.10 × 여론조사 변동성(최근 60일 표준편차)
```

**B. Data Center Policy Risk Score (정책 자체의 리스크, 0~100)**
```
= 0.25 × 후보군 평균 support_score의 부정 방향 편차
+ 0.20 × 전력망 스트레스(예비율·접속 대기열·요금 인상률)
+ 0.15 × 지역사회 반대 강도(모라토리엄 건수·주민 반대 사례)
+ 0.15 × 세제혜택 취약성(감면 규모 × 일몰/재심의 일정)
+ 0.15 × 규제 파이프라인(계류 법안·행정명령 건수)
+ 0.10 × 물 스트레스
```

**C. Overall = 0.45 × A + 0.55 × B**

B의 가중치가 더 높은 이유: 선거가 접전이어도 양당 후보가 모두 데이터센터에 우호적이면(또는 모두 적대적이면) 산업 리스크는 낮거나 이미 확정적이다. **2026년의 실제 위험은 "누가 이기느냐"보다 "양당 모두 규제로 수렴하고 있다"는 데 있다.**

→ 이를 포착하기 위해 `bipartisan_convergence_flag`를 별도 산출한다:
해당 주 주요 레이스에서 **양당 후보의 support_score가 모두 음수**이면 TRUE.
이 플래그가 TRUE인 주는 선거 결과와 무관하게 규제가 진행되므로, 시나리오 분석에서 A/B/C 결과가 수렴한다.

---

## 7. 시나리오 분석 구조 (§5)

주 × 시나리오(A/B/C) 그리드. 단, **정당 고정관념 금지 규칙**을 구조로 강제한다:

`scenario` 테이블의 각 영향 평가(`dc_expansion_impact` 등)는
`driver_evidence_ids` (해당 주의 실제 법안/발언/행정명령 ID 배열)가 비어 있으면 저장할 수 없다.
근거가 없으면 `'INSUFFICIENT_EVIDENCE'`로 남긴다.

예시(PA): Shapiro(D)가 규제 행정명령을 냈고 Garrity(R)도 "pause"를 주장 중 →
Scenario A(D 유지)와 Scenario B(R 승리) 모두 규제 방향. `bipartisan_convergence_flag = TRUE`.
"민주당=규제, 공화당=완화"라는 도식이 이 주에서는 성립하지 않는다.

---

## 8. 출처 신뢰도 체계 (§7)

`source.tier` 1~9 (낮을수록 우선):

| Tier | 유형 | 예 |
|---|---|---|
| 1 | 공식 선거기관 | 주 선거관리위원회, FEC |
| 2 | 주정부 | 주지사실, 주 PUC, 주 의회 |
| 3 | 미국 의회 | Congress.gov, 표결기록 |
| 4 | 후보 공식 홈페이지 | 캠페인 사이트, 공약집 |
| 5 | 법안 데이터베이스 | LegiScan, Ballotpedia(법안) |
| 6 | 공공기관 | EIA, LBNL, JLARC, Census |
| 7 | 기업 공식 발표 | AWS/Meta/Google 보도자료, 10-K |
| 8 | 산업 리서치 | CBRE, JLL, Aterio, DataCenterMap |
| 9 | 주요 언론 | WaPo, NPR, Politico, The Hill |

`confidence_level`은 tier와 **별개**로 부여한다 (Tier 9 언론의 직접 인용이 Tier 8 추정치보다 신뢰도가 높을 수 있음).
동일 사실에 출처가 충돌하면 `source_conflict` 테이블에 양쪽을 모두 기록하고 `status_code='DISPUTED'`.

---

## 9. 자동 업데이트 구조 (§8)

`change_log`가 아래 12개 이벤트를 추적한다:

`NEW_CANDIDATE` / `CANDIDATE_WITHDRAWAL` / `POLLING_CHANGE` / `RACE_RATING_CHANGE` /
`GOVERNOR_ELECTION_CHANGE` / `NEW_DC_ANNOUNCEMENT` / `DC_CANCELLATION` / `NEW_LEGISLATION` /
`TAX_INCENTIVE_CHANGE` / `ELECTRICITY_RATE_CHANGE` / `COMMUNITY_OPPOSITION` / `WATER_REGULATION`

구현 방식: 핵심 테이블에 AFTER UPDATE 트리거를 걸어 `(table, pk, field, old_value, new_value, changed_at, source_id)`를 자동 적재.
→ 이 로그가 곧 대시보드의 "최근 변동" 피드이자, 등급 변화 타임라인의 원천이 된다.

갱신 주기 권장:
- 레이스 등급: 주 2회 (Cook/Sabato 갱신 주기)
- 여론조사: 일 1회
- 데이터센터 프로젝트: 주 1회
- 정치인 입장: 주 1회 + 토론회·행정명령 발생 시 즉시
- 선거 D-30 이후: 전 항목 일 1회

---

## 10. STEP 2~8 작업 계획

| STEP | 산출물 | 주 출처 | 예상 난이도 |
|---|---|---|---|
| 2 | 연방 상·하원 2026 선거 대상 구조 + 50개 주 정치구조 | Ballotpedia, Cook, 270toWin, 주 선관위 | 중 |
| 3 | 36개 주지사 선거 현황 (후보·등급·임기제한) | Wikipedia/Ballotpedia + Cook/Sabato | 중 |
| 4 | 50개 주 데이터센터 현황 (벤더별 병렬 저장) | Aterio, dcmap, CBRE, EIA, 주 PUC | **상** |
| 5 | 데이터센터 규모 Top 20 주 확정 | STEP 4 집계 | 하 |
| 6 | Top 20 주 주요 정치인 입장 조사 (근거 필수) | 캠페인 사이트, 표결기록, 광고, 언론 | **최상** |
| 7 | 리스크 스코어 산출 | 파생 계산 | 중 |
| 8 | 인터랙티브 대시보드 | — | 상 |

**병목은 STEP 6이다.** Top 20 주 × (상원 후보 2~4명 + 주지사 후보 2~3명 + 접전 하원 지역구) ≈ 150~250명.
전원을 근거 기반으로 채우는 것은 이번 세션 범위를 넘는다.
→ 권장: **Top 10 주 × 상원·주지사 후보만 우선(약 50~60명)** 으로 1차 완성 후 확장.

### 확정 완료된 전국 베이스라인 (2026-08-27 기준, Fact)

| 항목 | 값 | 출처 |
|---|---|---|
| 선거일 | 2026년 11월 3일 | — |
| 현 상원 | 공화 53 / 민주 47 (무소속 2명 민주당 코커스 포함) | 270toWin |
| 2026 상원 선거 대상 | 35석 (FL·OH 보궐 포함), 그중 공화당 보유 23석 | 270toWin |
| 민주당 상원 다수당 요건 | 순증 4석 | 270toWin |
| 주지사 | 공화 26 / 민주 24 (2026년 1월 기준) | 270toWin |
| 2026 주지사 선거 | 36개 주 + 3개 준주, 15명 임기제한 | 270toWin / Wikipedia |
| Cook 하원 Toss-up | 18석 (민주 보유 10 / 공화 보유 8) | Cook Political Report |
| 8월 등급 변동 | IA·TX 상원 Lean R → Toss-up (Cook, 8/20) / AK·OH 추가 (Almanac, 8/24) | 270toWin |
| 주지사 등급 변동 | IA Toss-up → Lean D, TX Safe R → Likely R (8/20~8/26) | 270toWin |

> 위 표는 **Fact 레이어**다. 아래 어떤 점수도 이 표를 근거로 자동 추론하지 않는다.
