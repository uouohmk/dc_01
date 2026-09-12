#!/usr/bin/env python3
"""2026-09-10 갱신

1) 뉴햄프셔 예비선거(9/8) 결과 — 공화 John E. Sununu vs 민주 Chris Pappas 확정
2) 알래스카 상원 조사 3건 — 등급이 Lean R → Toss-up 으로 옮겨간 이유 포함
3) 함정 2건 추가 기록
   - 동명이인: Chris Sununu(전 주지사) ≠ John E. Sununu(전 상원의원).
     전자를 대상으로 한 가상대결 조사가 유통 중이나 후보가 아니다. 미적재.
   - 집계 사이트 캐시 오염: RCP 발췌에 2024년 대진(Brown vs Moreno,
     McCormick vs Casey, Hovde vs Baldwin, Rogers vs Slotkin)이 2026년 목록으로 섞여 나옴.
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-09-10"

for row in [
 (80,9,"NBC News","Sununu and Pappas win New Hampshire Senate primaries",
  "https://www.nbcnews.com/politics/2026-primary-elections/new-hampshire-senate-results",
  "2026-09-08",NOW,0),
 (81,9,"New Hampshire Public Radio","Pappas, Sununu sweep to victory in U.S. Senate primaries",
  "https://www.nhpr.org/politics/2026-09-08/pappas-sununu-win-senate-primaries-nh-newhampshire-elections-2026",
  "2026-09-08",NOW,0),
 (82,8,"Alaska Survey Research","Alaska Senate poll, 1371 LV",
  "https://www.newsweek.com/democrats-chances-of-flipping-the-senate-75-days-to-midterms-polls-12347504",
  "2026-08-19",NOW,0),
 (83,8,"Data for Progress","Alaska Senate poll, 578 LV",
  "https://www.newsweek.com/democrats-chances-of-flipping-the-senate-75-days-to-midterms-polls-12347504",
  "2026-08-19",NOW,0),
 (84,8,"New York Times / Siena College","Alaska Senate poll, 593 LV",
  "https://www.newsweek.com/democrats-chances-of-flipping-the-senate-75-days-to-midterms-polls-12347504",
  "2026-08-19",NOW,0),
 (85,9,"NPR","With just a few primaries to go, the competitive Senate map keeps shifting",
  "https://www.npr.org/2026/07/27/nx-s1-5907379/2026-midterm-election-senate-races",
  "2026-07-27",NOW,0),
]:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", row)

def rid(st, off):
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    return r[0] if r else None

# ================================================= 1. 뉴햄프셔 본선 대진 확정
nh = rid("NH", "U.S. Senate")
pid_ = cur.execute("SELECT MAX(politician_id)+1 FROM politician").fetchone()[0]
cur.execute("""INSERT INTO politician(politician_id,full_name,party,state_code,current_office,
    last_updated) VALUES (?,'John E. Sununu','R','NH','U.S. Senate',?)""", (pid_, NOW))
cid_ = cur.execute("SELECT MAX(candidate_id)+1 FROM candidate").fetchone()[0]
cur.execute("""INSERT INTO candidate(candidate_id,race_id,politician_id,candidate_name,
    candidate_party,is_incumbent,current_position,current_status,status_code,source_id,
    last_updated) VALUES (?,?,?,'John E. Sununu','R',0,?,'Nominee','OK',?,?)""",
    (cid_, nh, pid_, "Former U.S. Senator (2003-2009)", 80, NOW))
cur.execute("""UPDATE candidate SET current_status='Nominee', last_updated=?
    WHERE race_id=? AND candidate_name='Chris Pappas'""", (NOW, nh))
cur.execute("UPDATE election_race SET primary_date='2026-09-08', last_updated=? WHERE race_id=?",
            (NOW, nh))

# ================================================= 2. 알래스카 조사
POLLS = [
 # (주, 직위, 조사기관, 시작, 종료, n, 모집단, D-R 마진, source)
 ("AK","U.S. Senate","Alaska Survey Research","2026-08-02","2026-08-05",1371,"LV", 2.0,82),
 ("AK","U.S. Senate","Data for Progress","2026-07-28","2026-08-04",578,"LV", 6.0,83),
 ("AK","U.S. Senate","New York Times / Siena","2026-06-15","2026-06-29",593,"LV",-2.0,84),
]
pid2 = cur.execute("SELECT COALESCE(MAX(poll_id),0) FROM polling").fetchone()[0]
for st, off, house, s0, s1, n, pop, marg, src in POLLS:
    r = rid(st, off)
    if not r: continue
    pid2 += 1
    cur.execute("""INSERT INTO polling(poll_id,race_id,pollster,field_start,field_end,
        sample_size,population,margin_d_minus_r,is_average,polling_source,source_id)
        VALUES (?,?,?,?,?,?,?,?,0,?,?)""",
        (pid2, r, house, s0, s1, n, pop, marg, house, src))

# ================================================= 3. 함정 기록
conf = cur.execute("SELECT COALESCE(MAX(conflict_id),0)+1 FROM source_conflict").fetchone()[0]
cur.executemany("""INSERT INTO source_conflict(conflict_id,target_table,target_pk,target_field,
    source_id_a,value_a,source_id_b,value_b,resolution,note,logged_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",[
 (conf,"polling","NH","margin_d_minus_r",
  2,"Chris Sununu(전 주지사) 53 - Pappas 44 가상대결",
  80,"실제 공화당 후보는 John E. Sununu(전 상원의원)",
  "PREFER_B",
  "동명이인. Chris Sununu 는 2026 상원 후보가 아니며 해당 조사는 실존하지 않는 대진을 측정했다. 미적재.",
  NOW),
 (conf+1,"polling","US","race_matchup",
  2,"RealClearPolling 발췌: Brown vs Moreno / McCormick vs Casey / Hovde vs Baldwin / Rogers vs Slotkin",
  2,"모두 2024년 대진. 2026년 목록에 캐시가 섞여 노출됨",
  "PREFER_B",
  "집계 사이트 발췌는 연도와 후보명을 반드시 대조할 것. 이번 사이클에서 두 번째 발생.",
  NOW),
])

# ================================================= 4. change_log
cl = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
for et, st, note, ov, nv, when, src in [
 ("NEW_CANDIDATE","NH","예비선거(9/8) — 공화 John E. Sununu 지명(Scott Brown 상대 70:25). "
  "민주 Chris Pappas 지명(Karishma Manzur 상대 62:36). 셰이힌 은퇴 오픈시트 본선 대진 확정",
  None,"Sununu(R) vs Pappas(D)","2026-09-08",80),
 ("POLLING_CHANGE","AK","Alaska Survey Research: Peltola +2 (8/2-5, n=1371 LV). "
  "Data for Progress D+6, NYT/Siena는 6월 R+2로 편차 큼",
  "R+2 (6월 NYT/Siena)","D+2 (8월 ASR)","2026-08-19",82),
 ("RACE_RATING_CHANGE","AK","동명이인 Daniel J. Sullivan 출마로 표 분산 우려. "
  "현직 Dan S. Sullivan 의 후보 배제 시도 실패. Lean R → Toss-up 이동 사유",
  "Lean Republican","Toss Up","2026-07-27",85),
]:
    cl += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,target_pk,
        field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'election_race',?,'candidate/poll',?,?,?,?,?)""",
        (cl, et, st, st, ov, nv, when, src, note))

con.commit()

print("=== NH 본선 대진 ===")
for r in cur.execute("""SELECT candidate_name,candidate_party,current_status FROM candidate
    WHERE race_id=? ORDER BY candidate_party""", (nh,)):
    print(f"  {r[0]:<20}{r[1]}  {r[2]}")

print("\n=== 여론조사 확보 현황 ===")
for r in cur.execute("""SELECT state_code,office,poll_count,last_poll_date,latest_margin,
    poll_age_days,coverage_status FROM v_poll_coverage WHERE poll_count>0
    ORDER BY last_poll_date DESC"""):
    lead = (f"D+{r[4]:.1f}".rstrip('0').rstrip('.') if r[4] and r[4] > 0
            else (f"R+{abs(r[4]):.1f}".rstrip('0').rstrip('.') if r[4] else "—"))
    print(f"  {r[0]} {r[1]:<14}{r[2]}건  {r[3]}  {lead:>6}  {r[5]:>4}일  {r[6]}")

print("\n=== 커버리지 ===")
for r in cur.execute("SELECT coverage_status,COUNT(*) FROM v_poll_coverage GROUP BY 1 ORDER BY 2 DESC"):
    print(f"  {r[0]:<12}{r[1]:>3}")
con.close()
