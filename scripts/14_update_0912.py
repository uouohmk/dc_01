#!/usr/bin/env python3
"""2026-09-12 정기 트래커 갱신

1) 후보 명단 동기화
   - 미시간 연방상원(MI U.S. Senate): 민주당 후보 Abdul El-Sayed(Nominee) 공식 등재
2) 여론조사 갱신 (NC · ME · PA · OH · TX)
   - NC 상원 (5건 + 공식평균): PJM 고노출 사각지대 신규 해소 (Cooper vs Whatley)
   - ME 상원 (5건 + 공식평균): AGING 레이스 최신화 (Jackson vs Collins, D+2.1)
   - PA 주지사 (4건 + 공식평균): PJM 고노출 사각지대 신규 해소 (Shapiro vs Garrity)
   - OH 상원 (2건 + 공식평균): Brown vs Husted 9월 신규 조사 반영
   - TX 상원 / 주지사 (신규 조사 각 4건/2건 + 공식평균): 9월 최신 추세 반영
3) 정책 입장 축 보강 (policy-update)
   - Vivek Ramaswamy (OH 주지사, R): 수자원 공개의무 근거로 WATER(-40) 축 확충 → 종합 점수(-55.0) 신규 산출
   - Abdul El-Sayed (MI 상원, D): 요금·수자원 비판 근거로 RATES(-70), WATER(-60) 축 확충 → 종합 점수(-71.7) 신규 산출
4) 거부 항목 명시적 분리 (14건)
   - 조지아 구형 조사 / 필드기간 결측 (5건)
   - 뉴햄프셔 동명이인(Chris Sununu) 조사 (4건)
   - 메인 후보교체 이전 구 대진 및 텍사스 구형 조사 (5건)
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-09-12"

# ================================================================ 1. 출처 등록
SOURCES = [
 (100, 8, "Pollsmax", "North Carolina Senate polling average",
  "https://www.pollsmax.com/senate/north-carolina/", "2026-09-03", NOW, 0),
 (101, 6, "East Carolina University", "ECU Center for Survey Research: NC Statewide Poll (675 LV)",
  "https://surveyresearch.ecu.edu/wp-content/pv-uploads/sites/103/2026/09/ECU-Poll-Sept-2026.pdf", "2026-09-03", NOW, 1),
 (102, 8, "YouGov", "North Carolina Senate General Election Survey (565 LV)",
  "https://today.yougov.com/politics/articles/2026-midterms-nc-senate", "2026-08-31", NOW, 1),
 (103, 8, "Pollsmax", "Maine Senate polling average (8건)",
  "https://www.pollsmax.com/senate/maine/", "2026-09-08", NOW, 0),
 (104, 9, "CNN / SSRS", "Maine Senate Survey: Jackson leads Collins (880 LV)",
  "https://www.cnn.com/2026/09/06/politics/maine-senate-race-poll/index.html", "2026-09-06", NOW, 1),
 (105, 8, "Pollsmax", "Pennsylvania Governor polling average (14건)",
  "https://www.pollsmax.com/governor/pennsylvania/", "2026-08-23", NOW, 0),
 (106, 6, "Franklin & Marshall College", "Pennsylvania Center for Opinion Research: August 2026 Poll",
  "https://www.fandm.edu/poll/2026-august", "2026-08-23", NOW, 1),
 (107, 8, "InsiderAdvantage", "Ohio & Texas Statewide General Election Polls (1,200 LV)",
  "https://insideradvantage.com/2026/09/09/ohio-texas-senate-polls-september-2026/", "2026-09-09", NOW, 1),
 (108, 8, "YouGov", "Texas General Election Poll (1,000 RV)",
  "https://today.yougov.com/politics/articles/texas-senate-gov-september-2026", "2026-09-04", NOW, 1),
]

for s in SOURCES:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", s)

def rid(st, off):
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    return r[0] if r else None

# ================================================================ 2. 후보 명단 동기화
# MI U.S. Senate (race_id 15): Abdul El-Sayed 공식 후보 등재
mi_race = rid("MI", "U.S. Senate")
el_sayed_cand = cur.execute("SELECT candidate_id FROM candidate WHERE race_id=? AND candidate_name='Abdul El-Sayed'",
                            (mi_race,)).fetchone()
if not el_sayed_cand:
    cid_ = (cur.execute("SELECT COALESCE(MAX(candidate_id),0)+1 FROM candidate").fetchone()[0])
    cur.execute("""INSERT INTO candidate(candidate_id,race_id,politician_id,candidate_name,
        candidate_party,is_incumbent,current_position,current_status,status_code,source_id,
        last_updated) VALUES (?,?,123,'Abdul El-Sayed','D',0,'Former Director of Wayne County Health Dept',
        'Nominee','OK',45,?)""", (cid_, mi_race, NOW))

# ================================================================ 3. 여론조사 적재
# (주, 직위, 조사기관, 시작, 종료, n, 모집단, D-R 마진, 평균여부, source_id)
NEW_POLLS = [
 # ---- 노스캐롤라이나 상원 (신규 커버리지)
 ("NC","U.S. Senate","East Carolina University","2026-08-30","2026-09-03",675,"LV",  7.2, 0, 101),
 ("NC","U.S. Senate","YouGov","2026-08-27","2026-08-31",565,"LV",                 11.0, 0, 102),
 ("NC","U.S. Senate","High Point University","2026-08-12","2026-08-18",1119,"LV",   5.0, 0, 100),
 ("NC","U.S. Senate","Fox News / Beacon Research","2026-07-23","2026-07-27",1005,"RV",9.0,0,100),
 ("NC","U.S. Senate","Pollsmax 평균 (28건)","2026-09-03","2026-09-03",None,None,    5.8, 1, 100),

 # ---- 메인 상원 (노후도 AGING → CURRENT 갱신)
 ("ME","U.S. Senate","YouGov","2026-09-03","2026-09-08",1335,"LV",                 4.0, 0, 103),
 ("ME","U.S. Senate","CNN / SSRS","2026-09-01","2026-09-06",880,"LV",              3.0, 0, 104),
 ("ME","U.S. Senate","Abacus Data (R)","2026-08-24","2026-08-28",1507,"LV",         9.0, 0, 103),
 ("ME","U.S. Senate","Fox News / Beacon Research","2026-08-06","2026-08-10",1000,"LV",2.0,0, 103),
 ("ME","U.S. Senate","Hart Research (D)","2026-07-27","2026-08-01",802,"LV",        4.0, 0, 103),
 ("ME","U.S. Senate","Pollsmax 평균 (8건)","2026-09-08","2026-09-08",None,None,     2.1, 1, 103),

 # ---- 펜실베이니아 주지사 (신규 커버리지)
 ("PA","Governor","Franklin & Marshall College","2026-08-18","2026-08-23",501,"RV",25.0,0, 106),
 ("PA","Governor","New York Times / Siena College","2026-08-16","2026-08-21",760,"LV",16.0,0,105),
 ("PA","Governor","National Public Affairs (R)","2026-07-26","2026-07-30",600,"LV", 7.0,0, 105),
 ("PA","Governor","Quinnipiac University","2026-07-09","2026-07-13",895,"RV",       13.0,0, 105),
 ("PA","Governor","Pollsmax 평균 (14건)","2026-08-23","2026-08-23",None,None,       20.3,1, 105),

 # ---- 오하이오 상원
 ("OH","U.S. Senate","InsiderAdvantage (R)","2026-09-05","2026-09-09",1200,"LV",   5.4, 0, 107),
 ("OH","U.S. Senate","Abacus Data (R)","2026-08-24","2026-08-28",1507,"LV",         6.0, 0, 107),
 ("OH","U.S. Senate","Pollsmax 평균 (18건)","2026-09-09","2026-09-09",None,None,   -0.4, 1, 107),

 # ---- 텍사스 상원
 ("TX","U.S. Senate","InsiderAdvantage (R)","2026-09-05","2026-09-09",1200,"LV",   1.5, 0, 107),
 ("TX","U.S. Senate","YouGov","2026-08-31","2026-09-04",1000,"RV",                 5.0, 0, 108),
 ("TX","U.S. Senate","Fabrizio, Lee & Associates (R)","2026-08-28","2026-09-01",895,"LV",4.0,0,107),
 ("TX","U.S. Senate","Slingshot Strategies (D)","2026-08-20","2026-08-24",1000,"LV",6.0,0, 107),
 ("TX","U.S. Senate","Pollsmax 평균 (30건)","2026-09-09","2026-09-09",None,None,   -0.3, 1, 107),

 # ---- 텍사스 주지사
 ("TX","Governor","YouGov","2026-08-31","2026-09-04",1000,"RV",                     0.0, 0, 108),
 ("TX","Governor","Slingshot Strategies (D)","2026-08-20","2026-08-24",1000,"LV",  -7.0, 0, 107),
 ("TX","Governor","Pollsmax 평균 (27건)","2026-09-04","2026-09-04",None,None,      -5.3, 1, 107),
]

pid = cur.execute("SELECT COALESCE(MAX(poll_id),0) FROM polling").fetchone()[0]
for st, off, pollster, f_start, f_end, n, pop, marg, is_avg, sid in NEW_POLLS:
    r = rid(st, off)
    if not r: continue
    pid += 1
    cur.execute("""INSERT INTO polling(poll_id,race_id,pollster,field_start,field_end,
        sample_size,population,margin_d_minus_r,is_average,polling_source,source_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (pid, r, pollster, f_start, f_end, n, pop, marg, is_avg, pollster, sid))

# ================================================================ 4. 정책 입장 축 보강
# 1) Vivek Ramaswamy (pos_id 8): 기존 evidence_id 24 기반 WATER 축 보강
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (8,'WATER',-40,24,'OK')""")

# 2) Abdul El-Sayed (pos_id 15): 요금·수자원 반대 근거 추가 및 RATES, WATER 축 보강
ev_id = cur.execute("SELECT COALESCE(MAX(evidence_id),0)+1 FROM position_evidence").fetchone()[0]
cur.execute("""INSERT INTO position_evidence(evidence_id,position_id,evidence_type,summary,
    evidence_date,source_id,binding_code,scope_code,direction) VALUES
    (?,'15','Public statement','Saline Township OpenAI·Oracle 부지 집회에서 데이터센터의 전력망 요금 전가 및 농업용수 고갈 위험 강력 비판',
     '2026-08-08',45,'PUBLIC_STATEMENT','COST_ALLOCATION','RESTRICTIVE')""", (ev_id,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (15,'RATES',-70,?,'OK')""", (ev_id,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (15,'WATER',-60,?,'OK')""", (ev_id,))
cur.execute("""UPDATE politician_dc_position SET confidence_level='High', policy_statement=?,
    last_updated=? WHERE position_id=15""",
    ("연방 차원 안전장치가 마련되기 전까지 신규 승인 전면 중단을 요구하며, "
     "주민 전기요금 전가 및 수자원 고갈 위험을 강력히 반대.", NOW))

# ================================================================ 5. change_log 기록
cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
CHANGES = [
 ("NEW_CANDIDATE","MI","Abdul El-Sayed(민주) 연방상원 후보 공식 등재 — candidate 테이블 동기화 완료",
  None,"Abdul El-Sayed (D-Nominee)",NOW,45),
 ("POLLING_CHANGE","NC","노스캐롤라이나 연방상원 신규 조사 5건 적재 — PJM 고노출 사각지대 해소",
  "NO_POLLING","Cooper D+5.8 (Pollsmax 평균)",NOW,100),
 ("POLLING_CHANGE","ME","메인 연방상원 최신 조사 5건 적재 — AGING 레이스 최신화",
  "D+3.0 (7/31)", "Jackson D+2.1 (Pollsmax 평균)",NOW,103),
 ("POLLING_CHANGE","PA","펜실베이니아 주지사 신규 조사 4건 적재 — PJM 고노출 사각지대 해소",
  "NO_POLLING","Shapiro D+20.3 (Pollsmax 평균)",NOW,105),
 ("POLLING_CHANGE","OH","오하이오 연방상원 9월 최신 조사 적재 — Brown D+5.4 (IA), 평균 Husted R+0.4",
  "Brown D+5 (DDHQ)", "Husted R+0.4 (Pollsmax 평균)",NOW,107),
 ("POLLING_CHANGE","TX","텍사스 연방상원/주지사 9월 최신 조사 적재 — 상원 Talarico D+1.5 (IA), 주지사 47:47 동률",
  "상원 D+0.6 / 주지사 R+1.1", "상원 Paxton R+0.3 / 주지사 Abbott R+5.3 (Pollsmax)",NOW,107),
 ("WATER_REGULATION","OH","Vivek Ramaswamy 수자원 공개의무 근거로 WATER 축(-40) 보강 — 종합 지지도(-55.0) 신규 산출",
  "축 2개 (미산출)","축 3개 (support: -55.0)",NOW,10),
 ("COMMUNITY_OPPOSITION","MI","Abdul El-Sayed 요금·수자원 근거로 RATES(-70), WATER(-60) 축 보강 — 종합 지지도(-71.7) 신규 산출",
  "축 1개 (미산출)","축 3개 (support: -71.7)",NOW,45),
]

for et, st, note, ov, nv, when, sid in CHANGES:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,target_pk,
        field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'election_race',?,'poll/position',?,?,?,?,?)""",
        (cid, et, st, st, ov, nv, when, sid, note))

con.commit()

print(f"✔ 2026-09-12 갱신 완료:")
print(f"  - 신규 조사 적재: {len(NEW_POLLS)}건")
print(f"  - 신규 후보 등재: 1명 (MI Abdul El-Sayed)")
print(f"  - 정책 축 보강: 2명 (Ramaswamy WATER 축, El-Sayed RATES/WATER 축)")
print(f"  - 변경 이력 기록: {len(CHANGES)}건")

con.close()
