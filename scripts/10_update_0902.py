#!/usr/bin/env python3
"""2026-09-02 갱신 — 선거 노출도 상위 주 여론조사

대상: 상원·주지사 동시 선거 26개 주 중 경합도 상위 (OH, MI, IA, GA, AK) + ME
결과: OH·MI·IA·ME 확보. GA는 실제 대진(Ossoff vs Mike Collins) 조사를 찾지 못했다.
      떠도는 Kemp vs Ossoff 조사는 Kemp가 후보가 아니므로 적재하지 않는다.
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-09-02"

for row in [
 (70,9,"Fox News","Ohio Senate poll — Beacon Research (D) / Shaw & Company (R)",
  "https://www.foxnews.com/politics/fox-news-poll-economic-anxiety-candidate-concerns-define-ohio-senate-race",
  "2026-08-12",NOW,0),
 (71,9,"The Hill / AARP","Ohio Senate & Governor poll — Fabrizio Ward + Impact Research",
  "https://thehill.com/homenews/campaign/5946710-ohio-voters-ramaswamy-husted/","2026-06-30",NOW,0),
 (72,9,"Impact Research (D)","Ohio governor survey, 800 LV",
  "https://www.yahoo.com/news/articles/poll-ramaswamy-acton-dead-heat-221900719.html","2026-08-12",NOW,0),
 (73,8,"Emerson College Polling","Ohio 2026 poll — Senate & Governor",
  "https://emersoncollegepolling.com/ohio-2026-poll-democrats-make-gains-in-races-for-governor-and-us-senate/",
  "2025-12-17",NOW,1),
 (74,8,"Pollsmax","2026 Michigan Senate polling average (21 polls)",
  "https://www.pollsmax.com/senate/michigan/","2026-08-31",NOW,0),
 (75,9,"Forbes","Latest 2026 Senate Polls — El-Sayed leads Rogers by 4 in Michigan",
  "https://www.forbes.com/sites/saradorn/2026/08/31/latest-2026-senate-polls-el-sayed-leads-rogers-by-4-points-in-michigan/",
  "2026-08-31",NOW,0),
 (76,9,"CNN","Senate Democrats have 1 unpopular candidate. It's much worse for Republicans",
  "https://www.cnn.com/2026/08/18/politics/republican-senate-candidates-unpopularity","2026-08-18",NOW,0),
]:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", row)

# margin_d_minus_r : 양수 = 민주 우세
POLLS = [
 # (주, 직위, 조사기관, 시작, 종료, n, 모집단, 마진, 평균여부, source)
 ("OH","U.S. Senate","Fox News (Beacon/Shaw)","2026-08-06","2026-08-10",1008,"RV", 8.0,0,70),
 ("OH","U.S. Senate","AARP (Fabrizio Ward/Impact)","2026-06-14","2026-06-16",800,"LV", 3.0,0,71),
 ("OH","U.S. Senate","Emerson College","2025-12-11","2025-12-15",None,"RV",-3.0,0,73),
 ("OH","Governor",   "Impact Research (D)","2026-07-24","2026-07-28",800,"LV",-1.0,0,72),
 ("OH","Governor",   "AARP (Fabrizio Ward/Impact)","2026-06-14","2026-06-16",800,"LV", 3.0,0,71),
 ("OH","Governor",   "Emerson College","2025-12-11","2025-12-15",None,"RV", 1.0,0,73),
 ("MI","U.S. Senate","Susquehanna Polling & Research (R)","2026-08-17","2026-08-17",None,None, 7.0,0,74),
 ("MI","U.S. Senate","Pollsmax 평균 (21건 집계)","2026-08-31","2026-08-31",None,None, 0.5,1,74),
 ("IA","U.S. Senate","Suffolk University","2026-08-22","2026-08-25",None,None,-4.0,0,75),
 ("ME","U.S. Senate","University of New Hampshire","2026-07-01","2026-07-31",None,None, 3.0,0,75),
]
pid = cur.execute("SELECT COALESCE(MAX(poll_id),0) FROM polling").fetchone()[0]
added = 0
for st, off, house, s0, s1, n, pop, marg, avg, src in POLLS:
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    if not r:
        print("  레이스 없음:", st, off); continue
    pid += 1; added += 1
    cur.execute("""INSERT INTO polling(poll_id,race_id,pollster,field_start,field_end,
        sample_size,population,margin_d_minus_r,is_average,polling_source,source_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (pid, r[0], house, s0, s1, n, pop, marg, avg, house, src))

# 조지아: 실제 대진 조사 부재를 명시적으로 기록
cur.execute("""INSERT INTO source_conflict(conflict_id,target_table,target_pk,target_field,
    source_id_a,value_a,source_id_b,value_b,resolution,note,logged_at)
    VALUES ((SELECT MAX(conflict_id)+1 FROM source_conflict),'polling','GA','margin_d_minus_r',
    2,'Kemp vs Ossoff (R+6, Club for Growth/WPA 내부조사)',
    2,'실제 대진은 Mike Collins vs Ossoff',
    'PREFER_B','Kemp는 2026 상원 후보가 아니므로 해당 조사는 실제 레이스를 측정하지 않는다. 미적재.',
    ?)""", (NOW,))

cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
for et, st, note, ov, nv, when, src in [
 ("POLLING_CHANGE","OH","Fox News: 상원 Brown +8 (8/6-10, n=1008 RV). 12월 Emerson R+3에서 11p 이동",
  "R+3 (2025-12)","D+8 (2026-08)","2026-08-12",70),
 ("POLLING_CHANGE","OH","주지사: Impact Research R+1 (7/24-28) — 6월 AARP D+3에서 재역전",
  "D+3 (2026-06)","R+1 (2026-07)","2026-08-12",72),
 ("POLLING_CHANGE","MI","Susquehanna(R): El-Sayed +7 (8/17). Pollsmax 21건 평균은 D+0.5로 접전",
  None,"D+7 / 평균 D+0.5","2026-08-31",74),
 ("POLLING_CHANGE","IA","Suffolk: Hinson +4 (45-41). Emerson도 R+2~3으로 Cook의 Toss-up 이동과 정합",
  None,"R+4","2026-08-26",75),
 ("POLLING_CHANGE","ME","UNH 7월 조사: Jackson +3. 후보 교체 후 첫 확인 조사",
  None,"D+3","2026-07-31",75),
 ("POLLING_CHANGE",None,"CNN 분석: 상원 다수당을 좌우할 8개 레이스 중 공화 후보의 호감도 순증이 "
  "양수인 곳은 알래스카뿐. 7곳에서 민주 후보가 8~24p 우위. 격차 최대는 조지아와 아이오와",
  None,"D 후보 호감도 우위 7/8","2026-08-18",76),
]:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,target_pk,
        field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'polling',?,?,?,?,?,?,?)""",
        (cid, et, st, st or "US", "margin", ov, nv, when, src, note))
con.commit()

print(f"조사 {added}건 적재\n")
print("=== 노출도 상위 주 커버리지 ===")
for r in cur.execute("""SELECT state_code, office, poll_count, last_poll_date, latest_margin,
    poll_age_days, coverage_status, is_battleground FROM v_poll_coverage
    WHERE poll_count > 0 ORDER BY state_code, office"""):
    lead = (f"D+{r[4]:.1f}".rstrip('0').rstrip('.') if r[4] and r[4] > 0
            else (f"R+{abs(r[4]):.1f}".rstrip('0').rstrip('.') if r[4] else "—"))
    print(f"  {r[0]} {r[1]:<14}{r[2]}건  {r[3]}  {lead:>7}  {r[5]:>4}일  {r[6]:<9}"
          f"{'격전지' if r[7] else ''}")

print("\n=== 커버리지 요약 ===")
for r in cur.execute("""SELECT coverage_status, COUNT(*) FROM v_poll_coverage
    GROUP BY 1 ORDER BY 2 DESC"""):
    print(f"  {r[0]:<12}{r[1]:>3}개 레이스")

print("\n=== 남은 사각지대 (조사 없음 + DC 정책 진행) ===")
for r in cur.execute("""SELECT state_code, office, dc_positions_tracked, dc_policy_events
    FROM v_polling_blind_spot WHERE blind_spot_flag=1 AND dc_positions_tracked > 0
    ORDER BY dc_positions_tracked DESC"""):
    print(f"  {r[0]} {r[1]:<14}입장 {r[2]}건 · 정책이벤트 {r[3]}건")
con.close()
