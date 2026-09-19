#!/usr/bin/env python3
"""2026-09-19 정기 트래커 갱신

1) 여론조사 갱신 (GA · NH · MI · FL — 16건)
   - GA 상원 (3건 + 공식평균): Ossoff vs Collins 최신 조사 적재 (PJM/남동부 사각지대 해소)
   - NH 상원 (5건 + 공식평균): Pappas vs John E. Sununu 최신 조사 적재 (동명이인 분류 검증 완료)
   - MI 상원 (2건 + 공식평균): El-Sayed vs Rogers 9월 최신 추세 반영 (D+1.4 박빙 유지)
   - FL 상원 (2건 + 공식평균): Nixon vs Moody 신규 조사 적재 (고노출 사각지대 해소)
2) 정책 입장 축 보강 (policy-update — 3명)
   - Stacy Garrity (PA 주지사, R): 천연가스 발전 인프라 지원 근거로 POWER(+35) 축 확충 → 종합 지지도(-36.8) 신규 산출
   - Amy Acton (OH 주지사, D): 수자원 영향평가 의무화 근거로 WATER(-50) 축 확충 → 종합 지지도(-63.5) 신규 산출
   - Sherrod Brown (OH 상원, D): 데이터센터 세제 감면 공격 근거로 TAX(-65) 축 확충 → 종합 지지도(-57.3) 신규 산출
3) 엄격한 거부 항목 분리 (38건)
   - FL 주지사: David Jolly vs Byron Donalds (19건, DB 공천후보 Jason Pizzo와 불일치)
   - FL 상원: Quantus 조사(필드기간 결측 1건) 및 봄철 구형 조사 3건 (총 4건)
   - NH 상원: 전 주지사 Chris Sununu 가상 대진 조사 (4건, 본선 후보 John E. Sununu와 불일치)
   - GA 상원: 필드기간 결측 및 비공식 조사 (5건)
   - 기타 주지사: MI·WI·AZ 미등록 후보 조사 (6건)
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-09-19"

# ================================================================ 1. 출처 등록
SOURCES = [
 (120, 8, "Pollsmax", "Georgia Senate polling average (18건)",
  "https://www.pollsmax.com/senate/georgia/", "2026-08-17", NOW, 0),
 (121, 8, "Fabrizio, Lee & Associates", "Georgia Senate General Election Survey (1,060 LV)",
  "https://fabriziolee.com/polls/2026-georgia-senate-july", "2026-07-16", NOW, 1),
 (122, 8, "Pollsmax", "New Hampshire Senate polling average (12건)",
  "https://www.pollsmax.com/senate/new-hampshire/", "2026-08-30", NOW, 0),
 (123, 8, "University of New Hampshire", "UNH Survey Center: NH Statewide Senate Poll (1,878 LV)",
  "https://cola.unh.edu/survey-center/publication/2026/08/nh-senate-poll", "2026-08-24", NOW, 1),
 (124, 9, "CNN / SSRS", "Michigan Senate Survey: El-Sayed leads Rogers (843 LV)",
  "https://www.cnn.com/2026/09/06/politics/michigan-senate-race-poll/index.html", "2026-09-06", NOW, 1),
 (125, 8, "Trafalgar Group", "Michigan Statewide Senate Poll (1,079 LV)",
  "https://thetrafalgargroup.org/polls/2026-michigan-senate-september", "2026-09-09", NOW, 1),
 (126, 8, "Pollsmax", "Florida Senate polling average (6건)",
  "https://www.pollsmax.com/senate/florida/", "2026-09-10", NOW, 0),
 (127, 8, "Change Research", "Florida Statewide Senate Survey (1,107 LV)",
  "https://changeresearch.com/polls/2026-florida-senate-september", "2026-09-09", NOW, 1),
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
NEW_POLLS = [
 # ---- 조지아 연방상원 (Ossoff vs Collins)
 ("GA","U.S. Senate","Fabrizio, Lee & Associates (R)","2026-07-13","2026-07-16",1060,"LV", 9.0, 0, 121),
 ("GA","U.S. Senate","Wick Insights","2026-06-27","2026-06-30",1175,"LV",                 3.8, 0, 120),
 ("GA","U.S. Senate","Fox News / Beacon Research","2026-06-23","2026-06-27",1002,"RV",    13.0, 0, 120),
 ("GA","U.S. Senate","Pollsmax 평균 (18건)","2026-08-17","2026-08-17",None,None,           7.5, 1, 120),

 # ---- 뉴햄프셔 연방상원 (Pappas vs John E. Sununu)
 ("NH","U.S. Senate","Fabrizio, Lee & Associates (R)","2026-08-28","2026-08-30",600,"LV", -1.0, 0, 122),
 ("NH","U.S. Senate","University of New Hampshire","2026-08-21","2026-08-24",1878,"LV",   -2.0, 0, 123),
 ("NH","U.S. Senate","University of New Hampshire","2026-08-15","2026-08-18",1411,"LV",    7.0, 0, 123),
 ("NH","U.S. Senate","Peak Insights (R)","2026-06-24","2026-06-27",500,"LV",              1.0, 0, 122),
 ("NH","U.S. Senate","Saint Anselm College","2026-06-24","2026-06-25",739,"LV",           6.0, 0, 122),
 ("NH","U.S. Senate","Pollsmax 평균 (12건)","2026-08-30","2026-08-30",None,None,          5.3, 1, 122),

 # ---- 미시간 연방상원 (El-Sayed vs Rogers)
 ("MI","U.S. Senate","Trafalgar Group (R)","2026-09-07","2026-09-09",1079,"LV",           1.5, 0, 125),
 ("MI","U.S. Senate","CNN / SSRS","2026-09-02","2026-09-06",843,"LV",                     3.0, 0, 124),
 ("MI","U.S. Senate","Pollsmax 평균 (27건)","2026-09-09","2026-09-09",None,None,          1.4, 1, 92),

 # ---- 플로리다 연방상원 (Nixon vs Moody)
 ("FL","U.S. Senate","Change Research (D)","2026-09-06","2026-09-09",1107,"LV",            0.0, 0, 127),
 ("FL","U.S. Senate","University of North Florida","2026-07-08","2026-07-17",848,"LV",   -8.0, 0, 126),
 ("FL","U.S. Senate","Pollsmax 평균 (6건)","2026-09-10","2026-09-10",None,None,          -6.1, 1, 126),
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

# ================================================================ 3. 정책 입장 축 보강
# 1) Stacy Garrity (PA Governor, R, pos_id 6): 천연가스 발전 인프라 지원 POWER(+35) 보강
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (6,'POWER',35,20,'OK')""")
cur.execute("""UPDATE politician_dc_position SET confidence_level='Medium', policy_statement=?,
    last_updated=? WHERE position_id=6""",
    ("향후 데이터센터 신규 개발의 '일시 중단'을 요구하면서도 주내 천연가스 기반 발전 설비 "
     "연계 유치에 대해서는 우호적 입장을 유지.", NOW))

# 2) Amy Acton (OH Governor, D, pos_id 7): 수자원 보호·영향평가 의무화 WATER(-50) 보강
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (7,'WATER',-50,21,'OK')""")
cur.execute("""UPDATE politician_dc_position SET confidence_level='Medium', policy_statement=?,
    last_updated=? WHERE position_id=7""",
    ("조건부 모라토리엄 및 데이터센터 수자원 소비 영향평가 의무화, 주민 요금보호 법안 지지.", NOW))

# 3) Sherrod Brown (OH U.S. Senate, D, pos_id 10): 빅테크 세제 감면 혜택 공격 TAX(-65) 보강
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (10,'TAX',-65,27,'OK')""")
cur.execute("""UPDATE politician_dc_position SET confidence_level='Medium', policy_statement=?,
    last_updated=? WHERE position_id=10""",
    ("Husted의 부지사 시절 세제감면을 강하게 공격하며 빅테크 세제특혜 폐지 및 전력비용 부담을 촉구.", NOW))

# ================================================================ 4. change_log 기록
cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
CHANGES = [
 ("POLLING_CHANGE","GA","조지아 연방상원 신규 조사 3건 + Pollsmax 평균 적재 — PJM/남동부 사각지대 해소 (Ossoff D+7.5)",
  "NO_POLLING","Ossoff D+7.5 (Pollsmax 평균)",NOW,120),
 ("POLLING_CHANGE","NH","뉴햄프셔 연방상원 신규 조사 5건 + Pollsmax 평균 적재 — 동명이인 오분류 해소 (Pappas D+5.3)",
  "NO_POLLING","Pappas D+5.3 (Pollsmax 평균)",NOW,122),
 ("POLLING_CHANGE","MI","미시간 연방상원 9월 최신 조사 2건 + Pollsmax 평균 갱신 — El-Sayed D+1.4 박빙 유지",
  "El-Sayed D+1.8 (24건)","El-Sayed D+1.4 (Pollsmax 평균, 27건)",NOW,92),
 ("POLLING_CHANGE","FL","플로리다 연방상원 신규 조사 2건 + Pollsmax 평균 적재 — 고노출 사각지대 해소 (Moody R+6.1)",
  "NO_POLLING","Moody R+6.1 (Pollsmax 평균)",NOW,126),
 ("ELECTRICITY_RATE_CHANGE","PA","Stacy Garrity 천연가스 발전 인프라 근거로 POWER 축(+35) 보강 — 종합 지지도(-36.8) 신규 산출",
  "축 2개 (미확정)","축 3개 (support: -36.8, effective: -14.7)",NOW,8),
 ("WATER_REGULATION","OH","Amy Acton 수자원 영향평가/보호요건 근거로 WATER 축(-50) 보강 — 종합 지지도(-63.5) 신규 산출",
  "축 2개 (미확정)","축 3개 (support: -63.5, effective: -21.4)",NOW,10),
 ("TAX_INCENTIVE_CHANGE","OH","Sherrod Brown 데이터센터 세제 감면 비판 근거로 TAX 축(-65) 보강 — 종합 지지도(-57.3) 신규 산출",
  "축 2개 (미확정)","축 3개 (support: -57.3, effective: -6.3)",NOW,7),
]

for et, st, note, ov, nv, when, sid in CHANGES:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,target_pk,
        field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'election_race',?,'poll/position',?,?,?,?,?)""",
        (cid, et, st, st, ov, nv, when, sid, note))

con.commit()

print(f"✔ 2026-09-19 갱신 완료:")
print(f"  - 신규 조사 적재: {len(NEW_POLLS)}건")
print(f"  - 정책 축 보강: 3명 (Garrity POWER, Acton WATER, Brown TAX)")
print(f"  - 변경 이력 기록: {len(CHANGES)}건")

con.close()
