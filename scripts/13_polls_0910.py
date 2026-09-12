#!/usr/bin/env python3
"""2026-09-10 격전지 여론조사 일괄 갱신

대상: AK · OH · TX · MI (요청) + 확보된 격전지
필드 기간이 명시된 조사만 적재한다. 집계 평균은 is_average=1 로 구분한다.

주의: 미시간에서 리드가 바뀌었다.
      Glengariff(9/3 종료)는 Rogers +1.4 로, 그 직전 조사들과 방향이 반대다.
      단일 조사로 판단하지 말 것 — 평균은 여전히 D+1.8 이다.
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-09-10"

for row in [
 (90,8,"Detroit News / WDIV / Glengariff Group","Michigan statewide poll, 600 LV",
  "https://www.clickondetroit.com/news/local/2026/09/08/poll-which-us-senate-candidates-are-most-favorable-to-michigan-voters/",
  "2026-09-08",NOW,1),
 (91,8,"EPIC-MRA","Michigan Senate poll",
  "https://www.pollsmax.com/senate/michigan/","2026-08-28",NOW,0),
 (92,8,"Pollsmax","Michigan Senate polling average (24건)",
  "https://www.pollsmax.com/senate/michigan/","2026-09-09",NOW,0),
 (93,8,"Decision Desk HQ","2026 Senate polling averages",
  "https://decisiondeskhq.substack.com/p/el-sayed-rogers-michigan-senate-trump-approval-generic-ballot-2026-midterms",
  "2026-08-20",NOW,0),
 (94,8,"Wedgewood Polls","Ohio Senate & Governor poll",
  "https://thehill.com/homenews/campaign/6031596-brown-acton-lead-ohio-polls/","2026-08-14",NOW,0),
 (95,8,"Emerson College Polling / Nexstar","Texas 2026 poll",
  "https://emersoncollegepolling.com/texas-2026-poll-paxton-and-talarico/","2026-08-10",NOW,1),
 (96,8,"Overton Insights / TPPF","Texas poll, 1167 LV",
  "https://overtoninsights.com/poll/september-2026/","2026-09-07",NOW,1),
 (97,9,"The Texan","New poll shows Texans split on Paxton and Talarico, opposed to data centers",
  "https://thetexan.news/elections/2026/new-poll-shows-texans-split-on-paxton-and-talarico-opposed-to-flock-and-data-centers/article_45a2d21c-9c79-417e-b724-6070cfd03887.html",
  "2026-09-02",NOW,0),
 (98,9,"Newsweek","El-Sayed dealt polling blow in Michigan race against Rogers",
  "https://www.newsweek.com/abdul-el-sayed-polling-blow-michigan-senate-mike-rogers-12421084",
  "2026-09-09",NOW,0),
]:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", row)

def rid(st, off):
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    return r[0] if r else None

# (주, 직위, 조사기관, 시작, 종료, n, 모집단, D-R 마진, 평균여부, source)
POLLS = [
 # ---- 미시간: 리드 역전 구간
 ("MI","U.S. Senate","Detroit News/WDIV/Glengariff","2026-08-31","2026-09-03",600,"LV",-1.4,0,90),
 ("MI","U.S. Senate","EPIC-MRA","2026-08-28","2026-08-28",None,"LV",         4.0,0,91),
 ("MI","U.S. Senate","Pollsmax 평균 (24건)","2026-09-09","2026-09-09",None,None, 1.8,1,92),
 ("MI","U.S. Senate","Decision Desk HQ 평균","2026-08-20","2026-08-20",None,None, 2.0,1,93),

 # ---- 오하이오
 ("OH","U.S. Senate","Wedgewood Polls","2026-08-11","2026-08-13",None,None,     4.0,0,94),
 ("OH","U.S. Senate","Decision Desk HQ 평균","2026-08-20","2026-08-20",None,None,5.0,1,93),
 ("OH","Governor",   "Decision Desk HQ 평균","2026-08-20","2026-08-20",None,None,0.0,1,93),

 # ---- 텍사스
 ("TX","U.S. Senate","Overton Insights/TPPF","2026-08-24","2026-08-26",1167,"LV", 0.6,0,96),
 ("TX","Governor",   "Overton Insights/TPPF","2026-08-24","2026-08-26",1167,"LV",-1.1,0,96),
 ("TX","U.S. Senate","Emerson College/Nexstar","2026-08-05","2026-08-08",None,"LV",-1.0,0,95),
 ("TX","Governor",   "Emerson College/Nexstar","2026-08-05","2026-08-08",None,"LV",-4.0,0,95),
]
pid = cur.execute("SELECT COALESCE(MAX(poll_id),0) FROM polling").fetchone()[0]
added = 0
for st, off, house, s0, s1, n, pop, marg, avg, src in POLLS:
    r = rid(st, off)
    if not r:
        print("  레이스 없음:", st, off); continue
    pid += 1; added += 1
    cur.execute("""INSERT INTO polling(poll_id,race_id,pollster,field_start,field_end,
        sample_size,population,margin_d_minus_r,is_average,polling_source,source_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (pid, r, house, s0, s1, n, pop, marg, avg, house, src))

# ---- 텍사스: 데이터센터 반대 여론 지속 확인 (UT/TxPP 8월 조사와 별개 출처)
oid = cur.execute("SELECT MAX(opinion_id) FROM dc_public_opinion").fetchone()[0] + 1
cur.execute("""INSERT OR REPLACE INTO dc_public_opinion(opinion_id,state_code,pollster,
    field_start,field_end,sample_size,population,metric,subgroup,support_pct,oppose_pct,
    net_pct,source_id) VALUES (?,'TX','Overton Insights/TPPF','2026-08-24','2026-08-26',
    1167,'LV','LOCAL_CONSTRUCTION','ALL',NULL,NULL,NULL,97)""", (oid,))

cl = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
for et, st, note, ov, nv, when, src in [
 ("POLLING_CHANGE","MI","[리드 역전] Detroit News/Glengariff: Rogers 45.8 - El-Sayed 44.4 (8/31~9/3, "
  "n=600 LV, ±4). 조사기관이 직접 'toss-up'으로 규정. 다만 '반드시 투표' 층에서는 El-Sayed 46.7-44.4 우위",
  "D+4 (EPIC-MRA 8/28)","R+1.4 (Glengariff 9/3)","2026-09-08",90),
 ("POLLING_CHANGE","MI","Pollsmax 24건 평균은 여전히 El-Sayed +1.8 (46.0-44.2). "
  "단일 조사와 평균이 방향이 다르다",None,"평균 D+1.8","2026-09-09",92),
 ("POLLING_CHANGE","OH","Wedgewood(8/11~13): Brown 48 - Husted 44. DDHQ 평균 Brown +5. "
  "2024년 트럼프 투표자의 9%가 상원 레이스에서 미결정",None,"D+4 ~ D+5","2026-08-14",94),
 ("POLLING_CHANGE","OH","주지사: DDHQ 평균 Acton 47 - Ramaswamy 47 동률",
  "R+1 (Impact 7월)","동률 (DDHQ 8월)","2026-08-20",93),
 ("POLLING_CHANGE","TX","Overton Insights/TPPF(8/24~26, n=1167 LV): 상원 Talarico +0.6, "
  "주지사 Abbott +1.1. 조사기관이 '주지사 레이스가 오차범위 안에 든 것이 가장 놀라운 결과'라고 평가",
  None,"상원 D+0.6 · 주지사 R+1.1","2026-09-07",96),
 ("POLLING_CHANGE","TX","Emerson/Nexstar(8/5~8): 상원 Paxton 47 - Talarico 46. "
  "연령별 분화 — 50세 미만 Talarico +15, 50세 이상 Paxton +11",None,"R+1","2026-08-10",95),
 ("COMMUNITY_OPPOSITION","TX","Overton Insights/TPPF 조사에서도 데이터센터 반대 지속 확인. "
  "Hinojosa는 Abbott 책임론, Paxton은 추가 규제안 발표로 대응",None,"반대 지속","2026-09-02",97),
]:
    cl += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,target_pk,
        field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'polling',?,'margin',?,?,?,?,?)""",
        (cl, et, st, st, ov, nv, when, src, note))
con.commit()

print(f"조사 {added}건 적재\n")
print("=== 격전지 4개 주 조사 전체 ===")
for st in ("AK","OH","TX","MI"):
    print(f"\n[{st}]")
    for r in cur.execute("""SELECT r.office, p.pollster, p.field_start, p.field_end,
        p.sample_size, p.margin_d_minus_r, p.is_average FROM polling p
        JOIN election_race r ON r.race_id=p.race_id WHERE r.state_code=?
        ORDER BY r.office, p.field_end DESC""", (st,)):
        lead = f"D+{r[5]:g}" if r[5] > 0 else (f"R+{abs(r[5]):g}" if r[5] < 0 else "동률")
        avg = " [평균]" if r[6] else ""
        n = f"n={r[4]}" if r[4] else ""
        print(f"  {r[0]:<13}{lead:>7}  {r[1]:<32}{r[3]}  {n}{avg}")

print("\n=== 전체 커버리지 ===")
for r in cur.execute("SELECT coverage_status,COUNT(*) FROM v_poll_coverage GROUP BY 1 ORDER BY 2 DESC"):
    print(f"  {r[0]:<12}{r[1]:>3}")
con.close()
