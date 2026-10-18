#!/usr/bin/env python3
"""2026-10-18 정기 트래커 갱신 (Cycle: 2026-10-18)

1) 후보 명단 동기화 (Candidate Roster Synchronization — 6명)
   - MN 주지사: Lisa Demuth(R, Nominee) 8/11 공화 경선 승리 확정 반영 및 Kendall Qualls(R, Withdrawn) 전환
   - MN 연방상원: Peggy Flanagan(D, Nominee) 및 Michele Tafoya(R, Nominee) 8/11 경선 승리 공식 후보 등재
   - KS 주지사: Cindy Holscher(D, Nominee) 및 Ty Masterson(R, Nominee) 8/4 경선 승리 공식 후보 등재
   - KS 연방상원: Adam Hamilton(D, Nominee) 8/4 민주 경선 승리 공식 후보 등재 (Roger Marshall과 본선 대진)
2) 정책 입장 및 레버리지 갱신 (policy-update — 3명)
   - Abdul El-Sayed (MI 연방상원, D, pos_id 15): 10/12 'AI Under Control' 공식 정책안 발표 (하이퍼스케일 데이터센터 연방 모라토리엄, 100% 재생에너지 조달 의무화, 연방·주 세제특혜 전면 폐지)
     → POWER(-50)·TAX(-70) 보강으로 5대 축 완비(3축→5축), 구속력 상향(CAMPAIGN_PROMISE→POLICY_PLAN), 레버리지(22.0→24.8)
   - Stacy Garrity (PA 주지사, R, pos_id 6): 10/14 펜실베이니아 우량 농지 및 농촌 지하수 보호를 위한 데이터센터 산업단지·브라운필드 입지 제한 정책안 발표
     → WATER(-45) 4번째 축 신규 추가(3축→4축), 신뢰도 상향(Medium→High)
   - Amy Acton (OH 주지사, D, pos_id 7): 10/11 'My Promise for Ohio' 정책안 내 데이터센터 비밀유지협약(NDA) 전면 금지 및 엄격한 지역사회·노동·전력요금 기준 미충족 시 주·지자체 세제감면 배제 공약
     → TAX(-60) 4번째 축 신규 추가(3축→4축), 신뢰도 상향(Medium→High)
3) 여론조사 갱신 (23개 레이스, 118건 적재)
   - 사각지대(NO_POLLING) 13개 레이스 신규 해소: MN 주지사 · MN 상원 · KS 주지사 · KS 상원 · NM 주지사 · NM 상원 · NH 주지사 · ME 주지사 · AL 주지사 · CA 주지사 · NE 주지사 · SC 주지사 · SC 상원
   - 기존 추적 10개 레이스 10월 중순 최신 조사 보강: IA 상원 · TX 상원 · TX 주지사 · GA 주지사 · NC 상원 · IA 주지사 · FL 상원 · FL 주지사 · NY 주지사 · AZ 주지사
   - 주요 리드 역전(Lead Change) 및 격차 변동 반영:
     * IA 연방상원 (격전지 리드 재역전!): YouGov(10/12, Turek D+1.0, 2,245 LV) 반영으로 Pollsmax 평균(30건)이 Hinson R+0.1에서 Turek D+0.2로 재역전
     * TX 주지사: ActiVote(R+2), GBAO(D+2), Siena/ReconMR(R+1) 등 접전 조사 반영으로 Abbott 리드 축소(R+4.4 → R+3.4)
     * TX 연방상원: ActiVote(D+4), Siena/ReconMR(D+4), UT/TPP(D+3) 반영으로 Talarico 리드 유지·확대(D+2.7 → D+2.8)
     * KS 연방상원: 사각지대 해소와 동시에 Hamilton(D)이 현역 Marshall(R)에 D+0.8(InsiderAdvantage D+1, YouGov D+3, GBAO D+5) 초접전 우세 확인
4) 10/18 기준 여론조사 커버리지 뷰(v_poll_coverage) 재정의
5) 엄격한 거부 항목 분리 (총 41건: 여론조사 39건 + 정책 2건)
   - 표본크기(sample_size) 결측 배제 (P1): 4건 (10/11 Marist University 조사 — TX 상원, TX 주지사, IA 상원, IA 주지사 4건 모두 'n=LV'로 표본크기 수치 누락)
   - 후보 대진 불일치 배제 (P2): 17건
     * AK 주지사 5건: Pollsmax가 Top-4 예비선거 후보 중 Kreiss-Tomkins(D) vs Wilson(R) 대진으로 집계하여 DB 등록 본선 주자(Tom Begich / Bill Walker)와 불일치
     * NE 연방상원 12건: 무소속 Dan Osborn(I)을 민주당('D') 슬롯에 매핑하여 DB 민주당 공천자(Cindy Burbank)와 정당·후보 매핑 충돌
   - 필드 기간(dateDisplay) 결측 및 경선 이전 구형 조사 배제 (P1): 18건 (MN 상원 3건, MN 주지사 2건, KS 상원 1건, AL 주지사 1건, NE 주지사 2건, VA 상원 6월 경선 이전 STALE 조사 2건, 기타 2025년 조사 7건)
   - 정책 근거 배제 (P1/P3): 2건 (MI Mike Rogers 10월 디트로이트 경제클럽 연설 — 원전·천연가스 일반론 반복으로 신규 축·구속력 변화 없음 1건, GA Rick Jackson 캠페인 논평 — 1차 원문 미확인 전언 1건)
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-10-18"

def rid(st, off):
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    return r[0] if r else None

# ================================================================ 1. 출처 등록 (206..230)
SOURCES = [
 (206, 8, "Pollsmax", "Texas Senate & Governor Mid-October 2026 Polling Average (54건/48건)",
  "https://www.pollsmax.com/senate/texas/", "2026-10-14", NOW, 0),
 (207, 8, "ActiVote", "ActiVote October 2026 Texas Senate & Governor Surveys (400 LV)",
  "https://www.activote.net/2026-october-texas-statewide-polls/", "2026-10-14", NOW, 1),
 (208, 8, "Siena College / ReconMR", "Siena College / ReconMR Texas Statewide Poll Oct 5-8, 2026 (617 LV)",
  "https://scri.siena.edu/2026/10/08/texas-senate-and-governor-poll-october-2026/", "2026-10-08", NOW, 1),
 (209, 8, "University of Texas / Texas Politics Project", "UT / Texas Politics Project October 2026 Poll (861 LV)",
  "https://texaspolitics.utexas.edu/blog/october-2026-ut-texas-politics-project-poll", "2026-10-05", NOW, 1),
 (210, 8, "Pollsmax", "Iowa Senate & Governor Mid-October 2026 Polling Average (30건/18건) & YouGov Poll",
  "https://www.pollsmax.com/senate/iowa/", "2026-10-12", NOW, 0),
 (211, 8, "Pollsmax", "Georgia Governor Mid-October 2026 Polling Average (14건) & InsiderAdvantage Poll",
  "https://www.pollsmax.com/governor/georgia/", "2026-10-13", NOW, 0),
 (212, 8, "Pollsmax", "North Carolina Senate Mid-October 2026 Polling Average (43건) & SurveyUSA / Change Research",
  "https://www.pollsmax.com/senate/north-carolina/", "2026-10-11", NOW, 0),
 (213, 8, "Pollsmax", "Florida Senate & Governor Mid-October 2026 Polling Average (16건/33건)",
  "https://www.pollsmax.com/governor/florida/", "2026-10-11", NOW, 0),
 (214, 8, "Stetson University", "Stetson University Center for Public Opinion Research: Florida Poll Oct 6-9, 2026 (716 LV)",
  "https://www.stetson.edu/other/cpor/polls/2026-october-florida-poll.php", "2026-10-09", NOW, 1),
 (215, 8, "Pollsmax", "New York Governor Mid-October 2026 Polling Average (30건) & Pollfinity / Beacon Surveys",
  "https://www.pollsmax.com/governor/new-york/", "2026-10-12", NOW, 0),
 (216, 8, "Pollsmax", "Arizona Governor Mid-October 2026 Polling Average (26건) & HighGround / Wick Insights",
  "https://www.pollsmax.com/governor/arizona/", "2026-10-08", NOW, 0),
 (217, 8, "Pollsmax", "Minnesota Governor & Senate October 2026 Polling Average (10건/15건) & Star Tribune / Morning Consult",
  "https://www.pollsmax.com/governor/minnesota/", "2026-10-07", NOW, 0),
 (218, 8, "Minnesota Star Tribune / KARE 11", "Minnesota Poll: Klobuchar vs. Demuth & Flanagan vs. Tafoya October 2026 Surveys",
  "https://www.startribune.com/minnesota-poll-october-2026-governor-senate-klobuchar-demuth-flanagan-tafoya/", "2026-10-07", NOW, 1),
 (219, 8, "Pollsmax", "Kansas Governor & Senate October 2026 Polling Average (7건/13건) & YouGov / NYT-Siena / InsiderAdvantage",
  "https://www.pollsmax.com/senate/kansas/", "2026-10-10", NOW, 0),
 (220, 8, "Pollsmax", "New Mexico Governor & Senate October 2026 Polling Average (5건/3건) & Research & Polling Inc.",
  "https://www.pollsmax.com/governor/new-mexico/", "2026-10-09", NOW, 0),
 (221, 8, "Pollsmax", "New Hampshire Governor October 2026 Polling Average (11건) & UNH / Saint Anselm / YouGov",
  "https://www.pollsmax.com/governor/new-hampshire/", "2026-10-05", NOW, 0),
 (222, 8, "Pollsmax", "Maine Governor October 2026 Polling Average (15건) & Suffolk / WaPo / Marist Surveys",
  "https://www.pollsmax.com/governor/maine/", "2026-10-11", NOW, 0),
 (223, 8, "Pollsmax", "Alabama Governor Polling Average (3건) & RMG Research / yes. every kid. Surveys",
  "https://www.pollsmax.com/governor/alabama/", "2026-09-25", NOW, 0),
 (224, 8, "Pollsmax", "California Governor Polling Average (9건) & UC Berkeley IGS / PPIC / SurveyUSA",
  "https://www.pollsmax.com/governor/california/", "2026-09-20", NOW, 0),
 (225, 8, "Pollsmax", "Nebraska Governor October 2026 Polling Average (11건) & YouGov / National Public Affairs",
  "https://www.pollsmax.com/governor/nebraska/", "2026-10-05", NOW, 0),
 (226, 8, "Pollsmax", "South Carolina Governor & Senate October 2026 Polling Average (3건/9건)",
  "https://www.pollsmax.com/senate/south-carolina/", "2026-10-08", NOW, 0),
 (227, 9, "Abdul El-Sayed for Senate / The Washington Post", "Abdul El-Sayed Releases 'AI Under Control' Policy Plan Calling for Federal Data Center Moratorium, 100% Clean Power, and End to Tax Subsidies",
  "https://www.washingtonpost.com/technology/2026/10/12/abdul-el-sayed-ai-data-center-moratorium-plan/", "2026-10-12", NOW, 1),
 (228, 9, "WPMT FOX43 / Stacy Garrity for Governor", "Stacy Garrity Unveils Farmland & Rural Water Protection Plan Restricting Hyperscale Data Centers to Industrial Brownfields",
  "https://www.fox43.com/article/news/politics/stacy-garrity-pennsylvania-data-center-farmland-water-policy-plan/521-oct2026", "2026-10-14", NOW, 1),
 (229, 9, "WVXU / Amy Acton for Governor", "Amy Acton 'My Promise for Ohio' Platform Pledges Ban on Secret Data Center NDAs and Ends Unconditional State Tax Abatements",
  "https://www.wvxu.org/politics/2026-10-11/amy-acton-ohio-data-center-nda-ban-tax-abatement-reform", "2026-10-11", NOW, 1),
]

for s in SOURCES:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", s)

# ================================================================ 2. 후보 명단 동기화 (6명)
# 1) MN Governor: Kendall Qualls (candidate_id=95) -> Withdrawn 전환 (8/11 공화 경선에서 Lisa Demuth 승리)
cur.execute("""UPDATE candidate SET current_status='Withdrawn', source_id=218, last_updated=?
    WHERE candidate_id=95""", (NOW,))

# 2) 신규 등재 후보 6명 (MN Demuth/Flanagan/Tafoya, KS Holscher/Masterson/Hamilton)
CAND_UPDATES = [
    # (pol_id, name, party, state, office, race_id, cand_id, cur_pos, status, src_id)
    (135, "Lisa Demuth", "R", "MN", "Governor", rid("MN","Governor"), 135, "Speaker of the Minnesota House of Representatives", "Nominee", 218),
    (136, "Peggy Flanagan", "D", "MN", "U.S. Senate", rid("MN","U.S. Senate"), 136, "Lieutenant Governor of Minnesota", "Nominee", 218),
    (137, "Michele Tafoya", "R", "MN", "U.S. Senate", rid("MN","U.S. Senate"), 137, "Broadcast Journalist & Political Commentator", "Nominee", 218),
    (138, "Cindy Holscher", "D", "KS", "Governor", rid("KS","Governor"), 138, "Kansas State Senator", "Nominee", 219),
    (139, "Ty Masterson", "R", "KS", "Governor", rid("KS","Governor"), 139, "President of the Kansas Senate", "Nominee", 219),
    (140, "Adam Hamilton", "D", "KS", "U.S. Senate", rid("KS","U.S. Senate"), 140, "Community Leader & Democratic Nominee", "Nominee", 219),
]

for pol_id, name, party, st, off, r_id, cand_id, cur_pos, status, src_id in CAND_UPDATES:
    cur.execute("""INSERT OR REPLACE INTO politician(politician_id,full_name,party,state_code,
        current_office,last_updated) VALUES (?,?,?,?,?,?)""",
        (pol_id, name, party, st, off, NOW))
    cur.execute("""INSERT OR REPLACE INTO candidate(candidate_id,race_id,politician_id,candidate_name,
        candidate_party,is_incumbent,current_position,current_status,status_code,source_id,last_updated)
        VALUES (?,?,?,?,?,0,?,?,'OK',?,?)""",
        (cand_id, r_id, pol_id, name, party, cur_pos, status, src_id, NOW))

# ================================================================ 3. 정책 입장 및 레버리지 갱신 (3명)
ev_base = cur.execute("SELECT COALESCE(MAX(evidence_id),0) FROM position_evidence").fetchone()[0]

# (1) Abdul El-Sayed (MI U.S. Senate, D, pos_id 15): 10/12 'AI Under Control' 공식 정책안 발표 (5대 축 완비 & 레버리지 상향)
ev_elsayed = ev_base + 1
cur.execute("""INSERT OR REPLACE INTO position_evidence(evidence_id,position_id,evidence_type,summary,
    evidence_date,source_id,binding_code,scope_code,direction) VALUES
    (?,15,'Campaign promise',
     'AI Under Control 공식 정책안 발표: 지역 전력망·수자원·전기요금 보호 기준 발효 전까지 하이퍼스케일 AI 데이터센터 연방 인허가 모라토리엄, 100% 신규 재생에너지 자체 조달 의무화 및 연방·주 세제특혜 전면 폐지 공약',
     '2026-10-12',227,'POLICY_PLAN','NEW_TOTAL','RESTRICTIVE')""", (ev_elsayed,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (15,'POWER',-50,?,'OK')""", (ev_elsayed,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (15,'TAX',-70,?,'OK')""", (ev_elsayed,))
cur.execute("""UPDATE politician_dc_position SET
    policy_statement='AI Under Control 공식 정책안을 통해 하이퍼스케일 데이터센터 연방 모라토리엄, 100% 청정에너지 자체 조달 의무화, 오대호 수자원 보호 및 빅테크 세제특혜 전면 폐지를 공약.',
    last_updated=? WHERE position_id=15""", (NOW,))

# (2) Stacy Garrity (PA Governor, R, pos_id 6): 10/14 우량 농지·지하수 보호를 위한 브라운필드 입지 제한 정책안 발표
ev_garrity = ev_base + 2
cur.execute("""INSERT OR REPLACE INTO position_evidence(evidence_id,position_id,evidence_type,summary,
    evidence_date,source_id,binding_code,scope_code,direction) VALUES
    (?,6,'Campaign promise',
     '펜실베이니아 우량 농지 잠식 및 농촌 지하수 고갈 방지를 위해 대규모 데이터센터 입지를 기존 산업단지·폐광지(브라운필드)로 제한하고 상수원 수질·수량 영향평가를 의무화하는 정책안 발표',
     '2026-10-14',228,'POLICY_PLAN','SITING_BAN','RESTRICTIVE')""", (ev_garrity,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (6,'WATER',-45,?,'OK')""", (ev_garrity,))
cur.execute("""UPDATE politician_dc_position SET confidence_level='High',
    policy_statement='농촌 주민 동의 없는 신규 승인 중단 공약에 이어 우량 농지·지하수 보호를 위해 데이터센터 입지를 산업단지·브라운필드로 제한하는 정책안 발표.',
    last_updated=? WHERE position_id=6""", (NOW,))

# (3) Amy Acton (OH Governor, D, pos_id 7): 10/11 'My Promise for Ohio' NDA 금지 및 조건부 세제특혜 배제 정책안 발표
ev_acton = ev_base + 3
cur.execute("""INSERT OR REPLACE INTO position_evidence(evidence_id,position_id,evidence_type,summary,
    evidence_date,source_id,binding_code,scope_code,direction) VALUES
    (?,7,'Campaign promise',
     'My Promise for Ohio 정책안에서 하이퍼스케일 데이터센터 관련 지자체 비밀유지협약(NDA)을 전면 금지하고, 지역사회 투명성·노조 고용·가계 전기요금 인상 방지 요건 미충족 시 주 판매세 및 재산세 감면을 전면 배제하겠다고 공약',
     '2026-10-11',229,'POLICY_PLAN','NEW_CONDITIONAL','RESTRICTIVE')""", (ev_acton,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (7,'TAX',-60,?,'OK')""", (ev_acton,))
cur.execute("""UPDATE politician_dc_position SET confidence_level='High',
    policy_statement='My Promise for Ohio 정책안을 통해 데이터센터 비밀유지협약(NDA) 금지, 무분별한 세제감면 중단 및 가계 전기요금·수자원 보호 조건부 인허가 공약.',
    last_updated=? WHERE position_id=7""", (NOW,))

# ================================================================ 4. 여론조사 적재 (23개 레이스, 118건)
NEW_POLLS = [
 # ---- 1. IA U.S. Senate (Turek vs Hinson — 평균 D+0.2 리드 재역전!)
 ("IA","U.S. Senate","YouGov","2026-10-09","2026-10-12",2245,"LV",                     1.0, 0, 210),
 ("IA","U.S. Senate","InsiderAdvantage (R)","2026-09-21","2026-09-23",1200,"LV",       1.0, 0, 210),
 ("IA","U.S. Senate","Pollsmax 평균 (30건)","2026-10-12","2026-10-12",None,None,        0.2, 1, 210),

 # ---- 2. IA Governor (Sand vs Lahn — 평균 D+6.5 우세 유지)
 ("IA","Governor","YouGov","2026-10-09","2026-10-12",2245,"LV",                        6.0, 0, 210),
 ("IA","Governor","Pollsmax 평균 (18건)","2026-10-12","2026-10-12",None,None,           6.5, 1, 210),

 # ---- 3. TX U.S. Senate (Talarico vs Paxton — 평균 D+2.8 우세 유지)
 ("TX","U.S. Senate","ActiVote","2026-10-11","2026-10-14",400,"LV",                    4.0, 0, 207),
 ("TX","U.S. Senate","Quantus Insights (R)","2026-10-08","2026-10-11",854,"LV",        0.0, 0, 206),
 ("TX","U.S. Senate","Siena College / ReconMR","2026-10-05","2026-10-08",617,"LV",     4.0, 0, 208),
 ("TX","U.S. Senate","University of Texas / Texas Politics Project","2026-10-02","2026-10-05",861,"LV",3.0,0,209),
 ("TX","U.S. Senate","Pollsmax 평균 (54건)","2026-10-14","2026-10-14",None,None,        2.8, 1, 206),

 # ---- 4. TX Governor (Hinojosa vs Abbott — 평균 R+3.4로 격차 축소)
 ("TX","Governor","ActiVote","2026-10-11","2026-10-14",400,"LV",                      -2.0, 0, 207),
 ("TX","Governor","GBAO (D)","2026-10-05","2026-10-08",800,"LV",                       2.0, 0, 206),
 ("TX","Governor","Siena College / ReconMR","2026-10-05","2026-10-08",617,"LV",       -1.0, 0, 208),
 ("TX","Governor","Pollsmax 평균 (48건)","2026-10-14","2026-10-14",None,None,          -3.4, 1, 206),

 # ---- 5. GA Governor (Bottoms vs Jackson — 평균 R+0.6 초접전)
 ("GA","Governor","InsiderAdvantage (R)","2026-10-11","2026-10-13",800,"LV",          -2.0, 0, 211),
 ("GA","Governor","Pollsmax 평균 (14건)","2026-10-13","2026-10-13",None,None,          -0.6, 1, 211),

 # ---- 6. NC U.S. Senate (Cooper vs Whatley — 평균 D+8.6 우세 확대)
 ("NC","U.S. Senate","SurveyUSA (D)","2026-10-08","2026-10-11",643,"LV",              14.0, 0, 212),
 ("NC","U.S. Senate","Change Research (D)","2026-10-04","2026-10-07",829,"LV",        10.0, 0, 212),
 ("NC","U.S. Senate","Pollsmax 평균 (43건)","2026-10-11","2026-10-11",None,None,        8.6, 1, 212),

 # ---- 7. FL U.S. Senate (Nixon vs Moody — 평균 R+8.0)
 ("FL","U.S. Senate","MDW Communications (D)","2026-10-08","2026-10-10",2351,"LV",    -6.0, 0, 213),
 ("FL","U.S. Senate","Stetson University","2026-10-06","2026-10-09",716,"LV",        -11.0, 0, 214),
 ("FL","U.S. Senate","Pollsmax 평균 (16건)","2026-10-10","2026-10-10",None,None,       -8.0, 1, 213),

 # ---- 8. FL Governor (Jolly vs Donalds — 평균 R+4.7 / Change Research 동률)
 ("FL","Governor","Fabrizio, Lee & Associates (R)","2026-10-08","2026-10-11",1200,"LV",-6.0,0, 213),
 ("FL","Governor","Change Research (D)","2026-10-07","2026-10-10",920,"LV",            0.0, 0, 213),
 ("FL","Governor","MDW Communications (D)","2026-10-08","2026-10-10",2351,"LV",       -2.0, 0, 213),
 ("FL","Governor","Stetson University","2026-10-06","2026-10-09",716,"LV",           -11.0, 0, 214),
 ("FL","Governor","Pollsmax 평균 (33건)","2026-10-11","2026-10-11",None,None,          -4.7, 1, 213),

 # ---- 9. NY Governor (Hochul vs Blakeman — 평균 D+12.0)
 ("NY","Governor","Pollfinity Research","2026-10-09","2026-10-12",499,"RV",            3.0, 0, 215),
 ("NY","Governor","Beacon Research (D)","2026-10-03","2026-10-06",820,"RV",           22.0, 0, 215),
 ("NY","Governor","Pollsmax 평균 (30건)","2026-10-12","2026-10-12",None,None,          12.0, 1, 215),

 # ---- 10. AZ Governor (Hobbs vs Biggs — 평균 D+7.3 우세 확대)
 ("AZ","Governor","HighGround, Inc.","2026-10-05","2026-10-08",400,"LV",              17.0, 0, 216),
 ("AZ","Governor","Wick Insights","2026-10-03","2026-10-06",1513,"LV",                 6.0, 0, 216),
 ("AZ","Governor","Pollsmax 평균 (26건)","2026-10-08","2026-10-08",None,None,           7.3, 1, 216),

 # ---- 11. MN Governor (Klobuchar vs Demuth — 사각지대 NO_POLLING 신규 해소, 평균 D+8.0)
 ("MN","Governor","Morning Consult","2026-10-04","2026-10-07",1000,"RV",               9.0, 0, 217),
 ("MN","Governor","KARE 11 / Minnesota Star Tribune","2026-10-04","2026-10-07",800,"LV",9.0,0, 218),
 ("MN","Governor","co/efficient (R)","2026-09-13","2026-09-15",833,"LV",               2.0, 0, 217),
 ("MN","Governor","SurveyUSA (D)","2026-09-11","2026-09-14",654,"LV",                  7.0, 0, 217),
 ("MN","Governor","TIPP Insights (R)","2026-08-30","2026-09-02",1201,"LV",             9.6, 0, 217),
 ("MN","Governor","KTSP / SurveyUSA (D)","2026-08-14","2026-08-17",661,"LV",          15.0, 0, 217),
 ("MN","Governor","Pollsmax 평균 (10건)","2026-10-07","2026-10-07",None,None,           8.0, 1, 217),

 # ---- 12. MN U.S. Senate (Flanagan vs Tafoya — 사각지대 NO_POLLING 신규 해소, 평균 D+4.3)
 ("MN","U.S. Senate","Morning Consult","2026-10-04","2026-10-07",1000,"RV",            4.0, 0, 217),
 ("MN","U.S. Senate","Rasmussen Reports (R)","2026-10-05","2026-10-07",856,"LV",       3.0, 0, 217),
 ("MN","U.S. Senate","Mason-Dixon Polling & Strategy","2026-10-04","2026-10-07",800,"LV",4.0,0,218),
 ("MN","U.S. Senate","GQR (D)","2026-10-01","2026-10-04",800,"LV",                     8.0, 0, 217),
 ("MN","U.S. Senate","Big Data Poll (R)","2026-09-28","2026-09-30",297,"LV",           2.2, 0, 217),
 ("MN","U.S. Senate","InsiderAdvantage (R)","2026-09-27","2026-09-29",1200,"LV",       1.0, 0, 217),
 ("MN","U.S. Senate","co/efficient (R)","2026-09-13","2026-09-15",833,"LV",            1.0, 0, 217),
 ("MN","U.S. Senate","SurveyUSA (D)","2026-09-11","2026-09-14",654,"LV",               0.0, 0, 217),
 ("MN","U.S. Senate","Quantus Insights (R)","2026-09-08","2026-09-10",720,"LV",        3.5, 0, 217),
 ("MN","U.S. Senate","TIPP Insights (R)","2026-08-30","2026-09-02",1201,"LV",          2.1, 0, 217),
 ("MN","U.S. Senate","Pollsmax 평균 (15건)","2026-10-07","2026-10-07",None,None,        4.3, 1, 217),

 # ---- 13. KS Governor (Holscher vs Masterson — 사각지대 NO_POLLING 신규 해소, 평균 R+4.5)
 ("KS","Governor","YouGov","2026-10-01","2026-10-04",2255,"LV",                       -3.0, 0, 219),
 ("KS","Governor","New York Times / Siena College","2026-09-26","2026-09-30",605,"LV",-5.0, 0, 219),
 ("KS","Governor","Wedgewood Polls","2026-09-21","2026-09-24",500,"LV",               -4.0, 0, 219),
 ("KS","Governor","Global Strategy Group (D)","2026-09-13","2026-09-16",800,"LV",      3.0, 0, 219),
 ("KS","Governor","Emerson College","2026-09-15","2026-09-16",750,"LV",               -7.0, 0, 219),
 ("KS","Governor","co/efficient (R)","2026-09-08","2026-09-10",915,"LV",              -8.0, 0, 219),
 ("KS","Governor","Global Strategy Group (D)","2026-08-13","2026-08-16",600,"LV",      1.0, 0, 219),
 ("KS","Governor","Pollsmax 평균 (7건)","2026-10-04","2026-10-04",None,None,           -4.5, 1, 219),

 # ---- 14. KS U.S. Senate (Hamilton vs Marshall — 사각지대 NO_POLLING 신규 해소, 평균 D+0.8 초접전!)
 ("KS","U.S. Senate","InsiderAdvantage (R)","2026-10-08","2026-10-10",1200,"LV",       1.0, 0, 219),
 ("KS","U.S. Senate","YouGov","2026-10-01","2026-10-04",2255,"LV",                     3.0, 0, 219),
 ("KS","U.S. Senate","GBAO (D)","2026-10-01","2026-10-04",600,"LV",                    5.0, 0, 219),
 ("KS","U.S. Senate","Trafalgar Group (R)","2026-09-29","2026-10-01",1095,"LV",        4.0, 0, 219),
 ("KS","U.S. Senate","New York Times / Siena College","2026-09-26","2026-09-30",504,"LV",-1.0,0,219),
 ("KS","U.S. Senate","Wedgewood Polls","2026-09-21","2026-09-24",500,"LV",             2.0, 0, 219),
 ("KS","U.S. Senate","Emerson College","2026-09-15","2026-09-16",750,"LV",             1.5, 0, 219),
 ("KS","U.S. Senate","Global Strategy Group (D)","2026-09-13","2026-09-16",800,"LV",   4.0, 0, 219),
 ("KS","U.S. Senate","co/efficient (R)","2026-09-08","2026-09-10",915,"LV",           -5.0, 0, 219),
 ("KS","U.S. Senate","Pollsmax 평균 (13건)","2026-10-10","2026-10-10",None,None,        0.8, 1, 219),

 # ---- 15. NM Governor (Haaland vs Hull — 사각지대 NO_POLLING 신규 해소, 평균 D+7.1)
 ("NM","Governor","Research & Polling Inc.","2026-10-05","2026-10-09",1125,"LV",       7.0, 0, 220),
 ("NM","Governor","SurveyUSA (D)","2026-09-26","2026-09-30",567,"LV",                  6.0, 0, 220),
 ("NM","Governor","Research & Polling Inc.","2026-08-24","2026-08-28",600,"LV",        6.0, 0, 220),
 ("NM","Governor","BSP Research","2026-08-03","2026-08-07",800,"RV",                  17.0, 0, 220),
 ("NM","Governor","Pollsmax 평균 (5건)","2026-10-09","2026-10-09",None,None,            7.1, 1, 220),

 # ---- 16. NM U.S. Senate (Lujan vs Marker — 사각지대 NO_POLLING 신규 해소, 평균 D+17.2)
 ("NM","U.S. Senate","Research & Polling Inc.","2026-10-05","2026-10-09",1125,"LV",   16.0, 0, 220),
 ("NM","U.S. Senate","SurveyUSA (D)","2026-09-26","2026-09-30",567,"LV",              18.3, 0, 220),
 ("NM","U.S. Senate","Research & Polling Inc.","2026-08-24","2026-08-28",516,"LV",    15.0, 0, 220),
 ("NM","U.S. Senate","Pollsmax 평균 (3건)","2026-10-09","2026-10-09",None,None,        17.2, 1, 220),

 # ---- 17. NH Governor (Warmington vs Ayotte — 사각지대 NO_POLLING 신규 해소, 평균 R+9.8)
 ("NH","Governor","YouGov","2026-10-02","2026-10-05",1520,"LV",                       -9.0, 0, 221),
 ("NH","Governor","Saint Anselm College","2026-09-27","2026-09-29",1042,"LV",         -7.0, 0, 221),
 ("NH","Governor","New York Times / Siena College","2026-09-18","2026-09-22",619,"LV",-11.0,0, 221),
 ("NH","Governor","University of New Hampshire","2026-09-17","2026-09-21",1418,"LV",  -4.0, 0, 221),
 ("NH","Governor","co/efficient (R)","2026-09-09","2026-09-11",958,"LV",             -21.0, 0, 221),
 ("NH","Governor","University of New Hampshire","2026-08-20","2026-08-24",2143,"LV", -10.0, 0, 221),
 ("NH","Governor","Saint Anselm College","2026-08-16","2026-08-18",1411,"LV",        -11.0, 0, 221),
 ("NH","Governor","Pollsmax 평균 (11건)","2026-10-05","2026-10-05",None,None,          -9.8, 1, 221),

 # ---- 18. ME Governor (Pingree vs Charles — 사각지대 NO_POLLING 신규 해소, 평균 D+11.3)
 ("ME","Governor","Suffolk University","2026-10-08","2026-10-11",500,"LV",            11.0, 0, 222),
 ("ME","Governor","The Washington Post / SSPG","2026-10-01","2026-10-05",800,"LV",    13.0, 0, 222),
 ("ME","Governor","Marist University","2026-10-01","2026-10-04",1505,"RV",            12.0, 0, 222),
 ("ME","Governor","CBS News / YouGov","2026-09-28","2026-10-01",1136,"LV",            12.0, 0, 222),
 ("ME","Governor","co/efficient (R)","2026-09-28","2026-09-30",1240,"LV",              9.0, 0, 222),
 ("ME","Governor","Impact Research (D) / Fabrizio, Lee & Associates (R)","2026-09-19","2026-09-22",982,"LV",13.0,0,222),
 ("ME","Governor","New York Times / Siena College","2026-09-18","2026-09-22",619,"LV",13.0, 0, 222),
 ("ME","Governor","University of New Hampshire","2026-09-17","2026-09-21",1301,"LV",  14.0, 0, 222),
 ("ME","Governor","Pollsmax 평균 (15건)","2026-10-11","2026-10-11",None,None,          11.3, 1, 222),

 # ---- 19. AL Governor (Jones vs Tuberville — 사각지대 NO_POLLING 신규 해소, 평균 R+18.0)
 ("AL","Governor","RMG Research","2026-09-22","2026-09-25",800,"RV",                 -13.0, 0, 223),
 ("AL","Governor","yes. every kid. (D)","2026-07-08","2026-07-11",601,"LV",           -8.0, 0, 223),
 ("AL","Governor","Pollsmax 평균 (3건)","2026-09-25","2026-09-25",None,None,          -18.0, 1, 223),

 # ---- 20. CA Governor (Becerra vs Hilton — 사각지대 NO_POLLING 신규 해소, 평균 D+19.4)
 ("CA","Governor","SurveyUSA (D)","2026-09-17","2026-09-20",742,"LV",                 21.9, 0, 224),
 ("CA","Governor","University of California, Berkeley","2026-09-15","2026-09-20",4512,"LV",25.0,0,224),
 ("CA","Governor","TrueDot","2026-09-13","2026-09-16",1983,"LV",                      18.0, 0, 224),
 ("CA","Governor","Public Policy Institute of California","2026-09-04","2026-09-10",1103,"LV",22.0,0,224),
 ("CA","Governor","David J Wolfson","2026-08-13","2026-08-16",912,"RV",                9.0, 0, 224),
 ("CA","Governor","University of California, Berkeley","2026-08-04","2026-08-09",2310,"LV",18.0,0,224),
 ("CA","Governor","Pollsmax 평균 (9건)","2026-09-20","2026-09-20",None,None,           19.4, 1, 224),

 # ---- 21. NE Governor (Walz vs Pillen — 사각지대 NO_POLLING 신규 해소, 평균 R+3.5 접전)
 ("NE","Governor","National Public Affairs (R)","2026-10-02","2026-10-05",800,"LV",   -4.0, 0, 225),
 ("NE","Governor","YouGov","2026-09-30","2026-10-03",1809,"LV",                       -1.0, 0, 225),
 ("NE","Governor","co/efficient (R)","2026-09-28","2026-09-30",1136,"LV",             -5.0, 0, 225),
 ("NE","Governor","Wedgewood Polls","2026-09-13","2026-09-16",500,"LV",              -17.0, 0, 225),
 ("NE","Governor","Lake Research Partners (D)","2026-09-10","2026-09-14",900,"LV",     0.0, 0, 225),
 ("NE","Governor","SurveyUSA (D)","2026-09-08","2026-09-13",503,"LV",                 -7.7, 0, 225),
 ("NE","Governor","Pollsmax 평균 (11건)","2026-10-05","2026-10-05",None,None,          -3.5, 1, 225),

 # ---- 22. SC Governor (Johnson vs Wilson — 사각지대 NO_POLLING 신규 해소, 평균 R+9.2)
 ("SC","Governor","Resonance Media","2026-09-30","2026-10-03",638,"RV",              -10.0, 0, 226),
 ("SC","Governor","Hart Research (D)","2026-08-12","2026-08-15",600,"LV",             -8.0, 0, 226),
 ("SC","Governor","Public Policy Polling (D)","2026-07-16","2026-07-17",577,"LV",     -8.0, 0, 226),
 ("SC","Governor","Pollsmax 평균 (3건)","2026-10-03","2026-10-03",None,None,           -9.2, 1, 226),

 # ---- 23. SC U.S. Senate (Andrews vs Graham — 사각지대 NO_POLLING 신규 해소, 평균 R+2.2 접전!)
 ("SC","U.S. Senate","Rasmussen Reports (R)","2026-10-06","2026-10-08",837,"LV",      -4.0, 0, 226),
 ("SC","U.S. Senate","InsiderAdvantage (R)","2026-09-27","2026-09-29",1200,"LV",      -1.0, 0, 226),
 ("SC","U.S. Senate","Trafalgar Group (R)","2026-09-23","2026-09-25",1087,"LV",       -1.0, 0, 226),
 ("SC","U.S. Senate","Pollsmax 평균 (9건)","2026-10-08","2026-10-08",None,None,        -2.2, 1, 226),
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

# ================================================================ 5. v_poll_coverage 10/18 기준 재정의
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
            ELSE CAST(julianday('2026-10-18') - julianday(l.last_poll_date) AS INTEGER)
       END AS poll_age_days,
       CASE
         WHEN l.poll_count = 0                       THEN 'NO_POLLING'
         WHEN julianday('2026-10-18') - julianday(l.last_poll_date) > 90 THEN 'STALE'
         WHEN julianday('2026-10-18') - julianday(l.last_poll_date) > 30 THEN 'AGING'
         ELSE 'CURRENT'
       END AS coverage_status
FROM latest l
LEFT JOIN comp c ON c.race_id = l.race_id
LEFT JOIN marg m ON m.race_id = l.race_id;
""")

# ================================================================ 6. change_log 기록 (15건)
cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
CHANGES = [
 ("NEW_CANDIDATE","MN","MN 주지사 Lisa Demuth(공화, 하원의장) 8/11 경선 승리 공식 후보 등재 및 Kendall Qualls(Withdrawn) 전환 / MN 연방상원 Peggy Flanagan(민주)·Michele Tafoya(공화) 본선 후보 등재",
  "MN Gov: Klobuchar vs Qualls / MN Sen: 미등재","MN Gov: Klobuchar(D) vs Demuth(R) / MN Sen: Flanagan(D) vs Tafoya(R)",NOW,218),
 ("NEW_CANDIDATE","KS","KS 주지사 Cindy Holscher(민주)·Ty Masterson(공화) 및 KS 연방상원 Adam Hamilton(민주) 8/4 경선 승리 공식 후보 등재",
  "KS Gov: 미등재 / KS Sen: Marshall 단독","KS Gov: Holscher(D) vs Masterson(R) / KS Sen: Hamilton(D) vs Marshall(R)",NOW,219),
 ("NEW_LEGISLATION","MI","Abdul El-Sayed 'AI Under Control' 공식 정책안 발표(10/12) — POWER(-50)·TAX(-70) 보강으로 5대 축 완비 및 레버리지 22.0→24.8 상향",
  "축 3개 (leverage: 22.0, support: -75.4)","축 5개 완비 (leverage: 24.8, POLICY_PLAN × NEW_TOTAL)",NOW,227),
 ("WATER_REGULATION","PA","Stacy Garrity 우량 농지·지하수 보호를 위한 데이터센터 산업단지·브라운필드 입지 제한 정책안 발표(10/14) — WATER(-45) 4번째 축 보강 및 신뢰도 High 상향",
  "축 3개 (support: -36.8, Medium)","축 4개 (WATER -45 추가, High)",NOW,228),
 ("TAX_INCENTIVE_CHANGE","OH","Amy Acton 'My Promise for Ohio' 데이터센터 비밀유지협약(NDA) 금지 및 조건부 세제감면 배제 정책안 발표(10/11) — TAX(-60) 4번째 축 보강 및 신뢰도 High 상향",
  "축 3개 (support: -63.5, Medium)","축 4개 (TAX -60 추가, High)",NOW,229),
 ("POLLING_CHANGE","IA","아이오와 연방상원 Turek(민주) D+0.2 리드 재역전! (YouGov 10/12 D+1.0 반영, Pollsmax 평균 30건 — 직전 Hinson R+0.1에서 재역전)",
  "Hinson R+0.1 (평균 28건)","Turek D+0.2 (평균 30건, 리드 재역전)",NOW,210),
 ("POLLING_CHANGE","TX","텍사스 상원(Talarico D+2.8)·주지사(Abbott R+3.4) 10월 중순 ActiVote·Siena·GBAO·UT 조사 9건 반영 — 주지사 격차 축소(R+4.4→R+3.4)",
  "상원 D+2.7 / 주지사 R+4.4","상원 D+2.8 (54건) / 주지사 R+3.4 (48건)",NOW,206),
 ("POLLING_CHANGE","NC","노스캐롤라이나 연방상원 SurveyUSA(D+14)·Change Research(D+10) 반영 — Cooper D+8.6 우세 확대(Pollsmax 평균 43건)",
  "Cooper D+8.4 (41건)","Cooper D+8.6 (43건)",NOW,212),
 ("POLLING_CHANGE","GA","조지아 주지사 InsiderAdvantage(10/13, Jackson R+2.0) 반영 — Jackson R+0.6 초접전 리드 유지(Pollsmax 평균 14건)",
  "Jackson R+0.2 (13건)","Jackson R+0.6 (14건)",NOW,211),
 ("POLLING_CHANGE","FL","플로리다 상원(Moody R+8.0)·주지사(Donalds R+4.7, Change Research 동률) 10월 중순 조사 8건 추가 적재",
  "상원 R+7.0 / 주지사 R+4.7 (29건)","상원 R+8.0 (16건) / 주지사 R+4.7 (33건)",NOW,213),
 ("POLLING_CHANGE","MN","미네소타 주지사(Klobuchar D+8.0)·연방상원(Flanagan D+4.3) 18건 적재 — MISO 중서부 사각지대(NO_POLLING) 2곳 신규 해소",
  "NO_POLLING","주지사 Klobuchar D+8.0 / 상원 Flanagan D+4.3 (CURRENT)",NOW,217),
 ("POLLING_CHANGE","KS","캔자스 연방상원(Hamilton D+0.8 초접전!)·주지사(Masterson R+4.5) 18건 적재 — SPP 사각지대(NO_POLLING) 2곳 신규 해소",
  "NO_POLLING","상원 Hamilton D+0.8 (초접전 우세) / 주지사 Masterson R+4.5",NOW,219),
 ("POLLING_CHANGE","NM","뉴멕시코 주지사(Haaland D+7.1)·연방상원(Lujan D+17.2) 9건 적재 — 서남부 사각지대(NO_POLLING) 2곳 신규 해소",
  "NO_POLLING","주지사 Haaland D+7.1 / 상원 Lujan D+17.2 (CURRENT)",NOW,220),
 ("POLLING_CHANGE","ME","메인 주지사(Pingree D+11.3, 9건)·뉴햄프셔 주지사(Ayotte R+9.8, 8건) 적재 — ISO-NE 뉴잉글랜드 사각지대(NO_POLLING) 2곳 신규 해소",
  "NO_POLLING","ME 주지사 Pingree D+11.3 / NH 주지사 Ayotte R+9.8 (CURRENT)",NOW,222),
 ("POLLING_CHANGE","SC","사우스캐롤라이나 상원(Graham R+2.2 접전)·주지사(Wilson R+9.2) 및 CA·NE·AL 주지사 총 25건 적재 — 사각지대(NO_POLLING) 5곳 신규 해소",
  "NO_POLLING","SC 상원 R+2.2·주지사 R+9.2 / CA D+19.4 / NE R+3.5 / AL R+18.0",NOW,226),
]

for et, st, note, ov, nv, when, sid in CHANGES:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,target_pk,
        field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'election_race',?,'poll/position/candidate',?,?,?,?,?)""",
        (cid, et, st, st, ov, nv, when, sid, note))

con.commit()

print(f"✔ 2026-10-18 갱신 완료:")
print(f"  - 후보 명단 동기화: 6명 신규 등재 + 1명 사퇴 전환 (MN Demuth/Flanagan/Tafoya, KS Holscher/Masterson/Hamilton)")
print(f"  - 정책 입장·레버리지 갱신: 3명 (MI El-Sayed 5축 완비·레버리지 상향, PA Garrity 4축·High, OH Acton 4축·High)")
print(f"  - 신규 조사 적재: {len(NEW_POLLS)}건 (23개 레이스)")
print(f"  - 변경 이력 기록: {len(CHANGES)}건")

con.close()
