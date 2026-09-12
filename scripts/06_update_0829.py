#!/usr/bin/env python3
"""2026-08-29 갱신
  1) 레이스 등급 변동 (Sabato / Inside Elections / Fox News 추가)
  2) 여론조사 테이블 최초 적재 (필드 기간이 명시된 조사만)
  3) 데이터센터 여론 레이어 신설 — 이 프로젝트에서 빠져 있던 층
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-08-29"

# ---------------------------------------------------- 0. 등급 스케일 확장
# Inside Elections 의 'Tilt' 등급은 기존 7단계에 없었다.
cur.executescript("""
INSERT OR IGNORE INTO race_rating_scale VALUES
 ('TILT_D','Tilt Democratic','D',85),
 ('TILT_R','Tilt Republican','R',85);
""")

# rater CHECK 제약에 Fox News 등이 없어 테이블을 재생성한다.
cur.executescript("""
ALTER TABLE race_rating RENAME TO race_rating_old;
CREATE TABLE race_rating (
    rating_id  INTEGER PRIMARY KEY,
    race_id    INTEGER NOT NULL REFERENCES election_race(race_id),
    rater      TEXT NOT NULL CHECK (rater IN
                ('Cook Political Report','Sabato Crystal Ball','Inside Elections',
                 'DDHQ','Almanac of American Politics','RacetotheWH','Fox News',
                 'Split Ticket','Kalshi','270toWin Consensus','Other')),
    rating_code TEXT NOT NULL REFERENCES race_rating_scale(rating_code),
    as_of_date  TEXT NOT NULL,
    source_id   INTEGER REFERENCES source(source_id),
    UNIQUE (race_id, rater, as_of_date)
);
INSERT INTO race_rating SELECT * FROM race_rating_old;
DROP TABLE race_rating_old;
""")

# ---------------------------------------------------- 1. 출처
for row in [
 (30,8,"Sabato's Crystal Ball","2026 Senate ratings",
  "https://centerforpolitics.org/crystalball/2026-senate/","2026-08-26",NOW,1),
 (31,8,"Inside Elections","2026 Senate ratings",
  "http://insideelections.com/ratings/senate","2026-08-06",NOW,1),
 (32,9,"Fox News","2026 Senate Power Rankings",
  "https://www.foxnews.com/politics/fox-news-power-rankings-democrats-turn-left-black-voters-tap-brakes",
  "2026-08-18",NOW,0),
 (33,6,"UT / Texas Politics Project","August 2026 Texas statewide poll (n=1200 RV)",
  "https://texaspolitics.utexas.edu/blog/new-ut-texas-politics-project-poll-finds-talarico-leading-paxton-abbott-leading-hinojosa-continued-resistance-to-data-centers-2",
  "2026-08-24",NOW,1),
 (34,9,"The Hill / Texas Public Opinion Research","Texas Senate & Governor poll (n=1000 LV)",
  "https://thehill.com/homenews/campaign/6055357-texas-senate-poll-talarico-leading/",
  "2026-08-28",NOW,0),
 (35,9,"270toWin","2026 Senate Election Forecast Maps",
  "https://www.270towin.com/2026-senate-election-predictions/","2026-08-28",NOW,0),
]:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", row)

# ---------------------------------------------------- 2. 등급 변동
def rid_of(state, office):
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (state, office)).fetchone()
    return r[0] if r else None

NEW_RATINGS = [
 # (주, 직위, 평가기관, 등급, 기준일, source_id)
 ("TX","U.S. Senate","Sabato Crystal Ball","TOSSUP","2026-08-26",30),
 ("IA","U.S. Senate","Inside Elections","TILT_R","2026-08-06",31),
 ("GA","U.S. Senate","Inside Elections","TILT_D","2026-08-06",31),
 ("NC","U.S. Senate","Inside Elections","TILT_D","2026-08-06",31),
 ("TX","U.S. Senate","Inside Elections","LEAN_R","2026-08-06",31),
 ("KS","U.S. Senate","Fox News","LIKELY_R","2026-08-18",32),
 ("MI","U.S. Senate","Fox News","TOSSUP","2026-08-18",32),
 ("TX","U.S. Senate","Fox News","TOSSUP","2026-08-18",32),
 ("IA","U.S. Senate","270toWin Consensus","TOSSUP","2026-08-20",35),
 ("TX","U.S. Senate","270toWin Consensus","TOSSUP","2026-08-20",35),
]
nid = cur.execute("SELECT COALESCE(MAX(rating_id),0) FROM race_rating").fetchone()[0]
added = 0
for st, off, rater, code, asof, src in NEW_RATINGS:
    r = rid_of(st, off)
    if not r: continue
    nid += 1
    try:
        cur.execute("""INSERT INTO race_rating(rating_id,race_id,rater,rating_code,
            as_of_date,source_id) VALUES (?,?,?,?,?,?)""", (nid, r, rater, code, asof, src))
        added += 1
    except sqlite3.IntegrityError:
        nid -= 1

# ---------------------------------------------------- 3. 여론조사
# 필드 기간이 명시된 조사만 적재한다.
# Emerson/Nexstar (Paxton 47 / Talarico 46) 는 필드 기간을 확인하지 못해 제외.
POLLS = [
 # (주, 직위, 조사기관, 시작, 종료, n, 모집단, D-R 마진, source_id)
 ("TX","U.S. Senate","UT / Texas Politics Project","2026-08-05","2026-08-13",1200,"RV", 3.0,33),
 ("TX","Governor",   "UT / Texas Politics Project","2026-08-05","2026-08-13",1200,"RV",-5.0,33),
 ("TX","U.S. Senate","Texas Public Opinion Research","2026-08-21","2026-08-26",1000,"LV", 7.0,34),
 ("TX","Governor",   "Texas Public Opinion Research","2026-08-21","2026-08-26",1000,"LV",-7.0,34),
]
pid = cur.execute("SELECT COALESCE(MAX(poll_id),0) FROM polling").fetchone()[0]
for st, off, house, s0, s1, n, pop, marg, src in POLLS:
    r = rid_of(st, off)
    if not r: continue
    pid += 1
    cur.execute("""INSERT INTO polling(poll_id,race_id,pollster,field_start,field_end,
        sample_size,population,margin_d_minus_r,is_average,polling_source,source_id)
        VALUES (?,?,?,?,?,?,?,?,0,?,?)""", (pid, r, house, s0, s1, n, pop, marg, house, src))

# ---------------------------------------------------- 4. 데이터센터 여론 레이어 (신설)
cur.executescript("""
CREATE TABLE IF NOT EXISTS dc_public_opinion (
    opinion_id   INTEGER PRIMARY KEY,
    state_code   TEXT REFERENCES state_political_structure(state_code),  -- NULL = 전국
    pollster     TEXT NOT NULL,
    field_start  TEXT,
    field_end    TEXT NOT NULL,
    sample_size  INTEGER,
    population   TEXT,
    metric       TEXT NOT NULL CHECK (metric IN
                  ('LOCAL_CONSTRUCTION','STATE_LEADERSHIP_APPROVAL','IMPACT_ENERGY_BILLS',
                   'IMPACT_WATER','IMPACT_GRID','IMPACT_LOCAL_ECONOMY','IMPACT_ENVIRONMENT')),
    subgroup     TEXT NOT NULL DEFAULT 'ALL',
    support_pct  REAL,
    oppose_pct   REAL,
    net_pct      REAL,
    source_id    INTEGER NOT NULL REFERENCES source(source_id),
    UNIQUE (state_code, pollster, field_end, metric, subgroup)
);
""")

# UT/TxPP 2026-08 텍사스. "지역에 데이터센터 건설 지지/반대"
TX_OPINION = [
 ("ALL",              30, 57), ("REPUBLICAN", 45, 43), ("DEMOCRAT", 15, 75),
 ("INDEPENDENT",      19, 54), ("RURAL",      25, 60), ("SUBURBAN", 26, 60),
]
oid = 0
for sg, sup, opp in TX_OPINION:
    oid += 1
    cur.execute("""INSERT OR REPLACE INTO dc_public_opinion(opinion_id,state_code,pollster,
        field_start,field_end,sample_size,population,metric,subgroup,support_pct,oppose_pct,
        net_pct,source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (oid,"TX","UT / Texas Politics Project","2026-08-05","2026-08-13",1200,"RV",
         "LOCAL_CONSTRUCTION",sg,sup,opp,sup-opp,33))

# 6월 대비 추세 (전체)
oid += 1
cur.execute("""INSERT OR REPLACE INTO dc_public_opinion VALUES
    (?,'TX','UT / Texas Politics Project','2026-06-01','2026-06-15',NULL,'RV',
     'LOCAL_CONSTRUCTION','ALL',29,56,-27,33)""", (oid,))

# 주 지도부의 데이터센터 대응 평가
oid += 1
cur.execute("""INSERT OR REPLACE INTO dc_public_opinion VALUES
    (?,'TX','UT / Texas Politics Project','2026-08-05','2026-08-13',1200,'RV',
     'STATE_LEADERSHIP_APPROVAL','ALL',24,45,-21,33)""", (oid,))

# 영향 인식 (부정 응답이 우세한 항목)
for metric, pos, neg in [("IMPACT_ENERGY_BILLS",20,56),("IMPACT_WATER",18,57),
                         ("IMPACT_GRID",23,56),("IMPACT_ENVIRONMENT",17,61),
                         ("IMPACT_LOCAL_ECONOMY",33,39)]:
    oid += 1
    cur.execute("""INSERT OR REPLACE INTO dc_public_opinion(opinion_id,state_code,pollster,
        field_start,field_end,sample_size,population,metric,subgroup,support_pct,oppose_pct,
        net_pct,source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (oid,"TX","UT / Texas Politics Project","2026-08-05","2026-08-13",1200,"RV",
         metric,"ALL",pos,neg,pos-neg,33))

# ---------------------------------------------------- 5. change_log
cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
EVENTS = [
 ("RACE_RATING_CHANGE","TX","Sabato: 상원 Lean R → Toss-up","Lean Republican","Toss Up","2026-08-26",30),
 ("RACE_RATING_CHANGE","TX","Fox News: 상원 Lean R → Toss-up","Lean Republican","Toss Up","2026-08-18",32),
 ("RACE_RATING_CHANGE","MI","Fox News: 상원 Lean D → Toss-up","Lean Democratic","Toss Up","2026-08-18",32),
 ("RACE_RATING_CHANGE","KS","Fox News: 상원 Safe R → Likely R","Safe Republican","Likely Republican","2026-08-18",32),
 ("RACE_RATING_CHANGE","GA","Inside Elections: 상원 Toss-up → Tilt D","Toss Up","Tilt Democratic","2026-08-06",31),
 ("RACE_RATING_CHANGE","NC","Inside Elections: 상원 Toss-up → Tilt D","Toss Up","Tilt Democratic","2026-08-06",31),
 ("RACE_RATING_CHANGE","IA","Inside Elections: 상원 Lean R → Tilt R","Lean Republican","Tilt Republican","2026-08-06",31),
 ("POLLING_CHANGE","TX","TxPOR 상원: Talarico +7 (8/21-26)",None,"D+7","2026-08-28",34),
 ("POLLING_CHANGE","TX","UT/TxPP 상원: Talarico +3 (8/5-13)",None,"D+3","2026-08-24",33),
 ("POLLING_CHANGE","TX","UT/TxPP 주지사 교외층: 6월 Abbott +5 → 8월 Hinojosa +4",
  "Abbott +5 (suburban)","Hinojosa +4 (suburban)","2026-08-24",33),
 ("COMMUNITY_OPPOSITION","TX","지역 데이터센터 건설 반대 57% / 찬성 30% (6월과 통계적으로 동일)",
  "29/56 (June)","30/57 (August)","2026-08-24",33),
 ("COMMUNITY_OPPOSITION","TX","공화당 지지층 내부 분열: 찬성 45 / 반대 43",None,"45/43","2026-08-24",33),
]
for et, st, note, ov, nv, when, src in EVENTS:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,
        target_pk,field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'election_race',?,?,?,?,?,?,?)""",
        (cid, et, st, st, "rating/poll", ov, nv, when, src, note))

con.commit()

print("등급 추가:", added, "| 여론조사:", pid, "| DC 여론 행:", oid, "| 변동로그:", cid)
print("\n=== TX 상원 등급 스냅샷 ===")
for r in cur.execute("""SELECT rr.rater, s.rating_label, rr.as_of_date FROM race_rating rr
    JOIN race_rating_scale s ON s.rating_code=rr.rating_code
    WHERE rr.race_id=(SELECT race_id FROM election_race WHERE state_code='TX'
    AND office='U.S. Senate') ORDER BY rr.as_of_date DESC"""):
    print(f"  {r[0]:<28}{r[1]:<20}{r[2]}")
print("\n=== 데이터센터 여론 (TX, 지역 건설) ===")
for r in cur.execute("""SELECT subgroup,support_pct,oppose_pct,net_pct FROM dc_public_opinion
    WHERE metric='LOCAL_CONSTRUCTION' AND field_end='2026-08-13' ORDER BY net_pct"""):
    print(f"  {r[0]:<14}찬성 {r[1]:>4.0f}  반대 {r[2]:>4.0f}  순 {r[3]:>+5.0f}")
con.close()
