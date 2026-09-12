#!/usr/bin/env python3
"""2026-08-31 갱신
  1) [수정] Kotek — 발표 단계가 아니라 이미 서명된 법률이었다. 구속력 0.25 → 1.00
  2) [신규] Drazan (OR 공화 주지사 후보) — 규제와 우호가 축별로 갈리는 사례
  3) [수정] Rogers — 축 3개 확보. 주 단위 모라토리엄이며 연방상원 권한 밖임이 캠프에서 확인됨
  4) [수정] Husted — 개발사 비용부담 법안 발의 확인. 순수 우호 → 혼합
  5) 지역 단위 표결 결과 및 NY 입법 압박
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-08-31"

for row in [
 (50,9,"KLCC / Oregon Capital Chronicle","Data centers emerge as new flashpoint between Kotek, Drazan",
  "https://www.klcc.org/politics-government/2026-08-31/data-centers-emerge-as-new-flashpoint-between-kotek-drazan-in-oregon-governors-race",
  "2026-08-31",NOW,0),
 (51,9,"Detroit News","Republican U.S. Senate candidate backs one-year data center moratorium",
  "https://www.detroitnews.com/story/news/politics/2026/08/20/data-center-politics-michigan-senate-mike-rogers-abdul-el-sayed/91385736007/",
  "2026-08-20",NOW,0),
 (52,9,"Axios","Data center uproar scrambles the midterm election",
  "https://www.axios.com/2026/08/20/data-center-uproar-2026-midterms","2026-08-20",NOW,0),
 (53,9,"The Hill","Mike Rogers doubles down on push for data center moratorium",
  "https://thehill.com/homenews/campaign/6043170-mike-rogers-data-center-pressure-michigan-senate-race/",
  "2026-08-21",NOW,0),
]:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", row)

ev_id = cur.execute("SELECT MAX(evidence_id) FROM position_evidence").fetchone()[0]
pos_id = cur.execute("SELECT MAX(position_id) FROM politician_dc_position").fetchone()[0]

def pos_of(name):
    return cur.execute("""SELECT p.position_id FROM politician_dc_position p
        JOIN politician pl ON pl.politician_id=p.politician_id
        WHERE pl.full_name=?""", (name,)).fetchone()[0]

def add_ev(position_id, et, summ, bind, scope, dirn, dt, src):
    global ev_id
    ev_id += 1
    cur.execute("""INSERT INTO position_evidence(evidence_id,position_id,evidence_type,summary,
        evidence_date,source_id,binding_code,scope_code,direction) VALUES (?,?,?,?,?,?,?,?,?)""",
        (ev_id, position_id, et, summ, dt, src, bind, scope, dirn))
    return ev_id

def set_axis(position_id, axis, score, evid):
    cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
        evidence_id,status_code) VALUES (?,?,?,?,?)""",
        (position_id, axis, score, evid if score is not None else None,
         'OK' if score is not None else 'NO_CLEAR_PUBLIC_POSITION'))

# ============================================== 1. Kotek 상향 (발표 → 서명된 법률)
k = pos_of("Tina Kotek")
e = add_ev(k,"Signed bill",
   "기업지구(enterprise zone) 세제혜택 확대안을 철회하고, 데이터센터의 해당 프로그램 이용을 "
   "2027년 여름까지 1년간 중단시키는 수정 법안을 지지해 성립시킴",
   "SIGNED_LAW","INCENTIVE_REPEAL","RESTRICTIVE","2026-06-30",50)
add_ev(k,"Public statement",
   "2027 회기에 자문위 권고를 반영한 자체 데이터센터 법안 제출 예정. 민주당 의원 4인의 "
   "3년 모라토리엄안과 별개 노선",
   "PUBLIC_STATEMENT","NEW_CONDITIONAL","RESTRICTIVE","2026-08-24",50)
set_axis(k,"GROWTH",-45,e); set_axis(k,"TAX",-60,e); set_axis(k,"RATES",-30,e)
cur.execute("""UPDATE politician_dc_position SET dc_position='Restrictive',confidence_level='High',
    policy_statement=?, last_updated=? WHERE position_id=?""",
    ("세제혜택 확대안을 철회하고 기업지구 프로그램의 데이터센터 이용을 2027년 여름까지 "
     "중단시키는 법안을 성립시킴. 별도로 2027 회기 자체 법안을 예고.", NOW, k))

# ============================================== 2. Drazan 신규 (축별로 갈리는 사례)
pos_id += 1
pl = cur.execute("SELECT politician_id FROM politician WHERE full_name='Christine Drazan'").fetchone()
if pl:
    dz_pid = pl[0]
else:
    dz_pid = cur.execute("SELECT MAX(politician_id)+1 FROM politician").fetchone()[0]
    cur.execute("""INSERT INTO politician(politician_id,full_name,party,state_code,current_office,
        last_updated) VALUES (?,'Christine Drazan','R','OR','Governor',?)""", (dz_pid, NOW))
or_race = cur.execute("""SELECT race_id FROM election_race WHERE state_code='OR'
    AND office='Governor'""").fetchone()[0]
cur.execute("""INSERT INTO politician_dc_position(position_id,politician_id,race_id,
    candidate_status,dc_position,power_source_pref,policy_statement,confidence_level,
    data_type,status_code,last_updated) VALUES (?,?,?,'Challenger','Mixed',NULL,?,?,'Fact','OK',?)""",
    (pos_id, dz_pid, or_race,
     "지역사회의 유치 거부권은 지지하나 '자의적 모라토리엄'에는 반대. 데이터센터에 요금 "
     "부담을 지우는 POWER Act에는 반대 표결했으면서, Kotek의 세제혜택은 공격하는 혼합형.",
     "High", NOW))
e1 = add_ev(pos_id,"Voted against",
   "전력회사가 데이터센터에 별도 요금제를 두어 인프라·발전 비용을 부담시키도록 한 2025년 "
   "POWER Act에 반대 표결","VOTE_RECORD","COST_ALLOCATION","SUPPORTIVE","2025-06-01",50)
e2 = add_ev(pos_id,"Public statement",
   "지역사회가 데이터센터 유치를 거부하는 것은 지지하나 자의적 모라토리엄에는 반대한다고 표명",
   "PUBLIC_STATEMENT","LOCAL_CONSENT","RESTRICTIVE","2026-08-27",50)
e3 = add_ev(pos_id,"Campaign ad",
   "Kotek이 10년 넘게 데이터센터 성장을 부추긴 세제 감면을 지지하면서 주민 세금은 계속 "
   "올렸다고 주장. 오리건이 이미 충분히 감당했다고 발언",
   "CAMPAIGN_AD","INCENTIVE_REPEAL","RESTRICTIVE","2026-08-27",50)
for ax, sc, ev in [("GROWTH",-25,e2),("RATES",55,e1),("TAX",-50,e3),
                   ("POWER",None,None),("WATER",None,None)]:
    set_axis(pos_id, ax, sc, ev)
for c in [1,3,8,9,10,12]:
    cur.execute("INSERT OR IGNORE INTO position_policy_category VALUES (?,?)", (pos_id, c))

# ============================================== 3. Rogers 축 확대
r = pos_of("Mike Rogers")
e = add_ev(r,"Campaign promise",
   "연방 차원 금지에는 반대하나 미시간에 더 강한 안전장치가 필요하다며 지역 통제권 보장, "
   "전기요금 인상 방지, 수자원 보호, 이권 거래 차단을 제시",
   "CAMPAIGN_PROMISE","NEW_TOTAL","RESTRICTIVE","2026-08-20",51)
add_ev(r,"Public statement",
   "캠프가 해당 모라토리엄은 주 단위 조치이며 연방 상원의원으로서는 공식 권한이 없다고 확인",
   "PUBLIC_STATEMENT","NEW_TOTAL","RESTRICTIVE","2026-08-21",53)
set_axis(r,"RATES",-65,e); set_axis(r,"WATER",-55,e); set_axis(r,"POWER",-20,e)
cur.execute("""UPDATE politician_dc_position SET confidence_level='High', policy_statement=?,
    last_updated=? WHERE position_id=?""",
    ("신규 건설 1년 모라토리엄을 지지하되 연방 금지에는 반대. 캠프가 주 단위 조치이며 "
     "연방상원 권한 밖임을 확인했다.", NOW, r))

# ============================================== 4. Husted 수정 (순수 우호 → 혼합)
h = pos_of("Jon Husted")
e = add_ev(h,"Introduced bill",
   "데이터센터 개발사가 전력망 비용의 자기 몫을 부담하도록 하는 법안을 발의",
   "BILL_FILED","COST_ALLOCATION","RESTRICTIVE","2026-08-01",8)
set_axis(h,"RATES",-40,e)
cur.execute("""UPDATE politician_dc_position SET dc_position='Mixed', policy_statement=?,
    last_updated=? WHERE position_id=?""",
    ("부지사 시절 세제 감면을 지원했으나, 공격이 집중되자 개발사 비용부담 법안을 발의해 "
     "요금축에서 방어로 선회. 성장·세제축은 여전히 우호적.", NOW, h))

# ============================================== 5. change_log
cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
for et, st, note, ov, nv, when, src in [
 ("NEW_LEGISLATION","OR","[수정] Kotek의 조치는 발표가 아니라 성립된 법률이었음. 기업지구 세제혜택 "
  "데이터센터 이용을 2027년 여름까지 중단","공개 발언 (0.25)","법률 서명 (1.00)","2026-08-31",50),
 ("NEW_CANDIDATE","OR","Drazan(공화) 입장 등재 — POWER Act 반대 표결(우호)과 세제혜택 공격(규제)이 공존",
  None,"Mixed","2026-08-31",50),
 ("COMMUNITY_OPPOSITION","MI","[수정] Rogers 근거 확대 — 요금·물·지역통제 축 확보. 캠프가 주 단위 "
  "조치이며 연방상원 권한 밖임을 확인","축 1개","축 4개","2026-08-21",51),
 ("NEW_LEGISLATION","OH","[수정] Husted, 개발사 전력망 비용부담 법안 발의 확인 — 순수 우호에서 혼합으로",
  "Supportive","Mixed","2026-08-01",8),
 ("NEW_LEGISLATION","NY","주의회 의원 60명이 Hochul에게 Responsible Data Center Development Act "
  "(20MW 기준) 서명을 촉구하는 서한 발송",None,"60인 서한","2026-08-24",46),
 ("NEW_LEGISLATION","FL","공익사업위원회, 신설 Hyperscale Data Center Act의 첫 시험대로 Duke Energy의 "
  "대규모 부하 제안이 요금납부자를 충분히 보호하는지 심사 착수",None,"PSC 심사 개시","2026-08-28",46),
 ("COMMUNITY_OPPOSITION","FL","탤러해시, AI 데이터센터 금지안 3-2 부결","제안","부결","2026-08-25",46),
 ("COMMUNITY_OPPOSITION","NC","데이비드슨 카운티, 6개월 중단안 부결","제안","부결","2026-08-25",46),
 ("COMMUNITY_OPPOSITION","IA","세일릭스, 개발사가 구글로 밝혀진 뒤 모라토리엄 3-2 부결","제안","부결","2026-08-25",46),
 ("COMMUNITY_OPPOSITION","AR","펄래스키 카운티, 대체 규제 조례 최종 표결이 방청객 초과로 연기",
  "표결 예정","연기","2026-08-25",46),
]:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,target_pk,
        field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'position_evidence',?,?,?,?,?,?,?)""",
        (cid, et, st, st or "US", "evidence/scope", ov, nv, when, src, note))

con.commit()

print(f"  {'주':<3}{'이름':<19}{'당':<3}{'레버리지':>9}{'방향':>8}  근거")
for r_ in cur.execute("""SELECT state_code,full_name,party,leverage_score,support_score,
    top_binding_label,top_scope_label FROM v_effective_position ORDER BY leverage_score DESC"""):
    dd = f"{r_[4]:>8}" if r_[4] is not None else f"{'미확정':>7}"
    print(f"  {r_[0]:<3}{r_[1]:<19}{r_[2]:<3}{r_[3]:>8}{dd}  [{r_[5]} / {r_[6]}]")
con.close()
