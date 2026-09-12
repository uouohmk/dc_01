#!/usr/bin/env python3
"""2026-09-01 갱신 — 여론조사 히트맵 레이어

이 갱신의 결론은 "여론조사 지도"가 아니라 "여론조사 공백 지도"다.
35개 상원 레이스 중 본선 여론조사가 확인되는 곳은 극소수이며,
격전지를 제외하면 사실상 비어 있다.
빈칸을 추정으로 채우지 않고, 공백 자체를 지표로 만든다.
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-09-01"

for row in [
 (60,8,"Pollsmax","2026 Kentucky Senate polling average",
  "https://www.pollsmax.com/senate/kentucky/","2026-08-01",NOW,0),
 (61,9,"270toWin","2026 Senate Polling by state — 폴링 없는 주 표기",
  "https://www.270towin.com/content/2026-senate-polling","2026-08-31",NOW,0),
]:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", row)

# ---------------------------------------------------------- 확인된 본선 조사 추가
pid = cur.execute("SELECT COALESCE(MAX(poll_id),0) FROM polling").fetchone()[0]
for st, off, house, s0, s1, n, pop, marg, src in [
 # 켄터키: 확인되는 유일한 본선 조사. 8개월 지난 자료라 사실상 무의미하다.
 ("KY","U.S. Senate","Public Policy Polling (D)","2025-12-17","2025-12-19",None,None,-11.0,60),
]:
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    if not r: continue
    pid += 1
    cur.execute("""INSERT INTO polling(poll_id,race_id,pollster,field_start,field_end,
        sample_size,population,margin_d_minus_r,is_average,polling_source,source_id)
        VALUES (?,?,?,?,?,?,?,?,0,?,?)""", (pid, r[0], house, s0, s1, n, pop, marg, house, src))

# ---------------------------------------------------------- 여론조사 공백 뷰
cur.executescript("""
DROP VIEW IF EXISTS v_poll_coverage;
CREATE VIEW v_poll_coverage AS
WITH latest AS (
    SELECT r.race_id, r.state_code, r.office,
           MAX(p.field_end) AS last_poll_date,
           COUNT(p.poll_id)  AS poll_count
    FROM election_race r LEFT JOIN polling p ON p.race_id = r.race_id
    WHERE r.general_election_date LIKE '2026%'
    GROUP BY r.race_id
),
comp AS (
    SELECT rr.race_id, MAX(s.competitiveness) AS max_comp
    FROM race_rating rr JOIN race_rating_scale s ON s.rating_code = rr.rating_code
    GROUP BY rr.race_id
),
marg AS (
    SELECT p.race_id, p.margin_d_minus_r, p.field_end, p.pollster
    FROM polling p
    WHERE p.field_end = (SELECT MAX(p2.field_end) FROM polling p2 WHERE p2.race_id = p.race_id)
)
SELECT l.race_id, l.state_code, l.office, l.poll_count, l.last_poll_date,
       m.margin_d_minus_r AS latest_margin, m.pollster AS latest_pollster,
       c.max_comp,
       CASE WHEN COALESCE(c.max_comp,0) >= 65 THEN 1 ELSE 0 END AS is_battleground,
       CASE WHEN l.last_poll_date IS NULL THEN NULL
            ELSE CAST(julianday('2026-09-10') - julianday(l.last_poll_date) AS INTEGER)
       END AS poll_age_days,
       CASE
         WHEN l.poll_count = 0                       THEN 'NO_POLLING'
         WHEN julianday('2026-09-10') - julianday(l.last_poll_date) > 90 THEN 'STALE'
         WHEN julianday('2026-09-10') - julianday(l.last_poll_date) > 30 THEN 'AGING'
         ELSE 'CURRENT'
       END AS coverage_status
FROM latest l
LEFT JOIN comp c ON c.race_id = l.race_id
LEFT JOIN marg m ON m.race_id = l.race_id;
""")

# ---------------------------------------------------------- 사각지대 지표
# 데이터센터 규제가 실제로 움직이는데 여론조사가 없는 주 = 관측 불가 리스크
cur.executescript("""
DROP VIEW IF EXISTS v_polling_blind_spot;
CREATE VIEW v_polling_blind_spot AS
SELECT pc.state_code,
       pc.office,
       pc.coverage_status,
       pc.poll_age_days,
       pc.is_battleground,
       (SELECT COUNT(*) FROM politician_dc_position p
          JOIN politician pl ON pl.politician_id = p.politician_id
         WHERE pl.state_code = pc.state_code)              AS dc_positions_tracked,
       (SELECT COUNT(*) FROM change_log c
         WHERE c.state_code = pc.state_code
           AND c.event_type IN ('NEW_LEGISLATION','COMMUNITY_OPPOSITION',
                                'TAX_INCENTIVE_CHANGE','WATER_REGULATION'))
                                                            AS dc_policy_events,
       sc.grid_operator, sc.grid_stress_level,
       CASE WHEN pc.coverage_status = 'NO_POLLING'
             AND ((SELECT COUNT(*) FROM change_log c2 WHERE c2.state_code = pc.state_code
                    AND c2.event_type IN ('NEW_LEGISLATION','COMMUNITY_OPPOSITION')) > 0
                  OR sc.grid_stress_level IN ('High','Severe'))
            THEN 1 ELSE 0 END AS blind_spot_flag,
       'AI Analysis' AS data_type
FROM v_poll_coverage pc
LEFT JOIN state_dc_context sc ON sc.state_code = pc.state_code;
""")
con.commit()

# ---------------------------------------------------------- 검증 출력
print("=== 2026 레이스 여론조사 커버리지 ===")
for r in cur.execute("""SELECT coverage_status, is_battleground, COUNT(*)
    FROM v_poll_coverage GROUP BY 1,2 ORDER BY 2 DESC, 1"""):
    tag = "격전지" if r[1] else "격전지 외"
    print(f"  {tag:<8}{r[0]:<12}{r[2]:>3}개")

print("\n=== 본선 조사가 있는 레이스 (전부) ===")
for r in cur.execute("""SELECT state_code, office, poll_count, last_poll_date, latest_margin,
    poll_age_days, is_battleground FROM v_poll_coverage
    WHERE poll_count > 0 ORDER BY last_poll_date DESC"""):
    lead = f"D+{r[4]:.0f}" if r[4] and r[4] > 0 else (f"R+{abs(r[4]):.0f}" if r[4] else "—")
    print(f"  {r[0]} {r[1]:<14}{r[2]}건  최근 {r[3]}  {lead:>6}  {r[5]:>4}일 전"
          f"  {'격전지' if r[6] else '격전지 외'}")

print("\n=== 사각지대: 조사 없음 + 데이터센터 정책 실제 진행 ===")
for r in cur.execute("""SELECT state_code, office, dc_positions_tracked, dc_policy_events,
    grid_operator, grid_stress_level FROM v_polling_blind_spot
    WHERE blind_spot_flag=1 ORDER BY dc_policy_events DESC, state_code"""):
    print(f"  {r[0]} {r[1]:<14}입장 {r[2]}건 · 정책이벤트 {r[3]}건 · {r[4] or '—'} "
          f"{r[5] or ''}")
con.close()
