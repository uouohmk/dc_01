#!/usr/bin/env python3
"""2026-09-12 격전지 및 노후 레이스 여론조사 갱신

1) STALE 레이스 해소
   - 켄터키 연방상원 (KY U.S. Senate): Global Strategy Group(8/27, R+9.0) 및 Pollsmax 평균(R+9.6) 적재
     → DB 내 유일했던 STALE(265일) 레이스 해소, CURRENT로 전환 (DB 전체 STALE = 0개 달성)
2) AGING 레이스 해소
   - 알래스카 연방상원 (AK U.S. Senate): Alaska Survey Research(8/23, D+2.0) 및 Pollsmax 평균(R+1.0) 적재
     → 8/5 이후 공백이던 AGING(36일) 상태에서 CURRENT로 복귀
3) 신규 격전지 사각지대(NO_POLLING) 해소
   - 아이오와 주지사 (IA Governor): Emerson(9/1, D+3.1) 등 6건 + Pollsmax 평균(D+4.2) 적재
   - 네바다 주지사 (NV Governor): POS(7/29, R+9.0) 등 4건 + Pollsmax 평균(R+4.3) 적재
4) 격전지 표본 보강
   - 아이오와 연방상원 (IA U.S. Senate): Emerson(9/1, R+4.4) 등 6건 + Pollsmax 평균(R+4.8) 적재
5) 엄격한 거부 항목 (56건)
   - 후보 명단 불일치: MI 주지사(Benson vs James, 24건), WI 주지사(Crowley vs Tiffany, 6건), AZ 주지사(Hobbs vs Biggs, 17건)
   - 필드기간 결측 및 2025년 구형 조사: GA 상원, IA/NV 구형 조사 (9건)
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-09-12"

# ================================================================ 1. 출처 등록
SOURCES = [
 (110, 8, "Pollsmax", "Alaska Senate polling average (14건)",
  "https://www.pollsmax.com/senate/alaska/", "2026-08-23", NOW, 0),
 (111, 8, "Alaska Survey Research", "Alaska Statewide Senate Survey (1,495 LV)",
  "https://www.alaskasurveyresearch.com/polls/2026-senate-august-update", "2026-08-23", NOW, 1),
 (112, 8, "Pollsmax", "Kentucky Senate polling average (2건)",
  "https://www.pollsmax.com/senate/kentucky/", "2026-08-27", NOW, 0),
 (113, 8, "Global Strategy Group", "Kentucky Senate General Election Poll (600 LV)",
  "https://www.globalstrategygroup.com/insights/kentucky-senate-2026-poll/", "2026-08-27", NOW, 1),
 (114, 8, "Pollsmax", "Iowa Senate polling average (14건)",
  "https://www.pollsmax.com/senate/iowa/", "2026-09-01", NOW, 0),
 (115, 8, "Emerson College Polling", "Iowa 2026 Senate & Governor Poll (750 LV)",
  "https://emersoncollegepolling.com/iowa-2026-senate-and-governor-poll/", "2026-09-01", NOW, 1),
 (116, 8, "Pollsmax", "Iowa Governor polling average (7건)",
  "https://www.pollsmax.com/governor/iowa/", "2026-09-01", NOW, 0),
 (117, 8, "Pollsmax", "Nevada Governor polling average (10건)",
  "https://www.pollsmax.com/governor/nevada/", "2026-07-29", NOW, 0),
 (118, 8, "Public Opinion Strategies", "Nevada Statewide Governor Survey (600 LV)",
  "https://pos.org/nevada-governor-race-poll-july-2026/", "2026-07-29", NOW, 1),
]

for s in SOURCES:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", s)

def rid(st, off):
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    return r[0] if r else None

# ================================================================ 2. 여론조사 적재
# (주, 직위, 조사기관, 시작, 종료, n, 모집단, D-R 마진, 평균여부, source_id)
POLLS = [
 # ---- 알래스카 상원 (AGING → CURRENT 전환)
 ("AK","U.S. Senate","Alaska Survey Research","2026-08-20","2026-08-23",1495,"LV",  2.0, 0, 111),
 ("AK","U.S. Senate","Pollsmax 평균 (14건)","2026-08-23","2026-08-23",None,None,   -1.0, 1, 110),

 # ---- 켄터키 상원 (STALE → CURRENT 전환: DB 내 STALE 소멸)
 ("KY","U.S. Senate","Global Strategy Group (D)","2026-08-24","2026-08-27",600,"LV", -9.0, 0, 113),
 ("KY","U.S. Senate","Pollsmax 평균 (2건)","2026-08-27","2026-08-27",None,None,    -9.6, 1, 112),

 # ---- 아이오와 상원 (표본 확충 및 9월 최신화)
 ("IA","U.S. Senate","Emerson College","2026-08-29","2026-09-01",750,"LV",          -4.4, 0, 115),
 ("IA","U.S. Senate","Global Strategy Group (D)","2026-08-27","2026-08-31",800,"LV",  4.0, 0, 114),
 ("IA","U.S. Senate","Wedgewood Polls","2026-08-26","2026-08-29",600,"LV",          -2.0, 0, 114),
 ("IA","U.S. Senate","Abacus Data (R)","2026-08-24","2026-08-28",1507,"LV",          9.0, 0, 114),
 ("IA","U.S. Senate","Suffolk University","2026-08-18","2026-08-22",500,"LV",       -4.6, 0, 114),
 ("IA","U.S. Senate","Emerson College","2026-08-02","2026-08-04",712,"LV",          -2.5, 0, 115),
 ("IA","U.S. Senate","Pollsmax 평균 (14건)","2026-09-01","2026-09-01",None,None,    -4.8, 1, 114),

 # ---- 아이오와 주지사 (NO_POLLING 사각지대 해소)
 ("IA","Governor","Emerson College","2026-08-29","2026-09-01",750,"LV",              3.1, 0, 115),
 ("IA","Governor","Wedgewood Polls","2026-08-26","2026-08-29",600,"LV",              5.0, 0, 116),
 ("IA","Governor","Suffolk University","2026-08-18","2026-08-22",500,"LV",           4.2, 0, 116),
 ("IA","Governor","Emerson College","2026-08-02","2026-08-04",712,"LV",              5.7, 0, 115),
 ("IA","Governor","Fox News / Beacon Research","2026-06-23","2026-06-27",1003,"RV",  9.0, 0, 116),
 ("IA","Governor","New York Times / Siena College","2026-06-15","2026-06-27",600,"LV",1.0,0, 116),
 ("IA","Governor","Pollsmax 평균 (7건)","2026-09-01","2026-09-01",None,None,         4.2, 1, 116),

 # ---- 네바다 주지사 (NO_POLLING 사각지대 해소)
 ("NV","Governor","Public Opinion Strategies (R)","2026-07-27","2026-07-29",600,"LV", -9.0, 0, 118),
 ("NV","Governor","Tarrance Group (R)","2026-07-25","2026-07-29",555,"LV",           -7.0, 0, 117),
 ("NV","Governor","Grassroots Targeting (R)","2026-07-08","2026-07-16",2500,"LV",   -12.0, 0, 117),
 ("NV","Governor","Public Policy Polling (D)","2026-07-15","2026-07-16",558,"LV",     0.0, 0, 117),
 ("NV","Governor","Pollsmax 평균 (10건)","2026-07-29","2026-07-29",None,None,        -4.3, 1, 117),
]

pid = cur.execute("SELECT COALESCE(MAX(poll_id),0) FROM polling").fetchone()[0]
for st, off, pollster, f_start, f_end, n, pop, marg, is_avg, sid in POLLS:
    r = rid(st, off)
    if not r: continue
    pid += 1
    cur.execute("""INSERT INTO polling(poll_id,race_id,pollster,field_start,field_end,
        sample_size,population,margin_d_minus_r,is_average,polling_source,source_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (pid, r, pollster, f_start, f_end, n, pop, marg, is_avg, pollster, sid))

# ================================================================ 3. change_log 기록
cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
CHANGES = [
 ("POLLING_CHANGE","KY","켄터키 연방상원 Global Strategy Group(8/27, R+9) 적재 — STALE 해소, CURRENT 전환 (STALE 레이스 0개 달성)",
  "STALE (2025-12, R+11)","CURRENT (Barr R+9.6, Pollsmax 평균)",NOW,112),
 ("POLLING_CHANGE","AK","알래스카 연방상원 ASR(8/23, D+2) 적재 — AGING 해소, CURRENT 복귀",
  "AGING (8/5 D+2)", "CURRENT (Sullivan R+1.0, Pollsmax 평균)",NOW,110),
 ("POLLING_CHANGE","IA","아이오와 연방상원 9월 최신 조사 6건 적재 — Hinson R+4.8 (Pollsmax 평균)",
  "Hinson R+4.0 (1건)","Hinson R+4.8 (Pollsmax 평균, 7건 확보)",NOW,114),
 ("POLLING_CHANGE","IA","아이오와 주지사 신규 조사 6건 적재 — Sand D+4.2 (Pollsmax 평균), NO_POLLING 사각지대 해소",
  "NO_POLLING","Rob Sand D+4.2 (Pollsmax 평균)",NOW,116),
 ("POLLING_CHANGE","NV","네바다 주지사 신규 조사 4건 적재 — Lombardo R+4.3 (Pollsmax 평균), NO_POLLING 사각지대 해소",
  "NO_POLLING","Joe Lombardo R+4.3 (Pollsmax 평균)",NOW,117),
]

for et, st, note, ov, nv, when, sid in CHANGES:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,target_pk,
        field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'election_race',?,'polling',?,?,?,?,?)""",
        (cid, et, st, st, ov, nv, when, sid, note))

con.commit()

print(f"✔ 2026-09-12 여론조사 갱신 완료:")
print(f"  - 신규 조사 적재: {len(POLLS)}건")
print(f"  - 변경 이력 기록: {len(CHANGES)}건")

con.close()
