#!/usr/bin/env python3
"""
STEP 2 & 3 seed: 50-state political skeleton, 35 Senate races, 36 Governor races.

원칙:
  - 출처가 확인된 값만 입력한다. 나머지는 NULL + status_code='NOT_YET_COLLECTED'.
  - 주의회 의석 구성(state_senate_*/state_house_*)은 이번 단계에서 수집하지 않았으므로
    전부 NULL 로 남긴다. 추정치로 채우지 않는다.
  - political_control 도 주의회 데이터가 없으면 판정하지 않는다 (NULL).
"""
import sqlite3, math, os, json

DB = "data/tracker.db"
if os.path.exists(DB):
    os.remove(DB)

con = sqlite3.connect(DB)
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
con.executescript(open("data/01_schema.sql").read())
cur = con.cursor()

TODAY = "2026-08-27"

# ---------------------------------------------------------------- sources
SOURCES = [
    (1, 1, "U.S. Senate", "Class II - Terms Expiring 2027",
     "https://www.senate.gov/senators/Class_II.htm", None, TODAY, 1),
    (2, 9, "270toWin", "2026 Senate Election / Cook ratings",
     "https://www.270towin.com/2026-senate-election/cook-political-report-2026-senate",
     "2026-08-20", TODAY, 0),
    (3, 9, "270toWin", "2026 Governor Election forecasts",
     "https://www.270towin.com/2026-governor-election-predictions/", "2026-08-26", TODAY, 0),
    (4, 9, "Wikipedia", "2026 United States Senate elections",
     "https://en.wikipedia.org/wiki/2026_United_States_Senate_elections", "2026-08-26", TODAY, 0),
    (5, 9, "Wikipedia", "2026 United States gubernatorial elections",
     "https://en.wikipedia.org/wiki/2026_United_States_gubernatorial_elections", "2026-08-26", TODAY, 0),
    (6, 8, "Cook Political Report", "2026 Senate Race Ratings",
     "https://www.cookpolitical.com/ratings/senate-race-ratings", "2026-08-20", TODAY, 1),
    (7, 9, "Brookings", "Why data centers are a top issue in the 2026 midterms",
     "https://www.brookings.edu/articles/why-data-centers-are-a-top-issue-in-the-2026-midterms/",
     "2026-08-25", TODAY, 0),
    (8, 9, "The Hill", "Rising data center backlash shakes up midterm races",
     "https://thehill.com/homenews/campaign/6044618-ai-data-center-backlash-michigan-ohio-pennsylvania/",
     "2026-08-23", TODAY, 0),
    (9, 9, "CNBC", "AI data center outrage in ads and elections",
     "https://www.cnbc.com/2026/08/20/ai-data-center-election-backlash.html", "2026-08-20", TODAY, 0),
    (10, 9, "NPR", "Data centers a top issue in midterms for voters, candidates",
     "https://www.npr.org/2026/08/08/g-s1-137853/data-centers-primaries-midterms", "2026-08-08", TODAY, 0),
    (11, 8, "Aterio", "US Data Center Database",
     "https://www.aterio.io/insights/us-data-centers", "2026-08-26", TODAY, 0),
    (12, 8, "dcmap.us", "US Data Center Map",
     "https://dcmap.us/", "2026-02-20", TODAY, 0),
]
cur.executemany(
    "INSERT INTO source(source_id,tier,publisher,title,url,published_date,retrieved_at,is_primary)"
    " VALUES (?,?,?,?,?,?,?,?)", SOURCES)

# ------------------------------------------------- 50 states + governors
# (code, name, governor, party, gov_election_2026, term_limited_or_not_running)
# gov_flag: 1=2026 선거 있음. tl: 1=임기제한, 2=불출마(임기제한 아님), 0=출마
STATES = [
 ("AL","Alabama","Kay Ivey","R",1,1),      ("AK","Alaska","Mike Dunleavy","R",1,1),
 ("AZ","Arizona","Katie Hobbs","D",1,0),   ("AR","Arkansas","Sarah Huckabee Sanders","R",1,0),
 ("CA","California","Gavin Newsom","D",1,1),("CO","Colorado","Jared Polis","D",1,1),
 ("CT","Connecticut","Ned Lamont","D",1,0),("DE","Delaware","Matt Meyer","D",0,0),
 ("FL","Florida","Ron DeSantis","R",1,1),  ("GA","Georgia","Brian Kemp","R",1,1),
 ("HI","Hawaii","Josh Green","D",1,0),     ("ID","Idaho","Brad Little","R",1,0),
 ("IL","Illinois","JB Pritzker","D",1,0),  ("IN","Indiana","Mike Braun","R",0,0),
 ("IA","Iowa","Kim Reynolds","R",1,2),     ("KS","Kansas","Laura Kelly","D",1,1),
 ("KY","Kentucky","Andy Beshear","D",0,0), ("LA","Louisiana","Jeff Landry","R",0,0),
 ("ME","Maine","Janet Mills","D",1,1),     ("MD","Maryland","Wes Moore","D",1,0),
 ("MA","Massachusetts","Maura Healey","D",1,0),("MI","Michigan","Gretchen Whitmer","D",1,1),
 ("MN","Minnesota","Tim Walz","D",1,2),    ("MS","Mississippi","Tate Reeves","R",0,0),
 ("MO","Missouri","Mike Kehoe","R",0,0),   ("MT","Montana","Greg Gianforte","R",0,0),
 ("NE","Nebraska","Jim Pillen","R",1,0),   ("NV","Nevada","Joe Lombardo","R",1,0),
 ("NH","New Hampshire","Kelly Ayotte","R",1,0),("NJ","New Jersey","Mikie Sherrill","D",0,0),
 ("NM","New Mexico","Michelle Lujan Grisham","D",1,1),("NY","New York","Kathy Hochul","D",1,0),
 ("NC","North Carolina","Josh Stein","D",0,0),("ND","North Dakota","Kelly Armstrong","R",0,0),
 ("OH","Ohio","Mike DeWine","R",1,1),      ("OK","Oklahoma","Kevin Stitt","R",1,1),
 ("OR","Oregon","Tina Kotek","D",1,0),     ("PA","Pennsylvania","Josh Shapiro","D",1,0),
 ("RI","Rhode Island","Dan McKee","D",1,0),("SC","South Carolina","Henry McMaster","R",1,1),
 ("SD","South Dakota","Larry Rhoden","R",1,0),("TN","Tennessee","Bill Lee","R",1,1),
 ("TX","Texas","Greg Abbott","R",1,0),     ("UT","Utah","Spencer Cox","R",0,0),
 ("VT","Vermont","Phil Scott","R",1,0),    ("VA","Virginia","Abigail Spanberger","D",0,0),
 ("WA","Washington","Bob Ferguson","D",0,0),("WV","West Virginia","Patrick Morrisey","R",0,0),
 ("WI","Wisconsin","Tony Evers","D",1,2),  ("WY","Wyoming","Mark Gordon","R",1,1),
]

for code, name, gov, party, gflag, tl in STATES:
    cur.execute("""INSERT INTO state_political_structure
      (state_code,state_name,governor,governor_party,governor_election_2026,
       governor_term_limited,federal_senate_seats,status_code,source_id,last_updated,
       legislature_note)
      VALUES (?,?,?,?,?,?,2,'OK',?,?,?)""",
      (code, name, gov, party, gflag, 1 if tl == 1 else 0, 5, TODAY,
       "주의회 의석 구성은 STEP 2 범위에 미포함 (NOT_YET_COLLECTED)"))

# --------------------------------------------------------- Senate races
# (state, incumbent, party, running(1)/open(0), open_reason, nominee_D, nominee_R, other)
SEN = [
 ("AL","Tommy Tuberville","R",0,"Seeking Other Office","Everett Wess","Barry Moore",None),
 ("AK","Dan Sullivan","R",1,"Not Open","Mary Peltola","Dan Sullivan",None),
 ("AR","Tom Cotton","R",1,"Not Open","Hallie Shoffner","Tom Cotton",None),
 ("CO","John Hickenlooper","D",1,"Not Open","John Hickenlooper","Mark Baisley",None),
 ("DE","Chris Coons","D",1,"Not Open","Chris Coons",None,None),
 ("GA","Jon Ossoff","D",1,"Not Open","Jon Ossoff","Mike Collins",None),
 ("ID","Jim Risch","R",1,"Not Open","David Roth","Jim Risch",None),
 ("IL","Dick Durbin","D",0,"Retirement","Juliana Stratton","Don Tracy",None),
 ("IA","Joni Ernst","R",0,"Retirement","Josh Turek","Ashley Hinson",None),
 ("KS","Roger Marshall","R",1,"Not Open",None,"Roger Marshall",None),
 ("KY","Mitch McConnell","R",0,"Retirement","Charles Booker","Andy Barr",None),
 ("LA","Bill Cassidy","R",0,"Primary Defeat",None,"Julia Letlow",None),
 ("ME","Susan Collins","R",1,"Not Open","Graham Platner","Susan Collins",None),
 ("MA","Ed Markey","D",1,"Not Open","Ed Markey","John Deaton",None),
 ("MI","Gary Peters","D",0,"Retirement",None,"Mike Rogers",None),
 ("MN","Tina Smith","D",0,"Retirement",None,None,None),
 ("MS","Cindy Hyde-Smith","R",1,"Not Open","Scott Colom","Cindy Hyde-Smith","Ty Pinkins (I)"),
 ("MT","Steve Daines","R",0,"Retirement","Alani Bankhead","Kurt Alme","Seth Bodnar (I)"),
 ("NE","Pete Ricketts","R",1,"Not Open","Cindy Burbank","Pete Ricketts","Dan Osborn (I)"),
 ("NH","Jeanne Shaheen","D",0,"Retirement","Chris Pappas",None,None),
 ("NJ","Cory Booker","D",1,"Not Open","Cory Booker","Justin Murphy",None),
 ("NM","Ben Ray Lujan","D",1,"Not Open","Ben Ray Lujan","Larry Marker",None),
 ("NC","Thom Tillis","R",0,"Retirement","Roy Cooper","Michael Whatley",None),
 ("OK","Alan S. Armstrong","R",0,"Resigned",None,"Kevin Hern",None),
 ("OR","Jeff Merkley","D",1,"Not Open","Jeff Merkley","David Brock Smith",None),
 ("RI","Jack Reed","D",1,"Not Open","Jack Reed","Raymond McKay",None),
 ("SC","Lindsey Graham","R",1,"Not Open","Annie Andrews","Lindsey Graham",None),
 ("SD","Mike Rounds","R",1,"Not Open","Julian Beaudion","Mike Rounds","Brian Bengs (I)"),
 ("TN","Bill Hagerty","R",1,"Not Open",None,"Bill Hagerty",None),
 ("TX","John Cornyn","R",0,"Primary Defeat","James Talarico","Ken Paxton",None),
 ("VA","Mark Warner","D",1,"Not Open","Mark Warner",None,None),
 ("WV","Shelley Moore Capito","R",1,"Not Open","Rachel Fetty Anderson","Shelley Moore Capito",None),
 ("WY","Cynthia Lummis","R",0,"Retirement",None,"Harriet Hageman",None),
]
SEN_SPECIAL = [
 ("FL","Ashley Moody","R",1,"Not Open",None,"Ashley Moody","Alexander Vindman / Angie Nixon (D primary)"),
 ("OH","Jon Husted","R",1,"Not Open","Sherrod Brown","Jon Husted",None),
]

rid = 0
cand_id = 0
pol_id = 0
politicians = {}

def add_politician(name, party, state, office):
    global pol_id
    key = (name, state, office)
    if key in politicians:
        return politicians[key]
    pol_id += 1
    cur.execute("""INSERT INTO politician(politician_id,full_name,party,state_code,
                   current_office,last_updated) VALUES (?,?,?,?,?,?)""",
                (pol_id, name, party, state, office, TODAY))
    politicians[key] = pol_id
    return pol_id

def add_race(state, office, etype, inc, incp, running, reason, sclass=None):
    global rid
    rid += 1
    cur.execute("""INSERT INTO election_race(race_id,state_code,office,district,election_type,
        senate_class,incumbent_name,incumbent_party,incumbent_running,is_open_seat,
        open_seat_reason,primary_date,general_election_date,status_code,source_id,last_updated)
        VALUES (?,?,?,NULL,?,?,?,?,?,?,?,NULL,'2026-11-03','OK',?,?)""",
        (rid, state, office, etype, sclass, inc, incp, running,
         0 if reason == "Not Open" else 1, reason, 4 if office != "Governor" else 5, TODAY))
    return rid

def add_cand(race_id, name, party, state, office, incumbent, status="Nominee"):
    global cand_id
    if not name:
        return
    cand_id += 1
    pid = add_politician(name, party, state, office)
    cur.execute("""INSERT INTO candidate(candidate_id,race_id,politician_id,candidate_name,
        candidate_party,is_incumbent,current_status,status_code,source_id,last_updated)
        VALUES (?,?,?,?,?,?,?,'OK',?,?)""",
        (cand_id, race_id, pid, name, party, incumbent, status, 4, TODAY))

for st, inc, incp, running, reason, dnom, rnom, other in SEN + SEN_SPECIAL:
    etype = "Special" if (st, inc) in [("FL","Ashley Moody"), ("OH","Jon Husted")] else "Regular"
    r = add_race(st, "U.S. Senate", etype, inc, incp, running, reason,
                 3 if etype == "Special" else 2)
    add_cand(r, dnom, "D", st, "U.S. Senate", 1 if (dnom == inc) else 0)
    add_cand(r, rnom, "R", st, "U.S. Senate", 1 if (rnom == inc) else 0)
    if other:
        nm = other.split(" (")[0]
        add_cand(r, nm, "I", st, "U.S. Senate", 0, "Declared")

# -------------------------------------------------------- Governor races
# (state, incumbent, party, running, reason, D nominee, R nominee, other)
GOV = [
 ("AL","Kay Ivey","R",0,"Term Limited","Doug Jones","Tommy Tuberville",None),
 ("AK","Mike Dunleavy","R",0,"Term Limited","Tom Begich",None,"Bill Walker (I)"),
 ("AZ","Katie Hobbs","D",1,"Not Open","Katie Hobbs",None,None),
 ("AR","Sarah Huckabee Sanders","R",1,"Not Open","Fredrick Love","Sarah Huckabee Sanders",None),
 ("CA","Gavin Newsom","D",0,"Term Limited","Xavier Becerra","Steve Hilton",None),
 ("CO","Jared Polis","D",0,"Term Limited",None,None,"Greg Lopez (I)"),
 ("CT","Ned Lamont","D",1,"Not Open","Ned Lamont","Ryan Fazio",None),
 ("FL","Ron DeSantis","R",0,"Term Limited",None,"Byron Donalds","Jason Pizzo (I)"),
 ("GA","Brian Kemp","R",0,"Term Limited","Keisha Lance Bottoms","Rick Jackson",None),
 ("HI","Josh Green","D",1,"Not Open","Josh Green",None,None),
 ("ID","Brad Little","R",1,"Not Open","Terri Pickens","Brad Little",None),
 ("IL","JB Pritzker","D",1,"Not Open","JB Pritzker","Darren Bailey",None),
 ("IA","Kim Reynolds","R",0,"Retirement","Rob Sand","Zach Lahn",None),
 ("KS","Laura Kelly","D",0,"Term Limited",None,None,None),
 ("ME","Janet Mills","D",0,"Term Limited","Hannah Pingree","Robert B. Charles","Rick Bennett (I)"),
 ("MD","Wes Moore","D",1,"Not Open","Wes Moore","Dan Cox",None),
 ("MA","Maura Healey","D",1,"Not Open","Maura Healey",None,None),
 ("MI","Gretchen Whitmer","D",0,"Term Limited",None,None,"Mike Duggan (I)"),
 ("MN","Tim Walz","D",0,"Retirement","Amy Klobuchar","Kendall Qualls",None),
 ("NE","Jim Pillen","R",1,"Not Open","Lynne Walz","Jim Pillen",None),
 ("NV","Joe Lombardo","R",1,"Not Open","Aaron D. Ford","Joe Lombardo",None),
 ("NH","Kelly Ayotte","R",1,"Not Open","Cinde Warmington","Kelly Ayotte",None),
 ("NM","Michelle Lujan Grisham","D",0,"Term Limited","Deb Haaland","Gregg Hull",None),
 ("NY","Kathy Hochul","D",1,"Not Open","Kathy Hochul","Bruce Blakeman",None),
 ("OH","Mike DeWine","R",0,"Term Limited","Amy Acton","Vivek Ramaswamy",None),
 ("OK","Kevin Stitt","R",0,"Term Limited","Cyndi Munson","Gentner Drummond",None),
 ("OR","Tina Kotek","D",1,"Not Open","Tina Kotek","Christine Drazan",None),
 ("PA","Josh Shapiro","D",1,"Not Open","Josh Shapiro","Stacy Garrity",None),
 ("RI","Dan McKee","D",1,"Not Open",None,None,None),
 ("SC","Henry McMaster","R",0,"Term Limited","Jermaine Johnson","Alan Wilson",None),
 ("SD","Larry Rhoden","R",1,"Not Open","Dan Ahlers",None,None),
 ("TN","Bill Lee","R",0,"Term Limited",None,None,None),
 ("TX","Greg Abbott","R",1,"Not Open","Gina Hinojosa","Greg Abbott",None),
 ("VT","Phil Scott","R",1,"Not Open",None,"Phil Scott",None),
 ("WI","Tony Evers","D",0,"Retirement",None,"Tom Tiffany",None),
 ("WY","Mark Gordon","R",0,"Term Limited","Gabriel Green",None,None),
]

for st, inc, incp, running, reason, dnom, rnom, other in GOV:
    r = add_race(st, "Governor", "Regular", inc, incp, running, reason)
    tl = 1 if reason == "Term Limited" else 0
    cur.execute("""INSERT INTO governor_race_detail(race_id,current_governor,current_party,
        term_limited,running_for_reelection,status_code,source_id,last_updated)
        VALUES (?,?,?,?,?,'OK',5,?)""", (r, inc, incp, tl, running, TODAY))
    add_cand(r, dnom, "D", st, "Governor", 1 if dnom == inc else 0)
    add_cand(r, rnom, "R", st, "Governor", 1 if rnom == inc else 0)
    if other:
        add_cand(r, other.split(" (")[0], "I", st, "Governor", 0, "Declared")

# ------------------------------------------------------------- ratings
# Cook Political Report 상원 (2026-08-20 스냅샷). 출처 확인된 항목만.
# 2026-08-20 자 등급 "변경"이 직접 확인된 항목만 입력한다.
# GA/MI/ME/NC/OH 의 Cook 등급은 날짜가 특정된 1차 확인이 없어 의도적으로 비워 둔다.
COOK_SEN = {"IA":"TOSSUP","TX":"TOSSUP"}
# Almanac of American Politics (2026-08-24): AK/IA/OH/TX 를 Lean R -> Toss-up 으로 이동
ALMANAC_SEN = {"AK":"TOSSUP","IA":"TOSSUP","OH":"TOSSUP","TX":"TOSSUP"}
# Cook 주지사 (2026-08-20), Sabato 주지사 (2026-08-13 / 08-26)
COOK_GOV = {"IA":"LEAN_D","TX":"LIKELY_R"}
SABATO_GOV = {"WI":"LEAN_D","TX":"LIKELY_R"}

rt = 0
def add_rating(state, office, rater, code, asof, src):
    global rt
    row = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                      (state, office)).fetchone()
    if not row:
        return
    rt += 1
    cur.execute("""INSERT OR IGNORE INTO race_rating(rating_id,race_id,rater,rating_code,
        as_of_date,source_id) VALUES (?,?,?,?,?,?)""", (rt, row[0], rater, code, asof, src))

for s, c in COOK_SEN.items():
    add_rating(s, "U.S. Senate", "Cook Political Report", c, "2026-08-20", 6)
for s, c in ALMANAC_SEN.items():
    add_rating(s, "U.S. Senate", "Almanac of American Politics", c, "2026-08-24", 2)
for s, c in COOK_GOV.items():
    add_rating(s, "Governor", "Cook Political Report", c, "2026-08-20", 3)
for s, c in SABATO_GOV.items():
    add_rating(s, "Governor", "Sabato Crystal Ball", c, "2026-08-26", 3)

# ------------------------------------- 데이터센터: 벤더 카운트만 (STEP 4 예고)
# 정의가 다른 두 벤더의 수치를 병렬 저장. 절대 합치지 않는다.
cur.executemany("""INSERT INTO dc_vendor_count(vendor_id,state_code,snapshot_date,
    total_count,total_pipeline_mw,status_code,source_id) VALUES (?,?,?,?,?,'OK',?)""", [
    (1,"TX","2026-08-26",1330,127662,11),
    (1,"VA","2026-08-26",1030,58000,11),
    (1,"GA","2026-08-26",477,None,11),
    (1,"PA","2026-08-26",368,None,11),
    (1,"OH","2026-08-26",349,None,11),
    (2,"TX","2026-02-20",578,None,12),
    (2,"VA","2026-02-20",484,None,12),
    (2,"CA","2026-02-20",393,None,12),
])
cur.execute("""INSERT INTO source_conflict(conflict_id,target_table,target_pk,target_field,
    source_id_a,value_a,source_id_b,value_b,resolution,note,logged_at) VALUES
    (1,'dc_vendor_count','TX','total_count',11,'1330 (Aterio, 발표단계 포함)',
     12,'578 (dcmap, 전 상태 시설)','BOTH_VALID_DIFFERENT_DEFINITION',
     '카운팅 단위와 포함 단계가 달라 직접 비교 불가. 벤더 내부에서만 순위 계산할 것.',?)""",
    (TODAY,))

con.commit()

# ------------------------------------------------------------- 검증 출력
def q(sql):
    return cur.execute(sql).fetchall()

print("states:", q("select count(*) from state_political_structure")[0][0])
print("senate races:", q("select count(*) from election_race where office='U.S. Senate'")[0][0])
print("  regular/special:", q("""select election_type,count(*) from election_race
      where office='U.S. Senate' group by 1"""))
print("  R-held seats up:", q("""select count(*) from election_race
      where office='U.S. Senate' and incumbent_party='R'""")[0][0])
print("  D-held seats up:", q("""select count(*) from election_race
      where office='U.S. Senate' and incumbent_party='D'""")[0][0])
print("  open seats:", q("""select count(*) from election_race
      where office='U.S. Senate' and is_open_seat=1""")[0][0])
print("governor races:", q("select count(*) from election_race where office='Governor'")[0][0])
print("  term-limited:", q("select count(*) from governor_race_detail where term_limited=1")[0][0])
print("  D-held / R-held up:", q("""select current_party,count(*) from governor_race_detail
      group by 1"""))
print("gov party split (all 50):", q("""select governor_party,count(*)
      from state_political_structure group by 1"""))
print("candidates:", q("select count(*) from candidate")[0][0])
print("ratings:", q("select count(*) from race_rating")[0][0])
print("exposure view:", q("select * from v_state_election_exposure order by tossup_races desc limit 5"))
con.close()
print("\nDB written:", DB)
