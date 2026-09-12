---
name: policy-update
description: 2026 선거 후보들의 데이터센터 관련 정책 입장을 수집해 dc_01 트래커에 근거 기반으로 적재한다. 사용자가 '정책 갱신', '후보 입장 확인', '데이터센터 공약', '레버리지 갱신', 'policy update', '새 행정명령·법안 반영'을 언급하면 사용한다. 방향 5축과 구속력·범위를 분리해 기록하며 근거 없는 점수 입력은 DB 트리거가 차단한다.
---

# 후보 정책 입장 갱신

## 핵심 원칙

**정당으로 입장을 추론하지 않는다.** 민주당 주지사가 모라토리엄을 걸고
공화당 상원 후보가 건설 중단을 요구하는 것이 이 사이클의 실제 모습이다.

**말의 강도와 실제 강도를 분리한다.** 광고에서 가장 세게 말하는 후보와
이미 서명한 후보는 다르다. 그 차이를 구속력 가중치가 담는다.

## 1. 현재 상태

```bash
sqlite3 data/tracker.db "SELECT state_code, full_name, party, office, leverage_score, \
  support_score, top_binding_label, confidence_level FROM v_effective_position \
  ORDER BY leverage_score DESC;"
```

`support_score` 가 NULL 인 후보는 5축 중 3축 미만이라 종합이 안 나온 상태다.
새 근거로 축을 채우면 처음으로 산출된다.

## 2. 검색 대상

우선순위가 높은 것부터.

1. 주지사실·규제기관 공식 발표 (행정명령, 지시) — 구속력 최상
2. 주의회 법안 (LegiScan, 주의회 사이트)
3. 후보 캠페인 사이트의 정책안
4. 지역 언론의 정책 상세 보도 ← **전국 언론보다 유용하다**
5. 선거 광고 분석 기사

질의 예: `[주] governor data center executive order 2026`,
`[후보명] data center moratorium tax exemption`

## 3. 5개 축

| 축 | +100 | −100 |
|---|---|---|
| `GROWTH` 산업성장 | 적극 유치·인허가 간소화 | 모라토리엄·건설 제한 |
| `POWER` 전력 | 발전·송전 확충 지지 | 신규 대용량 접속 제한 |
| `RATES` 전기요금 | 요금 영향 우려 없음 | 데이터센터가 망 투자비 부담 |
| `WATER` 물사용 | 규제·공개의무 반대 | 사용량 공개·취수 규제 주장 |
| `TAX` 세제혜택 | 감면·면제 지지 | 폐지·환수 주장 |

축이 서로 반대 방향인 경우가 실제로 있다.
Paxton은 전력축 +45인데 나머지 넷이 음수다. 한 숫자로 뭉개지 마라.

발전원 선호(`power_source_pref`)는 별도 기록한다.
원자력 지지와 가스 지지는 우호도가 같아도 정책 결과가 다르다.

## 4. 구속력과 범위

`binding_code` — 그 입장이 실제로 강제되는가

`SIGNED_LAW` 1.00 · `SIGNED_EO` 0.95 · `EXEC_DIRECTIVE` 0.85 · `VOTE_RECORD` 0.70
`BILL_FILED` 0.60 · `POLICY_PLAN` 0.45 · `CAMPAIGN_PROMISE` 0.40
`PUBLIC_STATEMENT` 0.25 · `CAMPAIGN_AD` 0.20

`scope_code` — 규제가 무엇에 걸리는가

`NEW_TOTAL` 1.00 · `EXISTING_INCLUDED` 0.90 · `NEW_CONDITIONAL` 0.75
`SITING_BAN` 0.70 · `LOCAL_CONSENT` 0.65 · `INCENTIVE_REPEAL` 0.60
`COST_ALLOCATION` 0.50 · `DISCLOSURE` 0.25

`direction` 은 `RESTRICTIVE` / `SUPPORTIVE` / `NEUTRAL`.
한 후보가 규제 근거와 우호 근거를 동시에 가질 수 있다. 둘 다 기록한다.

## 5. 적재

```python
# 1) 근거 먼저 (P3: 근거 없이 점수 입력 불가 — 트리거가 막는다)
cur.execute("""INSERT INTO position_evidence(evidence_id,position_id,evidence_type,
    summary,evidence_date,source_id,binding_code,scope_code,direction)
    VALUES (?,?,?,?,?,?,?,?,?)""", (...))

# 2) 축 점수
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,
    axis_score,evidence_id,status_code) VALUES (?,?,?,?,?)""", (...))
# 근거 없는 축은 axis_score=NULL, status_code='NO_CLEAR_PUBLIC_POSITION'

# 3) 분류 갱신
# Strongly Supportive / Supportive / Neutral / Mixed / Concerned /
# Restrictive / Strongly Opposed / No Clear Public Position
```

`evidence_type` 허용값: Public statement · Campaign promise · Introduced bill ·
Voted for · Voted against · Signed bill · Vetoed bill · Supported legislation ·
Opposed legislation · Interview · Press release · Campaign ad · Executive order

**"정당 소속"은 허용값에 없다.**

## 6. 기존 기록 재검토

새 근거를 볼 때마다 확인한다.

- 기존 구속력이 과소평가돼 있지 않은가 (발표인 줄 알았는데 이미 법률)
- 분류가 뒤집히지 않는가 (공격받은 후보가 방어 법안을 내면 Supportive → Mixed)
- 새 축이 채워져 `support_score` 가 처음 산출되는가

## 7. 검증

```bash
./scripts/run_pipeline.sh && python3 scripts/99_validate.py
```

레버리지 순위가 바뀌면 `change_log` 에 기록하고 보고한다.
