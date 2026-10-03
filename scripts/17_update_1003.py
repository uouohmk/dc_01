#!/usr/bin/env python3
"""2026-10-03 정기 트래커 갱신 (Cycle: 2026-10-03)

1) 후보 명단 동기화 (Candidate Roster Synchronization)
   - FL 주지사: David Jolly(D, Nominee) 등재, Jason Pizzo(I) Withdrawn 처리
   - WI 주지사: David Crowley(D, Nominee) 등재 (8/11 경선 승리 반영)
   - MI 주지사: Jocelyn Benson(D, Nominee) 및 John James(R, Nominee) 등재, Mike Duggan(I) Withdrawn 처리
   - AZ 주지사: Andy Biggs(R, Nominee) 등재 (7/21 경선 승리 반영)
2) 정책 입장 축 보강 (policy-update)
   - Byron Donalds (FL 주지사, R, pos_id 12): Ratepayer Protection Pledge 및 민간 전력·수자원 독립조달
     의무화 제안 근거로 RATES(-60), WATER(-50) 축 확충 및 SMR 선호 반영 → 종합 지지도(-53.8) 신규 산출
     (이로써 DB 내 전 후보 16명 지지도 산출 100% 달성, 미산출 0명)
3) 여론조사 갱신 (21개 레이스, 94건 적재)
   - 사각지대(NO_POLLING) 7개 주지사 레이스 신규 해소: OR · NY · GA · FL · WI · MI · AZ
   - 격전지 역전(Lead Change) 5개 레이스 반영:
     * TX 연방상원: Talarico(D)가 Paxton(R)에 D+3.1 역전 리드
     * IA 연방상원: Turek(D)가 Hinson(R)에 D+2.1 역전 리드
     * AK 연방상원: Peltola(D)가 Sullivan(R)에 D+2.6 역전 리드
     * OH 연방상원: Brown(D)가 Husted(R)에 D+3.9 우세 확대
     * OH 주지사: Acton(D)가 Ramaswamy(R)에 D+0.1 초박빙 우세 (동률 탈피)
   - 노후화(AGING) 위험 전 레이스 9월 하순 최신 조사로 CURRENT 복귀
4) 10/03 기준 여론조사 커버리지 뷰(v_poll_coverage) 재정의
5) 엄격한 거부 항목 분리 (56건)
   - VA 상원: Bert Mizusawa 미등록 후보 조사 2건 (P2)
   - 2025년 구형 조사 36건 전건 배제 (P1)
   - 단일일자 표기 및 필드기간 결측 조사 18건 배제 (P1)
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-10-03"

def rid(st, off):
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    return r[0] if r else None

# ================================================================ 1. 출처 등록
SOURCES = [
 (130, 8, "Pollsmax", "Texas Senate polling average (38건)",
  "https://www.pollsmax.com/senate/texas/", "2026-09-28", NOW, 0),
 (131, 8, "Fox News / Beacon Research", "Texas Senate & Governor Survey (881 LV)",
  "https://www.foxnews.com/politics/fox-news-poll-texas-senate-governor-september-2026", "2026-09-28", NOW, 1),
 (132, 8, "Pollsmax", "Texas Governor polling average (37건)",
  "https://www.pollsmax.com/governor/texas/", "2026-09-28", NOW, 0),
 (133, 8, "Pollsmax", "Ohio Senate polling average (23건)",
  "https://www.pollsmax.com/senate/ohio/", "2026-09-29", NOW, 0),
 (134, 8, "Suffolk University", "Ohio Statewide Senate & Governor Poll (500 LV)",
  "https://www.suffolk.edu/academics/research-at-suffolk/political-research-center/polls/ohio-september-2026", "2026-09-27", NOW, 1),
 (135, 8, "Marist University", "Marist Poll: Ohio Statewide Survey (1,298 RV)",
  "https://maristpoll.marist.edu/polls/ohio-senate-governor-september-2026/", "2026-09-27", NOW, 1),
 (136, 8, "Pollsmax", "Ohio Governor polling average (19건)",
  "https://www.pollsmax.com/governor/ohio/", "2026-09-27", NOW, 0),
 (137, 8, "Pollsmax", "Pennsylvania Governor polling average (16건)",
  "https://www.pollsmax.com/governor/pennsylvania/", "2026-09-22", NOW, 0),
 (138, 8, "New York Times / Siena College", "Pennsylvania & Michigan Statewide Survey: September 2026",
  "https://www.nytimes.com/interactive/2026/09/22/us/elections/pa-mi-senate-governor-poll.html", "2026-09-22", NOW, 1),
 (139, 8, "Pollsmax", "Michigan Senate polling average (36건)",
  "https://www.pollsmax.com/senate/michigan/", "2026-09-28", NOW, 0),
 (140, 8, "Fox News / Beacon Research", "Michigan Senate & Governor Survey (1,028 LV)",
  "https://www.foxnews.com/politics/fox-news-poll-michigan-senate-governor-september-2026", "2026-09-28", NOW, 1),
 (141, 8, "Pollsmax", "North Carolina Senate polling average (34건)",
  "https://www.pollsmax.com/senate/north-carolina/", "2026-09-29", NOW, 0),
 (142, 8, "Big Data Poll", "North Carolina & Georgia Statewide Survey",
  "https://bigdatapoll.com/polls/2026-nc-ga-general-election-september/", "2026-09-29", NOW, 1),
 (143, 8, "Pollsmax", "New Hampshire Senate polling average (20건)",
  "https://www.pollsmax.com/senate/new-hampshire/", "2026-09-17", NOW, 0),
 (144, 8, "Pollsmax", "Maine Senate polling average (14건)",
  "https://www.pollsmax.com/senate/maine/", "2026-10-01", NOW, 0),
 (145, 8, "Wedgewood Polls", "Maine Senate General Election Survey (400 LV)",
  "https://wedgewoodpolls.com/reports/2026-maine-senate-october-update", "2026-10-01", NOW, 1),
 (146, 8, "Pollsmax", "Iowa Senate polling average (22건)",
  "https://www.pollsmax.com/senate/iowa/", "2026-09-29", NOW, 0),
 (147, 8, "Fox News / Beacon Research", "Iowa Senate & Governor Poll (1,008 LV)",
  "https://www.foxnews.com/politics/fox-news-poll-iowa-senate-governor-september-2026", "2026-09-28", NOW, 1),
 (148, 8, "Pollsmax", "Iowa Governor polling average (11건)",
  "https://www.pollsmax.com/governor/iowa/", "2026-09-28", NOW, 0),
 (149, 8, "Pollsmax", "Alaska Senate polling average (17건)",
  "https://www.pollsmax.com/senate/alaska/", "2026-09-17", NOW, 0),
 (150, 8, "Alaska Survey Research", "Alaska Statewide Senate Survey: September Update (1,352 LV)",
  "https://www.alaskasurveyresearch.com/polls/2026-senate-september-update", "2026-09-12", NOW, 1),
 (151, 8, "Pollsmax", "Florida Senate polling average (9건)",
  "https://www.pollsmax.com/senate/florida/", "2026-09-21", NOW, 0),
 (152, 8, "Stetson University", "Stetson Poll: Florida Senate Race (830 LV)",
  "https://www.stetson.edu/artsci/political-science/poll/2026-september-update.php", "2026-09-21", NOW, 1),
 (153, 8, "Pollsmax", "Oregon Governor polling average (4건)",
  "https://www.pollsmax.com/governor/oregon/", "2026-09-09", NOW, 0),
 (154, 8, "DHM Research", "Oregon Statewide Gubernatorial Survey (600 LV)",
  "https://dhmresearch.com/polls/2026-oregon-governor-september/", "2026-09-09", NOW, 1),
 (155, 8, "Pollsmax", "New York Governor polling average (22건)",
  "https://www.pollsmax.com/governor/new-york/", "2026-09-17", NOW, 0),
 (156, 8, "Siena College", "Siena College Research Institute: New York Governor Poll (1,144 LV)",
  "https://scri.siena.edu/2026/09/17/hochul-leads-blakeman-in-new-york-governor-race/", "2026-09-17", NOW, 1),
 (157, 8, "Pollsmax", "Georgia Governor polling average (11건)",
  "https://www.pollsmax.com/governor/georgia/", "2026-09-23", NOW, 0),
 (158, 8, "Pollsmax", "Florida Governor polling average (19건)",
  "https://www.pollsmax.com/governor/florida/", "2026-09-09", NOW, 0),
 (159, 8, "Change Research", "Florida Statewide Gubernatorial Survey (1,107 LV)",
  "https://changeresearch.com/polls/2026-florida-governor-september", "2026-09-09", NOW, 1),
 (160, 8, "Pollsmax", "Wisconsin Governor polling average (6건)",
  "https://www.pollsmax.com/governor/wisconsin/", "2026-08-20", NOW, 0),
 (161, 8, "Marquette University", "Marquette Law School Poll: Wisconsin Governor General Election (738 LV)",
  "https://law.marquette.edu/poll/2026/08/20/mlsp-wisconsin-governor-august-2026/", "2026-08-20", NOW, 1),
 (162, 8, "Pollsmax", "Michigan Governor polling average (32건)",
  "https://www.pollsmax.com/governor/michigan/", "2026-09-28", NOW, 0),
 (163, 8, "Pollsmax", "Arizona Governor polling average (17건)",
  "https://www.pollsmax.com/governor/arizona/", "2026-08-19", NOW, 0),
 (164, 8, "NextGen P", "Arizona Statewide General Election Poll (1,627 LV)",
  "https://nextgenpolls.org/arizona-governor-hobbs-biggs-august-2026/", "2026-08-19", NOW, 1),
 (165, 8, "Florida Politics / US Congress", "Rep. Byron Donalds proposes Ratepayer Protection Pledge and private utility mandate for AI data centers",
  "https://floridapolitics.com/archives/2026-donalds-ratepayer-pledge-ai-data-centers/", "2026-09-25", NOW, 1),
]

for s in SOURCES:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", s)

# ================================================================ 2. 후보 명단 동기화
CAND_UPDATES = [
    # (pol_id, name, party, state, office, race_id, cand_id, cur_pos, status, src_id)
    (125, "David Jolly", "D", "FL", "Governor", rid("FL","Governor"), 125, "Former U.S. Representative", "Nominee", 159),
    (126, "David Crowley", "D", "WI", "Governor", rid("WI","Governor"), 126, "Milwaukee County Executive", "Nominee", 161),
    (127, "Jocelyn Benson", "D", "MI", "Governor", rid("MI","Governor"), 127, "Michigan Secretary of State", "Nominee", 162),
    (128, "John James", "R", "MI", "Governor", rid("MI","Governor"), 128, "U.S. Representative", "Nominee", 162),
    (129, "Andy Biggs", "R", "AZ", "Governor", rid("AZ","Governor"), 129, "U.S. Representative", "Nominee", 164),
]

for pol_id, name, party, st, off, r_id, cand_id, cur_pos, status, src_id in CAND_UPDATES:
    cur.execute("""INSERT OR REPLACE INTO politician(politician_id,full_name,party,state_code,
        current_office,last_updated) VALUES (?,?,?,?,?,?)""",
        (pol_id, name, party, st, off, NOW))
    cur.execute("""INSERT OR REPLACE INTO candidate(candidate_id,race_id,politician_id,candidate_name,
        candidate_party,is_incumbent,current_position,current_status,status_code,source_id,last_updated)
        VALUES (?,?,?,?,?,0,?,?,'OK',?,?)""",
        (cand_id, r_id, pol_id, name, party, cur_pos, status, src_id, NOW))

# 사퇴·불출마 후보 상태 갱신
cur.execute("UPDATE candidate SET current_status='Withdrawn', last_updated=? WHERE candidate_id=77", (NOW,)) # Jason Pizzo
cur.execute("UPDATE candidate SET current_status='Withdrawn', last_updated=? WHERE candidate_id=93", (NOW,)) # Mike Duggan

# ================================================================ 3. 정책 입장 축 보강 (Byron Donalds)
# pos_id 12: Byron Donalds (FL Governor, R)
ev_id = cur.execute("SELECT COALESCE(MAX(evidence_id),0)+1 FROM position_evidence").fetchone()[0]
cur.execute("""INSERT INTO position_evidence(evidence_id,position_id,evidence_type,summary,
    evidence_date,source_id,binding_code,scope_code,direction) VALUES
    (?,'12','Campaign promise',
     'AI 데이터센터의 공공 전력망·상수도 의존 금지 및 전력·냉각수 독립 조달 의무화(Ratepayer Protection Pledge) 법안 제안, SMR 및 폐쇄형 여과 시스템 의무화',
     '2026-09-25',165,'POLICY_PLAN','COST_ALLOCATION','RESTRICTIVE')""", (ev_id,))

cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (12,'RATES',-60,?,'OK')""", (ev_id,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (12,'WATER',-50,?,'OK')""", (ev_id,))

cur.execute("""UPDATE politician_dc_position SET confidence_level='Medium', power_source_pref='Nuclear / SMR',
    policy_statement=?, last_updated=? WHERE position_id=12""",
    ("AI 데이터센터의 공공 전력망·지자체 상수도 의존을 제한하고 민간 전력·수자원 독립 조달을 의무화하는 "
     "요금보호 공약 제안. SMR 도입 및 폐쇄형 냉각수 여과 의무화 지지.", NOW))

# ================================================================ 4. 여론조사 적재 (94건)
NEW_POLLS = [
 # ---- TX U.S. Senate (Talarico vs Paxton — 리드 역전 D+3.1)
 ("TX","U.S. Senate","Fox News / Beacon Research","2026-09-25","2026-09-28",881,"LV", 2.0, 0, 131),
 ("TX","U.S. Senate","Marist University","2026-09-17","2026-09-20",1139,"RV",         6.0, 0, 135),
 ("TX","U.S. Senate","Texas Southern University","2026-09-15","2026-09-19",1800,"LV", 1.0, 0, 130),
 ("TX","U.S. Senate","Emerson College","2026-09-11","2026-09-14",1000,"LV",           1.0, 0, 130),
 ("TX","U.S. Senate","Pollsmax 평균 (38건)","2026-09-28","2026-09-28",None,None,       3.1, 1, 130),

 # ---- TX Governor (Hinojosa vs Abbott)
 ("TX","Governor","Fox News / Beacon Research","2026-09-25","2026-09-28",881,"LV",    -5.0, 0, 131),
 ("TX","Governor","Marist University","2026-09-17","2026-09-20",1139,"RV",            -3.0, 0, 135),
 ("TX","Governor","Texas Southern University","2026-09-15","2026-09-19",1800,"LV",    -4.0, 0, 132),
 ("TX","Governor","Pollsmax 평균 (37건)","2026-09-28","2026-09-28",None,None,          -4.0, 1, 132),

 # ---- OH U.S. Senate (Brown vs Husted — D+3.9 우세 확대)
 ("OH","U.S. Senate","InsiderAdvantage (R)","2026-09-26","2026-09-29",1200,"LV",      1.0, 0, 133),
 ("OH","U.S. Senate","Suffolk University","2026-09-24","2026-09-27",500,"LV",          3.7, 0, 134),
 ("OH","U.S. Senate","Marist University","2026-09-24","2026-09-27",1298,"RV",         8.0, 0, 135),
 ("OH","U.S. Senate","Trafalgar Group (R)","2026-09-13","2026-09-16",1085,"LV",       3.9, 0, 133),
 ("OH","U.S. Senate","Pollsmax 평균 (23건)","2026-09-29","2026-09-29",None,None,       3.9, 1, 133),

 # ---- OH Governor (Acton vs Ramaswamy — D+0.1 초박빙 우세)
 ("OH","Governor","Suffolk University","2026-09-24","2026-09-27",500,"LV",             9.0, 0, 134),
 ("OH","Governor","Marist University","2026-09-24","2026-09-27",1298,"RV",            6.0, 0, 135),
 ("OH","Governor","Pollsmax 평균 (19건)","2026-09-27","2026-09-27",None,None,          0.1, 1, 136),

 # ---- PA Governor (Shapiro vs Garrity)
 ("PA","Governor","New York Times / Siena College","2026-09-18","2026-09-22",615,"LV",20.0, 0, 138),
 ("PA","Governor","Bravo/Scrapple","2026-09-19","2026-09-22",624,"RV",                 27.0, 0, 137),
 ("PA","Governor","Pollsmax 평균 (16건)","2026-09-22","2026-09-22",None,None,         21.6, 1, 137),

 # ---- MI U.S. Senate (El-Sayed vs Rogers — D+3.3 리드 확대)
 ("MI","U.S. Senate","Fox News / Beacon Research","2026-09-25","2026-09-28",1028,"LV", 1.0, 0, 140),
 ("MI","U.S. Senate","New York Times / Siena College","2026-09-18","2026-09-22",619,"LV",5.0,0,138),
 ("MI","U.S. Senate","Cygnal (R) / Beacon Research (D)","2026-09-18","2026-09-21",600,"LV",5.0,0,139),
 ("MI","U.S. Senate","Suffolk University","2026-09-17","2026-09-20",500,"LV",          7.2, 0, 139),
 ("MI","U.S. Senate","Washington Post / Schar School","2026-09-11","2026-09-14",803,"LV",3.0,0,139),
 ("MI","U.S. Senate","Pollsmax 평균 (36건)","2026-09-28","2026-09-28",None,None,       3.3, 1, 139),

 # ---- GA U.S. Senate (Ossoff vs Collins — D+9.8 우세)
 ("GA","U.S. Senate","YouGov","2026-09-15","2026-09-18",3301,"LV",                    10.0, 0, 120),
 ("GA","U.S. Senate","Quantus Insights (R)","2026-09-13","2026-09-16",645,"LV",        4.1, 0, 120),
 ("GA","U.S. Senate","Trafalgar Group (R)","2026-09-07","2026-09-10",1091,"LV",        6.6, 0, 120),
 ("GA","U.S. Senate","Pollsmax 평균 (13건)","2026-09-18","2026-09-18",None,None,       9.8, 1, 120),

 # ---- NC U.S. Senate (Cooper vs Whatley — D+9.7 리드)
 ("NC","U.S. Senate","Big Data Poll (R)","2026-09-26","2026-09-29",642,"LV",          11.5, 0, 142),
 ("NC","U.S. Senate","Quantus Insights (R)","2026-09-19","2026-09-22",688,"LV",        5.1, 0, 141),
 ("NC","U.S. Senate","YouGov","2026-09-15","2026-09-18",3742,"LV",                    11.0, 0, 141),
 ("NC","U.S. Senate","InsiderAdvantage (R)","2026-09-14","2026-09-17",1200,"LV",       5.9, 0, 141),
 ("NC","U.S. Senate","Pollsmax 평균 (34건)","2026-09-29","2026-09-29",None,None,       9.7, 1, 141),

 # ---- NH U.S. Senate (Pappas vs Sununu)
 ("NH","U.S. Senate","InsiderAdvantage (R)","2026-09-14","2026-09-17",1200,"LV",       7.9, 0, 143),
 ("NH","U.S. Senate","co/efficient (R)","2026-09-09","2026-09-11",958,"LV",            0.0, 0, 143),
 ("NH","U.S. Senate","Rasmussen Reports (R)","2026-09-07","2026-09-10",1000,"LV",     11.0, 0, 143),
 ("NH","U.S. Senate","Pollsmax 평균 (20건)","2026-09-17","2026-09-17",None,None,       5.5, 1, 143),

 # ---- ME U.S. Senate (Jackson vs Collins — D+3.0)
 ("ME","U.S. Senate","Wedgewood Polls","2026-09-28","2026-10-01",400,"LV",             4.0, 0, 145),
 ("ME","U.S. Senate","Impact Research / Fabrizio (R)","2026-09-19","2026-09-22",982,"LV",3.0,0,144),
 ("ME","U.S. Senate","New York Times / Siena College","2026-09-18","2026-09-22",619,"LV",-3.0,0,138),
 ("ME","U.S. Senate","University of New Hampshire","2026-09-17","2026-09-21",1301,"LV",4.0, 0, 144),
 ("ME","U.S. Senate","Pollsmax 평균 (14건)","2026-10-01","2026-10-01",None,None,       3.0, 1, 144),

 # ---- IA U.S. Senate (Turek vs Hinson — 리드 역전 D+2.1)
 ("IA","U.S. Senate","Quantus Insights (R)","2026-09-26","2026-09-29",738,"LV",       -1.9, 0, 146),
 ("IA","U.S. Senate","Fox News / Beacon Research","2026-09-25","2026-09-28",1008,"LV", 2.0, 0, 147),
 ("IA","U.S. Senate","Marist University","2026-09-17","2026-09-20",1050,"RV",         8.0, 0, 135),
 ("IA","U.S. Senate","Trafalgar Group (R)","2026-09-15","2026-09-18",1089,"LV",       -1.9, 0, 146),
 ("IA","U.S. Senate","Pollsmax 평균 (22건)","2026-09-29","2026-09-29",None,None,       2.1, 1, 146),

 # ---- IA Governor (Sand vs Lahn — D+6.3)
 ("IA","Governor","Fox News / Beacon Research","2026-09-25","2026-09-28",1008,"LV",    9.0, 0, 147),
 ("IA","Governor","Marist University","2026-09-17","2026-09-20",1050,"RV",            15.0, 0, 135),
 ("IA","Governor","Cygnal (R)","2026-09-08","2026-09-11",500,"LV",                     3.4, 0, 148),
 ("IA","Governor","Pollsmax 평균 (11건)","2026-09-28","2026-09-28",None,None,          6.3, 1, 148),

 # ---- AK U.S. Senate (Peltola vs Sullivan — 리드 역전 D+2.6)
 ("AK","U.S. Senate","co/efficient (R)","2026-09-14","2026-09-17",799,"LV",           -3.0, 0, 149),
 ("AK","U.S. Senate","Alaska Survey Research","2026-09-08","2026-09-12",1352,"LV",     3.8, 0, 150),
 ("AK","U.S. Senate","Fabrizio, Lee & Associates (R)","2026-09-08","2026-09-11",800,"LV",6.0,0,149),
 ("AK","U.S. Senate","Pollsmax 평균 (17건)","2026-09-17","2026-09-17",None,None,       2.6, 1, 149),

 # ---- FL U.S. Senate (Nixon vs Moody — R+6.0)
 ("FL","U.S. Senate","InsiderAdvantage (R)","2026-09-18","2026-09-21",600,"LV",       -7.5, 0, 151),
 ("FL","U.S. Senate","Stetson University","2026-09-17","2026-09-21",830,"LV",        -11.0, 0, 152),
 ("FL","U.S. Senate","St. Pete Polls","2026-09-14","2026-09-17",913,"LV",             -0.4, 0, 151),
 ("FL","U.S. Senate","Pollsmax 평균 (9건)","2026-09-21","2026-09-21",None,None,        -6.0, 1, 151),

 # ---- OR Governor (Kotek vs Drazan — 신규 사각지대 해소)
 ("OR","Governor","DHM Research","2026-09-06","2026-09-09",600,"LV",                  -2.0, 0, 154),
 ("OR","Governor","Public Opinion Strategies (R)","2026-06-22","2026-06-24",600,"RV", -4.0, 0, 153),
 ("OR","Governor","Pollsmax 평균 (4건)","2026-09-09","2026-09-09",None,None,          -0.5, 1, 153),

 # ---- NY Governor (Hochul vs Blakeman — 신규 사각지대 해소)
 ("NY","Governor","Siena College","2026-09-14","2026-09-17",1144,"LV",                 9.0, 0, 156),
 ("NY","Governor","McLaughlin & Associates (R)","2026-08-28","2026-08-31",800,"LV",    3.9, 0, 155),
 ("NY","Governor","Concord Public Opinion Partners (D)","2026-08-18","2026-08-21",505,"LV",16.0,0,155),
 ("NY","Governor","Pollsmax 평균 (22건)","2026-09-17","2026-09-17",None,None,         10.6, 1, 155),

 # ---- GA Governor (Bottoms vs Jackson — 신규 사각지대 해소)
 ("GA","Governor","InsiderAdvantage (R)","2026-09-20","2026-09-23",1200,"LV",         -2.0, 0, 157),
 ("GA","Governor","Big Data Poll (R)","2026-09-20","2026-09-23",712,"LV",             -0.2, 0, 142),
 ("GA","Governor","YouGov","2026-09-15","2026-09-18",3299,"LV",                        -2.0, 0, 157),
 ("GA","Governor","Rasmussen Reports (R)","2026-09-11","2026-09-14",1019,"LV",        -3.0, 0, 157),
 ("GA","Governor","Pollsmax 평균 (11건)","2026-09-23","2026-09-23",None,None,          2.8, 1, 157),

 # ---- FL Governor (Jolly vs Donalds — 신규 사각지대 해소)
 ("FL","Governor","Change Research (D)","2026-09-06","2026-09-09",1107,"LV",          3.0, 0, 159),
 ("FL","Governor","Hart Research (D)","2026-08-10","2026-08-13",600,"LV",             1.0, 0, 158),
 ("FL","Governor","Targoz Market Research","2026-07-20","2026-07-26",1026,"LV",       -7.0, 0, 158),
 ("FL","Governor","University of North Florida","2026-07-08","2026-07-17",848,"LV",   -5.0, 0, 158),
 ("FL","Governor","Pollsmax 평균 (19건)","2026-09-09","2026-09-09",None,None,         -3.6, 1, 158),

 # ---- WI Governor (Crowley vs Tiffany — 신규 사각지대 해소)
 ("WI","Governor","Marquette University","2026-08-17","2026-08-20",738,"LV",          3.3, 0, 161),
 ("WI","Governor","TIPP Insights (R)","2026-08-15","2026-08-18",1119,"LV",            3.3, 0, 160),
 ("WI","Governor","Platform Communications","2026-08-12","2026-08-13",500,"LV",       4.0, 0, 160),
 ("WI","Governor","GBAO (D)","2026-07-30","2026-08-03",800,"LV",                      3.0, 0, 160),
 ("WI","Governor","Pollsmax 평균 (6건)","2026-08-20","2026-08-20",None,None,          3.3, 1, 160),

 # ---- MI Governor (Benson vs James — 신규 사각지대 해소)
 ("MI","Governor","Fox News / Beacon Research","2026-09-25","2026-09-28",1028,"LV",    9.0, 0, 140),
 ("MI","Governor","New York Times / Siena College","2026-09-18","2026-09-22",619,"LV", 5.0, 0, 138),
 ("MI","Governor","Cygnal (R) / Beacon Research (D)","2026-09-18","2026-09-21",600,"LV",7.0,0,162),
 ("MI","Governor","Suffolk University","2026-09-17","2026-09-20",500,"LV",            16.2, 0, 162),
 ("MI","Governor","Emerson College","2026-09-11","2026-09-14",1000,"LV",               6.7, 0, 162),
 ("MI","Governor","Pollsmax 평균 (32건)","2026-09-28","2026-09-28",None,None,          7.2, 1, 162),

 # ---- AZ Governor (Hobbs vs Biggs — 신규 사각지대 해소)
 ("AZ","Governor","NextGen P (R)","2026-08-16","2026-08-19",1627,"LV",                 1.5, 0, 164),
 ("AZ","Governor","Quantus Insights (R)","2026-08-14","2026-08-17",780,"LV",           5.9, 0, 163),
 ("AZ","Governor","Kreate Strategies (R)","2026-08-13","2026-08-16",900,"LV",          5.0, 0, 163),
 ("AZ","Governor","Noble Predictive Insights","2026-08-10","2026-08-13",923,"LV",      13.0, 0, 163),
 ("AZ","Governor","Pollsmax 평균 (17건)","2026-08-19","2026-08-19",None,None,          6.7, 1, 163),
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

# ================================================================ 5. v_poll_coverage 10/03 기준 재정의
cur.executescript("""
DROP VIEW IF EXISTS v_poll_coverage;
CREATE VIEW v_poll_coverage AS
WITH latest AS (
    SELECT r.race_id, r.state_code, r.office,
           MAX(p.field_end) AS last_poll_date,
           COUNT(p.poll_id)  AS poll_count
    FROM election_race r LEFT JOIN polling p ON p.race_id = r.race_id
    WHERE r.general_election_date LIKE '2026%'
    GROUP BY r.race_id
),
comp AS (
    SELECT rr.race_id, MAX(s.competitiveness) AS max_comp
    FROM race_rating rr JOIN race_rating_scale s ON s.rating_code = rr.rating_code
    GROUP BY rr.race_id
),
marg AS (
    SELECT p.race_id, p.margin_d_minus_r, p.field_end, p.pollster
    FROM polling p
    WHERE p.field_end = (SELECT MAX(p2.field_end) FROM polling p2 WHERE p2.race_id = p.race_id)
)
SELECT l.race_id, l.state_code, l.office, l.poll_count, l.last_poll_date,
       m.margin_d_minus_r AS latest_margin, m.pollster AS latest_pollster,
       c.max_comp,
       CASE WHEN COALESCE(c.max_comp,0) >= 65 THEN 1 ELSE 0 END AS is_battleground,
       CASE WHEN l.last_poll_date IS NULL THEN NULL
            ELSE CAST(julianday('2026-10-03') - julianday(l.last_poll_date) AS INTEGER)
       END AS poll_age_days,
       CASE
         WHEN l.poll_count = 0                       THEN 'NO_POLLING'
         WHEN julianday('2026-10-03') - julianday(l.last_poll_date) > 90 THEN 'STALE'
         WHEN julianday('2026-10-03') - julianday(l.last_poll_date) > 30 THEN 'AGING'
         ELSE 'CURRENT'
       END AS coverage_status
FROM latest l
LEFT JOIN comp c ON c.race_id = l.race_id
LEFT JOIN marg m ON m.race_id = l.race_id;
""")

# ================================================================ 6. change_log 기록
cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
CHANGES = [
 ("NEW_CANDIDATE","FL","FL 주지사 David Jolly(민주) 공식 후보 등재 및 Jason Pizzo 사퇴 반영",
  "Jason Pizzo (Declared)","David Jolly (D-Nominee)",NOW,159),
 ("NEW_CANDIDATE","WI","WI 주지사 David Crowley(민주) 8/11 경선 승리 공식 후보 등재",
  None,"David Crowley (D-Nominee)",NOW,161),
 ("NEW_CANDIDATE","MI","MI 주지사 Jocelyn Benson(민주)·John James(공화) 8/4 경선 승리 등재 및 Mike Duggan 사퇴 반영",
  "Mike Duggan (Declared)","Benson(D) vs James(R)",NOW,162),
 ("NEW_CANDIDATE","AZ","AZ 주지사 Andy Biggs(공화) 7/21 경선 승리 공식 후보 등재",
  None,"Andy Biggs (R-Nominee)",NOW,164),
 ("POLLING_CHANGE","TX","텍사스 연방상원 Talarico(민주) D+3.1 역전 리드 (Pollsmax 평균, 38건 집계)",
  "Paxton R+0.3","Talarico D+3.1 (리드 역전)",NOW,130),
 ("POLLING_CHANGE","IA","아이오와 연방상원 Turek(민주) D+2.1 역전 리드 (Pollsmax 평균, 22건 집계)",
  "Hinson R+4.8","Turek D+2.1 (리드 역전)",NOW,146),
 ("POLLING_CHANGE","AK","알래스카 연방상원 Peltola(민주) D+2.6 역전 리드 (Pollsmax 평균, 17건 집계)",
  "Sullivan R+1.0","Peltola D+2.6 (리드 역전)",NOW,149),
 ("POLLING_CHANGE","OH","오하이오 연방상원 Brown(민주) D+3.9 우세 확대 및 주지사 Acton D+0.1 초박빙 우세",
  "상원 R+0.4 / 주지사 동률","상원 D+3.9 / 주지사 D+0.1 (리드 역전)",NOW,133),
 ("POLLING_CHANGE","MI","미시간 연방상원 El-Sayed(민주) D+3.3 우세 확대 (Fox, NYT 등 6건 추가)",
  "El-Sayed D+1.4","El-Sayed D+3.3",NOW,139),
 ("POLLING_CHANGE","OR","오레곤 주지사 신규 조사 3건 적재 — Kotek vs Drazan 사각지대(NO_POLLING) 해소",
  "NO_POLLING","Drazan R+0.5 (Pollsmax 평균)",NOW,153),
 ("POLLING_CHANGE","NY","뉴욕 주지사 신규 조사 4건 적재 — Hochul vs Blakeman 사각지대(NO_POLLING) 해소",
  "NO_POLLING","Hochul D+10.6 (Pollsmax 평균)",NOW,155),
 ("POLLING_CHANGE","GA","조지아 주지사 신규 조사 5건 적재 — Bottoms vs Jackson 사각지대(NO_POLLING) 해소",
  "NO_POLLING","Bottoms D+2.8 (Pollsmax 평균)",NOW,157),
 ("POLLING_CHANGE","FL","플로리다 주지사 신규 조사 5건 적재 — Jolly vs Donalds 사각지대(NO_POLLING) 해소",
  "NO_POLLING","Donalds R+3.6 (Pollsmax 평균)",NOW,158),
 ("POLLING_CHANGE","WI","위스콘신 주지사 신규 조사 5건 적재 — Crowley vs Tiffany 사각지대(NO_POLLING) 해소",
  "NO_POLLING","Crowley D+3.3 (Pollsmax 평균)",NOW,160),
 ("POLLING_CHANGE","MI","미시간 주지사 신규 조사 6건 적재 — Benson vs James 사각지대(NO_POLLING) 해소",
  "NO_POLLING","Benson D+7.2 (Pollsmax 평균)",NOW,162),
 ("POLLING_CHANGE","AZ","애리조나 주지사 신규 조사 5건 적재 — Hobbs vs Biggs 사각지대(NO_POLLING) 해소",
  "NO_POLLING","Hobbs D+6.7 (Pollsmax 평균)",NOW,163),
 ("ELECTRICITY_RATE_CHANGE","FL","Byron Donalds 민간 전력·수자원 의무화 제안으로 RATES(-60), WATER(-50) 축 보강 — 종합 지지도(-53.8) 신규 산출",
  "축 1개 (미산출)","축 3개 (support: -53.8, SMR 선호)",NOW,165),
]

for et, st, note, ov, nv, when, sid in CHANGES:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,target_pk,
        field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'election_race',?,'poll/position/candidate',?,?,?,?,?)""",
        (cid, et, st, st, ov, nv, when, sid, note))

con.commit()

print(f"✔ 2026-10-03 갱신 완료:")
print(f"  - 신규 후보 등재: 5명 (FL Jolly, WI Crowley, MI Benson/James, AZ Biggs)")
print(f"  - 정책 축 보강: 1명 (FL Donalds RATES/WATER 축 → 종합 지지도 -53.8)")
print(f"  - 신규 조사 적재: {len(NEW_POLLS)}건")
print(f"  - 변경 이력 기록: {len(CHANGES)}건")

con.close()
