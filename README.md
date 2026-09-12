# U.S. Midterm × Data Center Political Risk Tracker

2026년 미국 중간선거와 데이터센터 산업의 정치 리스크를 함께 추적합니다.

**[→ 대시보드 열기](https://uouohmk.github.io/dc_01/)**

데이터 기준일 **2026-09-10** · 선거일 2026-11-03

---

## 무엇을 측정하나

후보의 데이터센터 입장을 "찬성/반대" 한 축으로 재지 않습니다. 세 가지를 따로 기록합니다.

| 차원 | 내용 |
|---|---|
| **방향** | 산업성장 · 전력 · 전기요금 · 물사용 · 세제혜택 5개 축, 각 -100~+100 |
| **구속력** | 법률 서명 1.00 → 행정명령 0.95 → 표결 0.70 → 공약 0.40 → 광고 0.20 |
| **범위** | 신규 전면중단 1.00 → 입지제한 0.70 → 세제폐지 0.60 → 비용부담 0.50 |
| **직위권한** | 주지사 1.00 · 주의원 0.70 · 연방상원 0.55 · 연방하원 0.45 |

`레버리지 = 구속력 × 범위 × 직위권한 × 100`

## 여론조사 공백 지도

지도의 "여론조사 공백" 모드는 조사 결과가 아니라 **조사의 부재**를 보여줍니다.
71개 레이스 중 본선 여론조사가 확인되는 곳은 9개입니다. 나머지 62개는 완전한 공백입니다.

"격전지 제외" 체크박스를 켜면 Lean 이상 등급이 붙은 레이스가 숨겨집니다.
남는 것은 거의 전부 빗금이며, 그것이 이 모드의 결론입니다.

`v_polling_blind_spot` 뷰는 **데이터센터 정책이 실제로 진행 중인데 여론조사가 없는** 레이스를 표시합니다.
선거 리스크를 여론으로 검증할 수 없는 구간입니다.

이렇게 재면 순위가 뒤집힙니다. 선거 광고에서 가장 강하게 말하는 후보와 실제로 규제에 서명한 후보는 다릅니다.

## 현재 수록 범위

- 50개 주 정치 골격 (주지사 · 정당 · 임기제한)
- 연방 상원 35석 (정규 33 + FL·OH 보궐 2), 주지사 36개 주
- 레이스 등급 27건 — Cook · Sabato · Inside Elections · Almanac · Fox News
- 후보 데이터센터 입장 16명 / 근거 44건 (NY·TX·PA·OH·MI·FL·OR)
- 텍사스 데이터센터 여론 13개 지표 + 전국(Pew) 3개
- 본선 여론조사 25건 / 9개 레이스 (AK·OH·TX·MI·IA·ME·KY) — 공백 62개 레이스
- PJM 용량시장 낙찰가 4개 연도 — 전기요금 쟁점의 실제 기전
- 발효 중인 주 단위 규제 3건 (NY 행정명령 62호, TX 접속승인 중단, OR 세제혜택 중단)

## 데이터 원칙

1. **사실과 분석을 섞지 않습니다.** 선거 일정·후보·발언은 Fact, 점수와 가중치는 AI 분석입니다. 대시보드에서 배지로 구분됩니다.
2. **모르는 값은 0이 아닙니다.** NULL + 상태코드로 남기고 "미수집"으로 표시합니다.
3. **정당만 보고 입장을 추론하지 않습니다.** `position_evidence` 레코드 없이는 점수 입력이 DB 트리거로 차단됩니다. 근거 유형에 "정당 소속"은 존재하지 않습니다.
4. **데이터센터 수치는 벤더별로 병렬 저장합니다.** 같은 "미국 데이터센터 수"가 출처별로 최대 6배 차이 납니다. 합치지 않습니다.

## 문서

| 파일 | 용도 |
|---|---|
| `HANDOFF.md` | **자동 생성.** 프로젝트 전체 상태 · 원칙 · 스코어링 · 출처 대장 · 남은 작업. 다른 시스템이 이어받을 때 이 파일 하나면 된다 |
| `AGENTS.md` | 에이전트 규칙. 절대 원칙 P1~P4와 확인된 함정 5가지 |
| `AUTOMATION.md` | Antigravity 에이전트 + GitHub Actions 설정 절차 |
| `BLUEPRINT.md` | 스키마 설계 문서. 정규화 결정과 그 사유 |
| `ARTICLE.md` | 발행용 작성 키트 — 본문 초안 · 제목안 · 카드 카피 · 인용 수치표 |
| `.agents/skills/` | Antigravity 스킬 — poll-update · policy-update |
| `.agents/workflows/` | 주간 갱신 절차 |

## 구조

```
index.html          단일 파일 대시보드 (외부 의존성 없음)
data/tracker.db     SQLite. 27 테이블 · 9 뷰 · 4 트리거
data/01_schema.sql  스키마 DDL
scripts/            재현용 스크립트
cards/              카드뉴스 6장 (1080×1350)
BLUEPRINT.md        설계 문서
AGENTS.md           에이전트 규칙
AUTOMATION.md       자동화 설정 (Antigravity + Actions)
.agents/
  skills/           poll-update · policy-update
  workflows/        weekly-tracker-update
HANDOFF.md          인수인계 문서 (자동 생성)
ARTICLE.md          작성 키트
```

## 갱신

```bash
python3 scripts/02_seed_step2_3.py    # 선거 구조
python3 scripts/04_positions.py       # 후보 입장
python3 scripts/06_update_0829.py     # 등급 · 여론
python3 scripts/07_update_0830.py     # NY 모라토리엄 · ME 후보 교체
python3 scripts/08_update_0831.py     # OR 쟁점 · 근거 수정
python3 scripts/09_update_0901.py     # 여론조사 공백 지도
python3 scripts/10_update_0902.py     # 노출도 상위 주 조사
python3 scripts/03_build_dashboard.py # 대시보드 재생성
python3 scripts/05_cards.py           # 카드뉴스 재생성
python3 scripts/11_build_handoff.py   # 인수인계 문서 재생성 (항상 마지막)
```

무엇이 바뀌었는지는 DB가 자동 기록합니다.

```sql
SELECT changed_at, state_code, note FROM change_log ORDER BY changed_at DESC LIMIT 20;
```

## 출처

공식 선거기관 → 주정부 → 미국 의회 → 후보 공식 → 법안DB → 공공기관 → 기업 공식 → 산업 리서치 → 언론 순으로 우선합니다. 모든 근거에 원문 URL과 날짜가 붙어 있으며 대시보드에서 확인할 수 있습니다.

주요 출처: UT/Texas Politics Project · CBS Texas · Texas Tribune · E&E News · The Hill · CNBC · NPR · Brookings · Cook Political Report · Sabato's Crystal Ball · 270toWin

## 면책

특정 정당이나 후보를 지지하지 않습니다. 점수는 공개된 근거에 기반한 저자의 판단이며 가중치는 `binding_force` · `regulation_scope` · `office_power` 테이블에 전부 공개돼 있습니다. 투자 판단의 근거로 삼기 전에 원문을 직접 확인하시기 바랍니다.
