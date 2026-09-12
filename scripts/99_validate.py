#!/usr/bin/env python3
"""무결성 검증. 위반이 있으면 exit 1 로 CI를 실패시킨다.

자동화에서 가장 큰 위험은 "그럴듯하지만 근거 없는 데이터"가 조용히 쌓이는 것이다.
사람 검토가 빠진 파이프라인에서는 이 검사가 유일한 방어선이다.
"""
import sqlite3, math, sys, datetime
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
fail, warn = [], []

def check(name, sql, expect_zero=True, note=""):
    n = cur.execute(sql).fetchone()[0]
    if expect_zero and n > 0:
        fail.append(f"{name}: {n}건 — {note}")
    return n

# ---- P3. 근거 없는 점수
check("P3 근거 없는 축 점수", """
  SELECT COUNT(*) FROM position_axis_score a WHERE a.axis_score IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM position_evidence e WHERE e.position_id=a.position_id)""",
  note="axis_score 는 position_evidence 최소 1건을 요구한다")

check("P3 출처 없는 근거", """
  SELECT COUNT(*) FROM position_evidence e
  WHERE e.source_id IS NULL OR NOT EXISTS
        (SELECT 1 FROM source s WHERE s.source_id=e.source_id)""",
  note="모든 근거는 source 테이블을 참조해야 한다")

check("P3 URL 없는 출처", "SELECT COUNT(*) FROM source WHERE url IS NULL OR url=''",
      note="출처는 URL 이 필수다")

check("P3 날짜 없는 근거", """
  SELECT COUNT(*) FROM position_evidence
  WHERE evidence_date IS NULL OR evidence_date=''""",
  note="근거는 발생일이 필수다")

# ---- P1. 사실/분석 혼입
check("P1 파생 테이블에 Fact 표기", """
  SELECT COUNT(*) FROM dc_election_risk WHERE data_type <> 'AI Analysis'""",
  note="파생 테이블은 AI Analysis 로 고정")
check("P1 시나리오 근거 누락", """
  SELECT COUNT(*) FROM scenario
  WHERE (driver_evidence_ids IS NULL OR trim(driver_evidence_ids)='')
    AND overall_risk_direction <> 'INSUFFICIENT_EVIDENCE'""",
  note="근거 없는 시나리오는 INSUFFICIENT_EVIDENCE 여야 한다")

# ---- 날짜 무결성
today = datetime.date.today().isoformat()
check("미래 날짜 여론조사", f"""
  SELECT COUNT(*) FROM polling WHERE field_end > '{today}'""",
  note="종료일이 미래인 조사")
check("날짜 없는 등급", """
  SELECT COUNT(*) FROM race_rating WHERE as_of_date IS NULL OR as_of_date=''""",
  note="등급은 기준일이 필수다")
check("필드 기간 없는 조사", """
  SELECT COUNT(*) FROM polling WHERE field_end IS NULL OR field_end=''""",
  note="필드 종료일 없는 조사는 적재 금지")

# ---- 대진 정합성: 조사가 붙은 레이스에 후보가 없으면 의심
check("후보 없는 레이스의 여론조사", """
  SELECT COUNT(*) FROM polling p JOIN election_race r ON r.race_id=p.race_id
  WHERE NOT EXISTS (SELECT 1 FROM candidate c WHERE c.race_id=r.race_id)""",
  note="실존하지 않는 대진 조사일 수 있다")

# ---- 범위 검사
check("범위 밖 축 점수", """
  SELECT COUNT(*) FROM position_axis_score
  WHERE axis_score IS NOT NULL AND (axis_score < -100 OR axis_score > 100)""")
check("범위 밖 가중치", """
  SELECT COUNT(*) FROM binding_force WHERE weight < 0 OR weight > 1""")

# ---- P4. 벤더 혼합 탐지
n = cur.execute("""SELECT COUNT(DISTINCT vendor_id) FROM dc_vendor_count""").fetchone()[0]
if n > 1:
    dup = cur.execute("""SELECT state_code, COUNT(DISTINCT vendor_id) c
        FROM dc_vendor_count GROUP BY state_code HAVING c > 1""").fetchall()
    if dup:
        warn.append(f"P4 확인 필요: {len(dup)}개 주에 복수 벤더 수치 존재 — "
                    "합산하지 말고 벤더 내부에서만 비교할 것")

# ---- 참조 무결성
for t, col, ref, rcol in [
    ("candidate","race_id","election_race","race_id"),
    ("position_evidence","position_id","politician_dc_position","position_id"),
    ("race_rating","race_id","election_race","race_id"),
    ("polling","race_id","election_race","race_id"),
]:
    check(f"고아 참조 {t}.{col}", f"""
      SELECT COUNT(*) FROM {t} x WHERE NOT EXISTS
      (SELECT 1 FROM {ref} y WHERE y.{rcol}=x.{col})""")

# ---- 커버리지 경고 (실패는 아님)
pos = cur.execute("SELECT COUNT(*) FROM politician_dc_position").fetchone()[0]
noscore = cur.execute("""SELECT COUNT(*) FROM v_effective_position
                         WHERE support_score IS NULL""").fetchone()[0]
if pos and noscore / pos > 0.6:
    warn.append(f"방향 종합 미산출 {noscore}/{pos} — 축 근거 보강 필요")

empty = [t for t in ("dc_project","dc_election_risk","scenario")
         if cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0]
if empty:
    warn.append("미착수 핵심 테이블: " + ", ".join(empty))

con.close()

print("=" * 58)
if warn:
    print("경고")
    for w in warn: print("  ⚠ " + w)
if fail:
    print("\n검증 실패")
    for f in fail: print("  ✗ " + f)
    print("=" * 58)
    sys.exit(1)
print("\n✔ 무결성 검증 통과")
print("=" * 58)
