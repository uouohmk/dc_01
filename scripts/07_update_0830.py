#!/usr/bin/env python3
"""2026-08-30 갱신
  1) [중대 수정] 메인 상원 민주당 후보: Platner 사퇴(7/8) → Troy Jackson 지명(7/25)
  2) [중대 누락] 뉴욕 행정명령 62호 — 전국 최초 주 단위 데이터센터 모라토리엄
  3) 신규 후보 입장 4건 (Hochul, Kotek, El-Sayed, Ramaswamy 상향)
  4) Sabato 등급 변동 (FL, MT)
  5) PJM 용량시장 가격 — 전기요금 쟁점의 실제 기전
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-08-30"

# ---------------------------------------------------------------- 출처
for row in [
 (40,2,"New York State Governor's Office","Executive Order No. 62 — Temporary Moratorium on Data Centers",
  "https://www.governor.ny.gov/executive-order/no-62-establishing-temporary-moratorium-data-centers-new-york-while-state-develops",
  "2026-07-14",NOW,1),
 (41,1,"Maine Democratic Party","Maine Senate Replacement Nomination Process",
  "https://mainedems.org/senate-race/","2026-07-25",NOW,1),
 (42,9,"NPR","Democrats in Maine formally nominate Troy Jackson",
  "https://www.npr.org/2026/07/25/nx-s1-5902982/democrats-maine-senate-race","2026-07-25",NOW,0),
 (43,9,"NBC News","Graham Platner officially withdraws from the Maine Senate race",
  "https://www.nbcnews.com/politics/2026-election/graham-platner-officially-drops-maine-senate-race-rcna385842",
  "2026-07-10",NOW,0),
 (44,8,"Sabato's Crystal Ball","2026 Rating Changes",
  "https://centerforpolitics.org/crystalball/2026-rating-changes/","2026-08-26",NOW,1),
 (45,9,"NPR","Data centers are a political issue crossing party lines",
  "https://www.npr.org/2026/08/08/g-s1-137853/data-centers-primaries-midterms","2026-08-08",NOW,0),
 (46,8,"datacenterbans.com","US Data Center Policy Landscape — end of August 2026",
  "https://www.datacenterbans.com/","2026-08-28",NOW,0),
 (47,9,"Brookings","How rising electric rates could affect the 2026 midterms",
  "https://www.brookings.edu/articles/how-rising-electric-rates-could-affect-the-2026-midterms",
  "2026-03-20",NOW,0),
 (48,5,"NY State Legislature","Responsible Data Center Development Act (S.10642/A.11560)",
  "https://hselaw.com/news-and-information/legalcurrents/data-center-development-in-new-york-faces-immediate-pause-under-executive-order-62/",
  "2026-06-30",NOW,0),
]:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", row)

# ================================================================ 1. 메인 후보 교체
me_race = cur.execute("""SELECT race_id FROM election_race
    WHERE state_code='ME' AND office='U.S. Senate'""").fetchone()[0]
cur.execute("""UPDATE candidate SET current_status='Withdrawn', last_updated=?
    WHERE race_id=? AND candidate_name='Graham Platner'""", (NOW, me_race))

npid = cur.execute("SELECT MAX(politician_id)+1 FROM politician").fetchone()[0]
cur.execute("""INSERT INTO politician(politician_id,full_name,party,state_code,
    current_office,last_updated) VALUES (?,?,?,?,?,?)""",
    (npid, "Troy Jackson", "D", "ME", "U.S. Senate", NOW))
ncid = cur.execute("SELECT MAX(candidate_id)+1 FROM candidate").fetchone()[0]
cur.execute("""INSERT INTO candidate(candidate_id,race_id,politician_id,candidate_name,
    candidate_party,is_incumbent,current_position,current_status,status_code,source_id,
    last_updated) VALUES (?,?,?,?,?,0,?,'Nominee','OK',?,?)""",
    (ncid, me_race, npid, "Troy Jackson", "D",
     "Former President of the Maine Senate", 42, NOW))

# ================================================================ 2. 신규 입장
POSITIONS = [
 dict(name="Kathy Hochul", st="NY", office="Governor", party="D",
   cls="Restrictive", power=None, conf="High",
   summary="전국 최초로 주 단위 데이터센터 모라토리엄을 행정명령으로 발효. 다만 의회 통과 법안(20MW)보다 문턱을 50MW로 높여 적용 범위는 좁혔다.",
   ev=[("Executive order","행정명령 62호 서명. 50MW 이상 데이터센터에 대한 DEC 재량 환경허가를 GEIS 완료 시까지 보류. 전국 최초 주 단위 모라토리엄",
        "SIGNED_EO","NEW_TOTAL","RESTRICTIVE","2026-07-14",40),
       ("Executive order","DPS에 대규모 부하 접속 관련 심리(Case 26-E-0045)에서 배전계통 영향을 검토하도록 지시",
        "SIGNED_EO","NEW_CONDITIONAL","RESTRICTIVE","2026-07-14",40),
       ("Public statement","2027 회기에서 하이퍼스케일 시설의 세제혜택과 인프라 비용 배분을 다루는 입법을 추진하겠다고 발표",
        "PUBLIC_STATEMENT","INCENTIVE_REPEAL","RESTRICTIVE","2026-07-14",40),
       ("Executive order","제조·연구·교육·의료 목적 시설은 적용 제외. 7월 14일 이전 완료 처리된 신청과 지방 단위 인허가에는 미적용",
        "SIGNED_EO","COST_ALLOCATION","SUPPORTIVE","2026-07-14",40)],
   axes=dict(GROWTH=-75, POWER=-40, RATES=-60, WATER=-45, TAX=-35),
   cats=[1,2,3,7,8,9,11,12]),

 dict(name="Tina Kotek", st="OR", office="Governor", party="D",
   cls="Concerned", power=None, conf="Medium",
   summary="자문위 권고를 담은 자체 데이터센터 법안을 2027 회기에 제출하겠다고 발표. 민주당 의원들의 3년 모라토리엄안과는 별개 노선.",
   ev=[("Public statement","2027 회기에 자문위원회 권고를 반영한 자체 데이터센터 법안을 제출하겠다고 발표",
        "PUBLIC_STATEMENT","NEW_CONDITIONAL","RESTRICTIVE","2026-08-24",46)],
   axes=dict(GROWTH=-35, POWER=None, RATES=None, WATER=None, TAX=None),
   cats=[1,3]),

 dict(name="Abdul El-Sayed", st="MI", office="U.S. Senate", party="D",
   cls="Restrictive", power=None, conf="Medium",
   summary="연방 차원 안전장치가 마련되기 전까지 신규 승인 전면 중단을 요구. OpenAI·Oracle 부지 앞에서 집회를 열었다.",
   ev=[("Campaign promise","연방 차원의 가드레일이 마련되기 전까지 신규 데이터센터를 더 승인할 수 없다고 주장",
        "CAMPAIGN_PROMISE","NEW_TOTAL","RESTRICTIVE","2026-08-08",45),
       ("Public statement","미시간 Saline Township의 OpenAI·Oracle 데이터센터 부지 앞에서 반대 집회 개최",
        "PUBLIC_STATEMENT","NEW_TOTAL","RESTRICTIVE","2026-08-08",45)],
   axes=dict(GROWTH=-85, POWER=None, RATES=None, WATER=None, TAX=None),
   cats=[1,2,12]),
]

pos_id = cur.execute("SELECT MAX(position_id) FROM politician_dc_position").fetchone()[0]
ev_id = cur.execute("SELECT MAX(evidence_id) FROM position_evidence").fetchone()[0]

for p in POSITIONS:
    row = cur.execute("SELECT politician_id FROM politician WHERE full_name=? AND state_code=?",
                      (p["name"], p["st"])).fetchone()
    if row:
        pid = row[0]
    else:
        pid = cur.execute("SELECT MAX(politician_id)+1 FROM politician").fetchone()[0]
        cur.execute("""INSERT INTO politician(politician_id,full_name,party,state_code,
            current_office,last_updated) VALUES (?,?,?,?,?,?)""",
            (pid, p["name"], p["party"], p["st"], p["office"], NOW))
    race = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                       (p["st"], p["office"])).fetchone()
    pos_id += 1
    cur.execute("""INSERT INTO politician_dc_position(position_id,politician_id,race_id,
        candidate_status,dc_position,power_source_pref,policy_statement,confidence_level,
        data_type,status_code,last_updated) VALUES (?,?,?,?,?,?,?,?,'Fact','OK',?)""",
        (pos_id, pid, race[0] if race else None, "Incumbent Running",
         p["cls"], p["power"], p["summary"], p["conf"], NOW))
    first_ev = None
    for et, summ, bind, scope, dirn, dt, src in p["ev"]:
        ev_id += 1
        cur.execute("""INSERT INTO position_evidence(evidence_id,position_id,evidence_type,
            summary,evidence_date,source_id,binding_code,scope_code,direction)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (ev_id, pos_id, et, summ, dt, src, bind, scope, dirn))
        if first_ev is None: first_ev = ev_id
    for axis, score in p["axes"].items():
        cur.execute("""INSERT INTO position_axis_score(position_id,axis_code,axis_score,
            evidence_id,status_code) VALUES (?,?,?,?,?)""",
            (pos_id, axis, score, first_ev if score is not None else None,
             'OK' if score is not None else 'NO_CLEAR_PUBLIC_POSITION'))
    for c in p["cats"]:
        cur.execute("INSERT INTO position_policy_category VALUES (?,?)", (pos_id, c))

# ---- Ramaswamy 상향: 모라토리엄 언급 근거 추가 (기존 근거는 비용 배분에 그쳤음)
r_pos = cur.execute("""SELECT p.position_id FROM politician_dc_position p
    JOIN politician pl ON pl.politician_id=p.politician_id
    WHERE pl.full_name='Vivek Ramaswamy'""").fetchone()[0]
ev_id += 1
cur.execute("""INSERT INTO position_evidence(evidence_id,position_id,evidence_type,summary,
    evidence_date,source_id,binding_code,scope_code,direction) VALUES (?,?,?,?,?,?,?,?,?)""",
    (ev_id, r_pos, "Public statement",
     "자체 모라토리엄과 '오하이오 우선 데이터센터 서약'을 제시. 재산세 다음으로 많이 듣는 민원이 데이터센터 확장 속도라고 언급",
     "2026-08-08", 45, "PUBLIC_STATEMENT", "NEW_TOTAL", "RESTRICTIVE"))
cur.execute("""UPDATE position_axis_score SET axis_score=-55 WHERE position_id=? AND axis_code='GROWTH'""",
            (r_pos,))
cur.execute("""UPDATE politician_dc_position SET dc_position='Restrictive', confidence_level='Medium',
    policy_statement=?, last_updated=? WHERE position_id=?""",
    ("자체 모라토리엄과 '오하이오 우선 서약'을 제시하면서, 데이터센터 기업이 인근 주민 전기요금을 부담해야 한다고 주장.",
     NOW, r_pos))

# ================================================================ 3. 등급 변동
nid = cur.execute("SELECT COALESCE(MAX(rating_id),0) FROM race_rating").fetchone()[0]
for st, off, rater, code, asof, src in [
    ("FL","U.S. Senate","Sabato Crystal Ball","SAFE_R","2026-08-19",44),
    ("MT","U.S. Senate","Sabato Crystal Ball","SAFE_R","2026-08-12",44),
]:
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    if not r: continue
    nid += 1
    try:
        cur.execute("""INSERT INTO race_rating(rating_id,race_id,rater,rating_code,as_of_date,
            source_id) VALUES (?,?,?,?,?,?)""", (nid, r[0], rater, code, asof, src))
    except sqlite3.IntegrityError:
        nid -= 1

# ================================================================ 4. PJM 용량시장 가격
# 전기요금이 왜 쟁점이 됐는지의 실제 기전. 13개 주 + DC, 약 6,700만 명.
cur.executescript("""
CREATE TABLE IF NOT EXISTS grid_capacity_price (
    grid_operator TEXT NOT NULL,
    delivery_year TEXT NOT NULL,
    price_mw_day  REAL NOT NULL,
    at_cap        INTEGER DEFAULT 0,
    note          TEXT,
    source_id     INTEGER NOT NULL REFERENCES source(source_id),
    PRIMARY KEY (grid_operator, delivery_year)
);
""")
cur.executemany("""INSERT OR REPLACE INTO grid_capacity_price VALUES (?,?,?,?,?,?)""", [
 ("PJM","2024/25", 28.92,0,"기준 연도",47),
 ("PJM","2025/26",269.92,0,"9.3배 급등",47),
 ("PJM","2026/27",329.17,1,"FERC 가격상한 도달",47),
 ("PJM","2027/28",333.44,1,"상향된 상한에서 마감. 신뢰도 요건 대비 약 6,625MW 부족",47),
])

PJM_STATES = ["PA","OH","VA","NJ","MD","DE","WV","NC","IN","IL","MI","KY","TN"]
for st in PJM_STATES:
    cur.execute("""INSERT OR IGNORE INTO state_dc_context(state_code,grid_operator,
        status_code,source_id,last_updated) VALUES (?,?,'OK',?,?)""", (st,"PJM",47,NOW))
    cur.execute("""UPDATE state_dc_context SET grid_operator='PJM', grid_stress_level='High',
        source_id=?, last_updated=? WHERE state_code=?""", (47, NOW, st))
cur.execute("""INSERT OR IGNORE INTO state_dc_context(state_code,grid_operator,grid_stress_level,
    status_code,source_id,last_updated) VALUES ('TX','ERCOT','Severe','OK',21,?)""", (NOW,))
cur.execute("""INSERT OR IGNORE INTO state_dc_context(state_code,grid_operator,grid_stress_level,
    status_code,source_id,last_updated) VALUES ('NY','NYISO','High','OK',40,?)""", (NOW,))

# ================================================================ 5. 전국 여론 (Pew)
oid = cur.execute("SELECT MAX(opinion_id) FROM dc_public_opinion").fetchone()[0]
for sg, pos, neg in [("ALL",6,38),("DEMOCRAT",None,44),("REPUBLICAN",None,33)]:
    oid += 1
    cur.execute("""INSERT OR REPLACE INTO dc_public_opinion(opinion_id,state_code,pollster,
        field_end,metric,subgroup,support_pct,oppose_pct,net_pct,source_id)
        VALUES (?,NULL,'Pew Research Center','2026-03-01','IMPACT_ENERGY_BILLS',?,?,?,?,?)""",
        (oid, sg, pos, neg, (pos-neg) if pos is not None else None, 47))

# ================================================================ 6. change_log
cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
for et, st, note, ov, nv, when, src in [
 ("CANDIDATE_WITHDRAWAL","ME","Graham Platner 사퇴 — 예비선거 승리(6/9) 후 7/8 중도 하차",
  "Graham Platner (Nominee)","Withdrawn","2026-07-10",43),
 ("NEW_CANDIDATE","ME","민주당 지명대회에서 Troy Jackson 선출 (571명 중 566표). Collins와 대결",
  None,"Troy Jackson (Nominee)","2026-07-25",42),
 ("NEW_LEGISLATION","NY","행정명령 62호 발효 — 50MW 이상 데이터센터 DEC 환경허가 보류. 전국 최초 주 단위 모라토리엄",
  None,"Executive Order 62","2026-07-14",40),
 ("NEW_LEGISLATION","NY","의회 통과 Responsible Data Center Development Act(20MW 기준)는 미서명 상태",
  None,"S.10642/A.11560 pending","2026-06-30",48),
 ("NEW_LEGISLATION","OR","Kotek 주지사, 2027 회기 자체 데이터센터 법안 제출 발표. 별도로 민주당 의원들의 3년 모라토리엄안 존재",
  None,"Kotek bill announced","2026-08-24",46),
 ("COMMUNITY_OPPOSITION","MI","상원 후보 El-Sayed, 연방 가드레일 전까지 신규 승인 전면 중단 요구",
  None,"El-Sayed moratorium","2026-08-08",45),
 ("COMMUNITY_OPPOSITION","OH","Ramaswamy, 자체 모라토리엄 및 '오하이오 우선 서약' 제시 — 입장 상향",
  "비용 배분 요구","모라토리엄 언급","2026-08-08",45),
 ("RACE_RATING_CHANGE","FL","Sabato: 상원 보궐 Likely R → Safe R","Likely Republican","Safe Republican","2026-08-19",44),
 ("RACE_RATING_CHANGE","MT","Sabato: 상원 Likely R → Safe R","Likely Republican","Safe Republican","2026-08-12",44),
 ("ELECTRICITY_RATE_CHANGE",None,"PJM 용량시장: 2024/25 $28.92 → 2027/28 $333.44/MW-day. 13개 주·6,700만 명 영향",
  "$28.92/MW-day (2024/25)","$333.44/MW-day (2027/28)","2026-08-30",47),
]:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,
        target_pk,field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'election_race',?,?,?,?,?,?,?)""",
        (cid, et, st, st or "US", "candidate/rating/policy", ov, nv, when, src, note))

con.commit()

print("=== 레버리지 순위 (2026-08-30) ===")
print(f"  {'주':<3}{'이름':<19}{'당':<3}{'레버리지':>9}{'방향':>8}  근거")
for r in cur.execute("""SELECT state_code,full_name,party,leverage_score,support_score,
    top_binding_label,top_scope_label,office FROM v_effective_position
    ORDER BY leverage_score DESC"""):
    dd = f"{r[4]:>8}" if r[4] is not None else f"{'미확정':>7}"
    print(f"  {r[0]:<3}{r[1]:<19}{r[2]:<3}{r[3]:>8}{dd}  [{r[5]} / {r[6]}]")
print("\nME 상원 후보:", cur.execute("""SELECT candidate_name,candidate_party,current_status
    FROM candidate WHERE race_id=(SELECT race_id FROM election_race WHERE state_code='ME'
    AND office='U.S. Senate')""").fetchall())
con.close()
