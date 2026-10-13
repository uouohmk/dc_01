#!/usr/bin/env python3
"""2026-10-13 정기 트래커 갱신 (Cycle: 2026-10-13)

1) 후보 명단 동기화 (Candidate Roster Synchronization — 5명)
   - FL 연방상원: Angie Nixon(D, Nominee) 8/18 민주 경선 승리 확정 반영 및 Alexander Vindman(D, Withdrawn) 분리 등재
   - TN 주지사: Marsha Blackburn(R, Nominee) 및 Jerri Green(D, Nominee) 8/6 경선 승리 공식 후보 등재
   - TN 연방상원: Marquita Bradshaw(D, Nominee) 8/6 민주 경선 승리 공식 후보 등재
   - VA 연방상원: Bert Mizusawa(R, Nominee) 8/4 공화 경선 승리 공식 후보 등재
2) 정책 입장 및 레버리지 갱신 (policy-update — 5명)
   - Greg Abbott (TX 주지사, R, pos_id 1): 9/21 TCEQ 데이터센터 환경·폐수·수리권 인허가 전면 중단 지시(EXEC_DIRECTIVE × NEW_TOTAL) 반영
     → GROWTH(-55→-70), WATER(-60→-75) 하향, 레버리지(63.7→85.0), 종합 지지도(-39.3→-45.3), 실효 영향(-25.1→-38.5)
   - Tina Kotek (OR 주지사, D, pos_id 14): 9/8 주 의사당 집회 전주 모라토리엄 공개 지지 및 주유지 데이터센터 인허가·임대 중단 지시 반영
     → GROWTH(-45→-75) 하향 및 WATER(-50) 4번째 축 신규 추가, 레버리지(60.0→85.0), 종합 지지도(-44.0→-55.3), 실효 영향(-26.4→-47.0)
   - Vivek Ramaswamy (OH 주지사, R, pos_id 8): 'Ohioans-First' 공식 정책안(인근 주민 재산세 전액 감면 및 지자체 세제특혜 중단) 반영
     → TAX(-60) 4번째 축 신규 추가, 레버리지(25.0→45.0), 종합 지지도(-58.5→-58.8), 실효 영향(-14.6→-26.5), 신뢰도 High 상향
   - Josh Shapiro (PA 주지사, D, pos_id 5): 행정명령 2026-05호(GRID 기준) 내 판매세 면제 및 DEP 수질·환경 인허가 조건부 연계 반영
     → TAX(-55), WATER(-45) 축 보강으로 5대 축 완비(3축→5축), 종합 지지도(-49.6→-50.3), 실효 영향(-35.3→-35.8)
   - Sherrod Brown (OH 연방상원, D, pos_id 10): 농촌 수자원 고갈 및 농지 잠식 비판 캠페인 반영
     → WATER(-55) 4번째 축 신규 추가, 종합 지지도(-57.3→-57.1), 신뢰도 High 상향
3) 여론조사 갱신 (29개 레이스, 129건 적재)
   - 사각지대(NO_POLLING) 7개 레이스 신규 해소: IL 상원 · IL 주지사 · MD 주지사 · AR 상원 · AR 주지사 · TN 주지사 · TN 상원
   - 노후화(AGING) 5개 레이스 CURRENT 복귀: WI 주지사(격전지) · NV 주지사 · AZ 주지사 · OR 주지사 · FL 주지사
   - 주요 리드 역전(Lead Change) 반영:
     * IA 연방상원: Hinson(R)이 Turek(D)에 R+0.1 재역전 (Pollsmax 평균 28건, 직전 Turek D+2.1)
     * GA 주지사: Jackson(R)이 Bottoms(D)에 R+0.2 역전 (Pollsmax 평균 13건, 직전 Bottoms D+2.8)
     * OR 주지사: 최신 단건 조사(GBAO D+4.0, DHM D+2.0)에서 Kotek(D) 역전 우세 (Pollsmax 평균은 Drazan R+0.4 초박빙)
4) 10/13 기준 여론조사 커버리지 뷰(v_poll_coverage) 재정의
5) 엄격한 거부 항목 분리 (총 96건: 여론조사 94건 + 정책 2건)
   - 2025년 구형 조사 배제: 73건 (P1 시기 부적합)
   - 필드 기간(dateDisplay) 결측 및 경선 이전 상반기 조사 배제: 19건 (P1 필드기간 결측·후보 확정 이전)
   - 표본크기(n) 결측 및 90일 초과(STALE) 경선 이전 조사 배제: 2건 (NV POS 표본크기 결측 1건, VA PSI 6월 경선 이전 STALE 조사 1건)
   - 정책 근거 배제: 2건 (NY Hochul 10월 원탁간담회 추가 구속력 없음 1건, VA 9월 후보 포럼 데이터센터 직접성 결여 1건)
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "2026-10-13"

def rid(st, off):
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    return r[0] if r else None

# ================================================================ 1. 출처 등록 (170..205)
SOURCES = [
 (170, 8, "Pollsmax", "Texas Senate & Governor October 2026 Polling Average (49건/43건)",
  "https://www.pollsmax.com/senate/texas/", "2026-10-08", NOW, 0),
 (171, 8, "New York Times / Siena College", "October 2026 Battleground Polls: TX, OH, IA, AK, NH",
  "https://www.nytimes.com/interactive/2026/10/01/us/elections/battleground-senate-governor-polls.html", "2026-10-01", NOW, 1),
 (172, 8, "Trafalgar Group", "October 2026 Statewide Polls: TX, MI, GA, NC, ME, AK, NH",
  "https://thetrafalgargroup.org/polls/2026-october-battleground-surveys/", "2026-10-10", NOW, 1),
 (173, 8, "YouGov", "CBS News / YouGov Early October 2026 Statewide Election Surveys",
  "https://today.yougov.com/politics/articles/2026-10-05-october-statewide-midterm-polls", "2026-10-05", NOW, 1),
 (174, 8, "Pollsmax", "Ohio Senate & Governor October 2026 Polling Average (32건/27건)",
  "https://www.pollsmax.com/senate/ohio/", "2026-10-06", NOW, 0),
 (175, 8, "SSRS", "SSRS October 2026 Ohio & Iowa Midterm Election Surveys",
  "https://ssrs.com/research/2026-october-ohio-iowa-election-poll/", "2026-10-05", NOW, 1),
 (176, 8, "Pollsmax", "Pennsylvania Governor October 2026 Polling Average (19건)",
  "https://www.pollsmax.com/governor/pennsylvania/", "2026-10-05", NOW, 0),
 (177, 8, "Quinnipiac University", "Quinnipiac Poll: Pennsylvania & New York Governor Races",
  "https://poll.qu.edu/poll-release?releaseid=3965", "2026-10-05", NOW, 1),
 (178, 8, "Pollsmax", "Michigan Senate & Governor October 2026 Polling Average (49건/40건)",
  "https://www.pollsmax.com/senate/michigan/", "2026-10-10", NOW, 0),
 (179, 8, "InsiderAdvantage", "InsiderAdvantage October 2026 Surveys: MI & AK Senate",
  "https://insideradvantage.com/2026/10/10/october-senate-polls-michigan-alaska/", "2026-10-10", NOW, 1),
 (180, 8, "Pollsmax", "Georgia Senate & Governor October 2026 Polling Average (19건/13건)",
  "https://www.pollsmax.com/senate/georgia/", "2026-10-09", NOW, 0),
 (181, 8, "Pollsmax", "North Carolina Senate October 2026 Polling Average (41건)",
  "https://www.pollsmax.com/senate/north-carolina/", "2026-10-10", NOW, 0),
 (182, 8, "East Carolina University", "ECU Center for Survey Research: NC Senate Poll (810 LV)",
  "https://surveyresearch-ecu.org/2026/10/03/cooper-leads-whatley-in-nc-senate-race/", "2026-10-03", NOW, 1),
 (183, 8, "Pollsmax", "New Hampshire Senate October 2026 Polling Average (26건)",
  "https://www.pollsmax.com/senate/new-hampshire/", "2026-10-05", NOW, 0),
 (184, 8, "Saint Anselm College", "Saint Anselm College Survey Center: NH Senate Poll (1,042 LV)",
  "https://www.anselm.edu/nh-institute-politics/polls/2026-09-29-nh-senate", "2026-09-29", NOW, 1),
 (185, 8, "Pollsmax", "Maine Senate October 2026 Polling Average (24건)",
  "https://www.pollsmax.com/senate/maine/", "2026-10-08", NOW, 0),
 (186, 8, "Washington Post / Schar School", "Washington Post-Schar School Maine Senate Poll (800 LV)",
  "https://www.washingtonpost.com/politics/2026/10/05/maine-senate-poll-jackson-collins/", "2026-10-05", NOW, 1),
 (187, 8, "Pollsmax", "Iowa Senate & Governor October 2026 Polling Average (28건/16건)",
  "https://www.pollsmax.com/senate/iowa/", "2026-10-06", NOW, 0),
 (188, 8, "Emerson College", "Emerson College Polling: October 2026 Iowa & New York Statewide Surveys",
  "https://emersoncollegepolling.com/october-2026-iowa-and-new-york-polls/", "2026-10-06", NOW, 1),
 (189, 8, "Pollsmax", "Alaska Senate October 2026 Polling Average (24건)",
  "https://www.pollsmax.com/senate/alaska/", "2026-10-10", NOW, 0),
 (190, 8, "Pollsmax", "Florida Senate & Governor October 2026 Polling Average (14건/29건)",
  "https://www.pollsmax.com/governor/florida/", "2026-10-07", NOW, 0),
 (191, 8, "St. Pete Polls", "Florida Statewide Senate & Governor Survey (836 LV)",
  "https://stpetepolls.org/files/StPetePolls_2026_Statewide_Oct7.pdf", "2026-10-07", NOW, 1),
 (192, 8, "Pollsmax", "Oregon Governor October 2026 Polling Average (7건)",
  "https://www.pollsmax.com/governor/oregon/", "2026-10-04", NOW, 0),
 (193, 8, "DHM Research", "Oregon Governor General Election October 2026 Survey (549 LV)",
  "https://dhmresearch.com/polls/2026-oregon-governor-october/", "2026-10-01", NOW, 1),
 (194, 8, "Pollsmax", "New York Governor October 2026 Polling Average (28건)",
  "https://www.pollsmax.com/governor/new-york/", "2026-10-05", NOW, 0),
 (195, 8, "Pollsmax", "Nevada Governor Polling Average (13건) & Noble Predictive Insights Survey",
  "https://www.pollsmax.com/governor/nevada/", "2026-09-26", NOW, 0),
 (196, 8, "Pollsmax", "Arizona Governor October 2026 Polling Average (24건)",
  "https://www.pollsmax.com/governor/arizona/", "2026-10-08", NOW, 0),
 (197, 8, "Marquette University", "Marquette Law School Poll: Wisconsin Statewide Survey Sept 16-23, 2026 (692 LV)",
  "https://law.marquette.edu/poll/2026/09/30/mlsp-wisconsin-september-2026/", "2026-09-30", NOW, 1),
 (198, 8, "Pollsmax", "Illinois Senate & Governor October 2026 Polling (PPP 569 LV)",
  "https://www.pollsmax.com/governor/illinois/", "2026-10-01", NOW, 0),
 (199, 8, "Pollsmax", "Maryland Governor Polling Average (3건) & UMD / UMBC Surveys",
  "https://www.pollsmax.com/governor/maryland/", "2026-09-27", NOW, 0),
 (200, 8, "Pollsmax", "Arkansas Senate & Governor Polling Average (5건/2건) & Hendrix / GrayHouse Surveys",
  "https://www.pollsmax.com/senate/arkansas/", "2026-10-04", NOW, 0),
 (201, 8, "Pollsmax", "Tennessee Governor & Senate Polling Average (4건/1건) & TargetSmart / Targoz Surveys",
  "https://www.pollsmax.com/governor/tennessee/", "2026-09-12", NOW, 0),
 (202, 8, "Cardinal News / Virginia Elections", "Retired Maj. Gen. Bert Mizusawa wins Virginia GOP Senate primary to face Mark Warner",
  "https://cardinalnews.org/2026/08/04/mizusawa-wins-virginia-gop-senate-primary/", "2026-08-04", NOW, 1),
 (203, 9, "Office of the Texas Governor / TCEQ", "Gov. Abbott Directs TCEQ to Freeze Environmental Permits for Data Centers Pending Grid and Water Audits",
  "https://gov.texas.gov/news/post/governor-abbott-directs-tceq-to-pause-data-center-environmental-permits", "2026-09-21", NOW, 1),
 (204, 9, "Oregon Public Broadcasting / Office of the Governor", "Gov. Tina Kotek Endorses Statewide Data Center Moratorium and Halts State Land Approvals Through July 2027",
  "https://www.opb.org/article/2026/09/08/oregon-governor-tina-kotek-endorses-data-center-moratorium/", "2026-09-08", NOW, 1),
 (205, 8, "Signal Ohio / The Guardian", "Ohio Data Center Flashpoint: Ramaswamy Property Tax Relief Mandate & Brown Farmland-Water Protection Campaign",
  "https://signalohio.org/2026/09/18/ohio-governor-senate-candidates-target-data-center-tax-breaks-and-water/", "2026-09-24", NOW, 1),
]

for s in SOURCES:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", s)

# ================================================================ 2. 후보 명단 동기화 (5명)
# 1) FL U.S. Senate: candidate_id=61 ('Alexander Vindman / Angie Nixon', I, Declared) -> Angie Nixon (D, Nominee)
cur.execute("""UPDATE politician SET full_name='Angie Nixon', party='D',
    current_office='U.S. Senate', last_updated=? WHERE politician_id=61""", (NOW,))
cur.execute("""UPDATE candidate SET candidate_name='Angie Nixon', candidate_party='D',
    current_position='Florida State Representative', current_status='Nominee',
    source_id=190, last_updated=? WHERE candidate_id=61""", (NOW,))

# 2) 신규 등재 후보 (FL Vindman Withdrawn, TN Blackburn/Green/Bradshaw Nominee, VA Mizusawa Nominee)
CAND_UPDATES = [
    # (pol_id, name, party, state, office, race_id, cand_id, cur_pos, status, src_id)
    (130, "Alexander Vindman", "D", "FL", "U.S. Senate", rid("FL","U.S. Senate"), 130, "Retired U.S. Army Lieutenant Colonel", "Withdrawn", 190),
    (131, "Marsha Blackburn", "R", "TN", "Governor", rid("TN","Governor"), 131, "U.S. Senator", "Nominee", 201),
    (132, "Jerri Green", "D", "TN", "Governor", rid("TN","Governor"), 132, "Shelby County Official", "Nominee", 201),
    (133, "Marquita Bradshaw", "D", "TN", "U.S. Senate", rid("TN","U.S. Senate"), 133, "Environmental Justice Advocate", "Nominee", 201),
    (134, "Bert Mizusawa", "R", "VA", "U.S. Senate", rid("VA","U.S. Senate"), 134, "Retired U.S. Army Major General", "Nominee", 202),
]

for pol_id, name, party, st, off, r_id, cand_id, cur_pos, status, src_id in CAND_UPDATES:
    cur.execute("""INSERT OR REPLACE INTO politician(politician_id,full_name,party,state_code,
        current_office,last_updated) VALUES (?,?,?,?,?,?)""",
        (pol_id, name, party, st, off, NOW))
    cur.execute("""INSERT OR REPLACE INTO candidate(candidate_id,race_id,politician_id,candidate_name,
        candidate_party,is_incumbent,current_position,current_status,status_code,source_id,last_updated)
        VALUES (?,?,?,?,?,0,?,?,'OK',?,?)""",
        (cand_id, r_id, pol_id, name, party, cur_pos, status, src_id, NOW))

# ================================================================ 3. 정책 입장 및 레버리지 갱신 (5명)
ev_base = cur.execute("SELECT COALESCE(MAX(evidence_id),0) FROM position_evidence").fetchone()[0]

# (1) Greg Abbott (TX Governor, R, pos_id 1): 9/21 TCEQ 데이터센터 환경·폐수·수리권 인허가 전면 중단 지시
ev_abbott = ev_base + 1
cur.execute("""INSERT OR REPLACE INTO position_evidence(evidence_id,position_id,evidence_type,summary,
    evidence_date,source_id,binding_code,scope_code,direction) VALUES
    (?,1,'Executive order',
     'TCEQ에 ERCOT·PUCT·TWDB의 전력망·수자원 감사가 완료될 때까지 데이터센터 대상 대기·폐수·우수·수리권 등 모든 환경 인허가 발급을 전면 중단하도록 지시하고 냉각수 사용량 보고 의무 위반에 대한 법적 제재 경고',
     '2026-09-21',203,'EXEC_DIRECTIVE','NEW_TOTAL','RESTRICTIVE')""", (ev_abbott,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (1,'GROWTH',-70,?,'OK')""", (ev_abbott,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (1,'WATER',-75,?,'OK')""", (ev_abbott,))
cur.execute("""UPDATE politician_dc_position SET
    policy_statement='ERCOT 그리드 접속 중단(8/3)에 이어 TCEQ에 데이터센터 환경·폐수·수리권 인허가 전면 중단을 지시(9/21). 주거용 전기요금 보호, 수자원 고갈 방지 및 농촌 주거지 입지 제한 명령.',
    last_updated=? WHERE position_id=1""", (NOW,))

# (2) Tina Kotek (OR Governor, D, pos_id 14): 9/8 전주 모라토리엄 공개 지지 및 주유지 인허가·임대 중단 지시
ev_kotek = ev_base + 2
cur.execute("""INSERT OR REPLACE INTO position_evidence(evidence_id,position_id,evidence_type,summary,
    evidence_date,source_id,binding_code,scope_code,direction) VALUES
    (?,14,'Executive order',
     '오리건 주의사당 집회에서 주 단위 신규 데이터센터 모라토리엄 지지를 공식 선언하고, 주정부 기관에 2027년 7월까지 미승인 데이터센터 관련 주유지 임대·지역권·토지이용 및 수자원 인허가 처리를 즉각 중단하도록 지시',
     '2026-09-08',204,'EXEC_DIRECTIVE','NEW_TOTAL','RESTRICTIVE')""", (ev_kotek,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (14,'GROWTH',-75,?,'OK')""", (ev_kotek,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (14,'WATER',-50,?,'OK')""", (ev_kotek,))
cur.execute("""UPDATE politician_dc_position SET
    policy_statement='기업지구 세제혜택 1년 중단 서명에 이어 주 단위 신규 데이터센터 모라토리엄을 공식 지지(9/8)하고 2027년 7월까지 주유지 인허가·임대 전면 중단 지시.',
    last_updated=? WHERE position_id=14""", (NOW,))

# (3) Vivek Ramaswamy (OH Governor, R, pos_id 8): 'Ohioans-First' 공식 정책안 — 인근 주민 재산세 전액 감면 및 세제특혜 중단
ev_vivek = ev_base + 3
cur.execute("""INSERT OR REPLACE INTO position_evidence(evidence_id,position_id,evidence_type,summary,
    evidence_date,source_id,binding_code,scope_code,direction) VALUES
    (?,8,'Campaign promise',
     'Ohioans-First 데이터센터 공식 정책안 발표: 인근 주민 전기요금 무상·할인 및 재산세 전액 감면, 지역사회 순편익 없는 지자체 세제 감면 중단 입법 전까지 취임 첫날 행정명령으로 신규 승인 전면 중단 공약',
     '2026-09-18',205,'POLICY_PLAN','NEW_TOTAL','RESTRICTIVE')""", (ev_vivek,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (8,'TAX',-60,?,'OK')""", (ev_vivek,))
cur.execute("""UPDATE politician_dc_position SET confidence_level='High',
    policy_statement='Ohioans-First 정책안을 통해 인근 주민 전기요금 보조·재산세 전액 감면 및 무분별한 세제특혜 중단 입법 전까지 신규 데이터센터 승인 중단 행정명령 공약.',
    last_updated=? WHERE position_id=8""", (NOW,))

# (4) Josh Shapiro (PA Governor, D, pos_id 5): 행정명령 2026-05호(GRID 기준) 판매세 면제 및 DEP 수질·환경 인허가 연계
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (5,'TAX',-55,15,'OK')""")
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (5,'WATER',-45,16,'OK')""")
cur.execute("""UPDATE politician_dc_position SET
    policy_statement='행정명령 2026-05호(GRID 기준)를 통해 신속 인허가 배제, NDA 금지, 전력망·수자원 보호 및 지역 승인 동의명령 서명을 주 데이터센터 판매세 면제 및 환경 인허가와 의무 연계.',
    last_updated=? WHERE position_id=5""", (NOW,))

# (5) Sherrod Brown (OH U.S. Senate, D, pos_id 10): 농촌 수자원 고갈 및 우량 농지 잠식 비판 공개 발언
ev_brown = ev_base + 4
cur.execute("""INSERT OR REPLACE INTO position_evidence(evidence_id,position_id,evidence_type,summary,
    evidence_date,source_id,binding_code,scope_code,direction) VALUES
    (?,10,'Public statement',
     '오하이오 농촌 캠페인에서 대규모 데이터센터가 지역 상수원을 고갈시키고 우량 농지를 잠식하며 일반 가계 전기요금을 인상시킨다고 비판하고 수자원·전력망 보호 기준 강화 촉구',
     '2026-09-24',205,'PUBLIC_STATEMENT','NEW_CONDITIONAL','RESTRICTIVE')""", (ev_brown,))
cur.execute("""INSERT OR REPLACE INTO position_axis_score(position_id,axis_code,axis_score,
    evidence_id,status_code) VALUES (10,'WATER',-55,?,'OK')""", (ev_brown,))
cur.execute("""UPDATE politician_dc_position SET confidence_level='High',
    policy_statement='Husted의 데이터센터 세제 감면을 정면 비판하며 빅테크 세제특혜 폐지, 전력망 비용 자체 부담, 농촌 수자원 및 우량 농지 보호 규제를 촉구.',
    last_updated=? WHERE position_id=10""", (NOW,))

# ================================================================ 4. 여론조사 적재 (29개 레이스, 129건)
NEW_POLLS = [
 # ---- 1. TX U.S. Senate (Talarico vs Paxton — D+2.7 우세 유지)
 ("TX","U.S. Senate","Trafalgar Group (R)","2026-10-05","2026-10-08",1086,"LV",        3.0, 0, 172),
 ("TX","U.S. Senate","YouGov","2026-10-02","2026-10-05",3625,"LV",                     6.0, 0, 173),
 ("TX","U.S. Senate","New York Times / Siena College","2026-09-26","2026-09-30",615,"LV",6.0,0,171),
 ("TX","U.S. Senate","Rasmussen Reports (R)","2026-09-27","2026-09-29",1128,"LV",      1.0, 0, 170),
 ("TX","U.S. Senate","Pollsmax 평균 (49건)","2026-10-08","2026-10-08",None,None,        2.7, 1, 170),

 # ---- 2. TX Governor (Hinojosa vs Abbott — 평균 R+4.4, 최신 단건 D+1.0/D+6.0 접전)
 ("TX","Governor","YouGov","2026-10-02","2026-10-05",3625,"LV",                        1.0, 0, 173),
 ("TX","Governor","New York Times / Siena College","2026-09-26","2026-09-30",615,"LV", 6.0, 0, 171),
 ("TX","Governor","Pollsmax 평균 (43건)","2026-10-05","2026-10-05",None,None,          -4.4, 1, 170),

 # ---- 3. OH U.S. Senate (Brown vs Husted — 평균 D+3.5)
 ("OH","U.S. Senate","co/efficient (R)","2026-10-04","2026-10-06",925,"LV",           -1.0, 0, 174),
 ("OH","U.S. Senate","SSRS","2026-10-02","2026-10-05",760,"LV",                        6.0, 0, 175),
 ("OH","U.S. Senate","New York Times / Siena College","2026-09-27","2026-10-01",616,"LV",3.0,0,171),
 ("OH","U.S. Senate","YouGov","2026-09-27","2026-09-30",3780,"LV",                     4.0, 0, 173),
 ("OH","U.S. Senate","Pollsmax 평균 (32건)","2026-10-06","2026-10-06",None,None,        3.5, 1, 174),

 # ---- 4. OH Governor (Acton vs Ramaswamy — 평균 D+2.1 우세 확대)
 ("OH","Governor","co/efficient (R)","2026-10-04","2026-10-06",925,"LV",              -2.0, 0, 174),
 ("OH","Governor","SSRS","2026-10-02","2026-10-05",760,"LV",                           8.0, 0, 175),
 ("OH","Governor","New York Times / Siena College","2026-09-27","2026-10-01",616,"LV", 4.0, 0, 171),
 ("OH","Governor","YouGov","2026-09-27","2026-09-30",3780,"LV",                        4.0, 0, 173),
 ("OH","Governor","Pollsmax 평균 (27건)","2026-10-06","2026-10-06",None,None,           2.1, 1, 174),

 # ---- 5. PA Governor (Shapiro vs Garrity — 평균 D+20.8)
 ("PA","Governor","Quinnipiac University","2026-10-01","2026-10-05",1159,"LV",        25.0, 0, 177),
 ("PA","Governor","Z to A Research (D)","2026-09-29","2026-10-01",630,"LV",           19.0, 0, 176),
 ("PA","Governor","Susquehanna Polling & Research (R)","2026-09-27","2026-09-30",700,"LV",21.0,0,176),
 ("PA","Governor","Pollsmax 평균 (19건)","2026-10-05","2026-10-05",None,None,          20.8, 1, 176),

 # ---- 6. MI U.S. Senate (El-Sayed vs Rogers — 평균 D+3.3 유지)
 ("MI","U.S. Senate","InsiderAdvantage (R)","2026-10-08","2026-10-10",1200,"LV",       2.0, 0, 179),
 ("MI","U.S. Senate","Wedgewood Polls","2026-10-06","2026-10-09",607,"LV",             6.0, 0, 178),
 ("MI","U.S. Senate","Quantus Insights (R)","2026-10-04","2026-10-06",762,"LV",        1.0, 0, 178),
 ("MI","U.S. Senate","YouGov","2026-10-01","2026-10-04",3949,"LV",                     1.0, 0, 173),
 ("MI","U.S. Senate","Mitchell Research & Communications","2026-09-29","2026-10-01",600,"LV",4.2,0,178),
 ("MI","U.S. Senate","Z to A Research (D)","2026-09-29","2026-10-01",483,"LV",         7.0, 0, 178),
 ("MI","U.S. Senate","Trafalgar Group (R)","2026-09-28","2026-09-30",1085,"LV",        1.8, 0, 172),
 ("MI","U.S. Senate","Pollsmax 평균 (49건)","2026-10-10","2026-10-10",None,None,        3.3, 1, 178),

 # ---- 7. MI Governor (Benson vs James — 평균 D+6.7)
 ("MI","Governor","Wedgewood Polls","2026-10-06","2026-10-09",607,"LV",               10.0, 0, 178),
 ("MI","Governor","YouGov","2026-10-01","2026-10-04",3949,"LV",                        3.0, 0, 173),
 ("MI","Governor","Mitchell Research & Communications","2026-09-29","2026-10-01",682,"LV",7.0,0,178),
 ("MI","Governor","Z to A Research (D)","2026-09-29","2026-10-01",483,"LV",           10.0, 0, 178),
 ("MI","Governor","Pollsmax 평균 (40건)","2026-10-09","2026-10-09",None,None,           6.7, 1, 178),

 # ---- 8. GA U.S. Senate (Ossoff vs Collins — 평균 D+9.2)
 ("GA","U.S. Senate","Trafalgar Group (R)","2026-10-07","2026-10-09",1101,"LV",        8.0, 0, 172),
 ("GA","U.S. Senate","Wedgewood Polls","2026-09-30","2026-10-03",600,"LV",            10.0, 0, 180),
 ("GA","U.S. Senate","InsiderAdvantage (R)","2026-09-20","2026-09-23",1200,"LV",       8.0, 0, 180),
 ("GA","U.S. Senate","Big Data Poll (R)","2026-09-20","2026-09-23",678,"LV",          11.0, 0, 180),
 ("GA","U.S. Senate","Pollsmax 평균 (19건)","2026-10-09","2026-10-09",None,None,        9.2, 1, 180),

 # ---- 9. GA Governor (Bottoms vs Jackson — 평균 R+0.2 리드 역전!)
 ("GA","Governor","Wedgewood Polls","2026-09-30","2026-10-03",600,"LV",               -2.0, 0, 180),
 ("GA","Governor","Pollsmax 평균 (13건)","2026-10-03","2026-10-03",None,None,          -0.2, 1, 180),

 # ---- 10. NC U.S. Senate (Cooper vs Whatley — 평균 D+8.4)
 ("NC","U.S. Senate","Trafalgar Group (R)","2026-10-08","2026-10-10",1091,"LV",        8.0, 0, 172),
 ("NC","U.S. Senate","East Carolina University","2026-09-30","2026-10-03",810,"LV",    7.0, 0, 182),
 ("NC","U.S. Senate","Pollsmax 평균 (41건)","2026-10-10","2026-10-10",None,None,        8.4, 1, 181),

 # ---- 11. NH U.S. Senate (Pappas vs Sununu — 평균 D+5.3)
 ("NH","U.S. Senate","YouGov","2026-10-02","2026-10-05",1520,"LV",                     8.0, 0, 173),
 ("NH","U.S. Senate","Saint Anselm College","2026-09-27","2026-09-29",1042,"LV",       7.0, 0, 184),
 ("NH","U.S. Senate","Trafalgar Group (R)","2026-09-25","2026-09-27",1082,"LV",        6.0, 0, 172),
 ("NH","U.S. Senate","New York Times / Siena College","2026-09-18","2026-09-22",613,"LV",5.0,0,171),
 ("NH","U.S. Senate","University of New Hampshire","2026-09-17","2026-09-21",1418,"LV",8.0, 0, 183),
 ("NH","U.S. Senate","Pollsmax 평균 (26건)","2026-10-05","2026-10-05",None,None,        5.3, 1, 183),

 # ---- 12. ME U.S. Senate (Jackson vs Collins — 평균 D+2.7)
 ("ME","U.S. Senate","Rasmussen Reports (R)","2026-10-06","2026-10-08",804,"LV",       2.0, 0, 185),
 ("ME","U.S. Senate","The Washington Post / SSPG","2026-10-01","2026-10-05",800,"LV",  4.0, 0, 186),
 ("ME","U.S. Senate","Marist University","2026-10-01","2026-10-04",1505,"RV",          4.0, 0, 185),
 ("ME","U.S. Senate","Trafalgar Group (R)","2026-09-29","2026-10-01",1091,"LV",        0.3, 0, 172),
 ("ME","U.S. Senate","CBS News / YouGov","2026-09-28","2026-10-01",1136,"LV",          0.0, 0, 173),
 ("ME","U.S. Senate","Pollsmax 평균 (24건)","2026-10-08","2026-10-08",None,None,        2.7, 1, 185),

 # ---- 13. IA U.S. Senate (Turek vs Hinson — 평균 R+0.1 리드 재역전!)
 ("IA","U.S. Senate","Emerson College","2026-10-03","2026-10-06",650,"LV",            -2.0, 0, 188),
 ("IA","U.S. Senate","SSRS","2026-10-02","2026-10-05",801,"LV",                       -2.0, 0, 175),
 ("IA","U.S. Senate","Suffolk University","2026-10-01","2026-10-04",500,"LV",          4.0, 0, 187),
 ("IA","U.S. Senate","New York Times / Siena College","2026-09-28","2026-10-01",606,"LV",-1.0,0,171),
 ("IA","U.S. Senate","Rasmussen Reports (R)","2026-09-27","2026-09-30",1048,"LV",      4.0, 0, 187),
 ("IA","U.S. Senate","Pollsmax 평균 (28건)","2026-10-06","2026-10-06",None,None,       -0.1, 1, 187),

 # ---- 14. IA Governor (Sand vs Lahn — 평균 D+7.0 우세 확대)
 ("IA","Governor","Emerson College","2026-10-03","2026-10-06",650,"LV",                4.0, 0, 188),
 ("IA","Governor","SSRS","2026-10-02","2026-10-05",801,"LV",                           9.0, 0, 175),
 ("IA","Governor","Suffolk University","2026-10-01","2026-10-04",500,"LV",            12.0, 0, 187),
 ("IA","Governor","New York Times / Siena College","2026-09-28","2026-10-01",606,"LV",11.0, 0, 171),
 ("IA","Governor","Pollsmax 평균 (16건)","2026-10-06","2026-10-06",None,None,           7.0, 1, 187),

 # ---- 15. AK U.S. Senate (Peltola vs Sullivan — 평균 D+1.2 박빙)
 ("AK","U.S. Senate","InsiderAdvantage (R)","2026-10-08","2026-10-10",1200,"LV",       5.0, 0, 179),
 ("AK","U.S. Senate","Alaska Survey Research","2026-09-30","2026-10-03",1512,"LV",     2.0, 0, 189),
 ("AK","U.S. Senate","Quantus Insights (R)","2026-09-28","2026-09-30",758,"LV",       -0.3, 0, 189),
 ("AK","U.S. Senate","New York Times / Siena College","2026-09-26","2026-09-30",504,"LV",7.0,0,171),
 ("AK","U.S. Senate","Trafalgar Group (R)","2026-09-22","2026-09-24",1079,"LV",       -1.0, 0, 172),
 ("AK","U.S. Senate","Pollsmax 평균 (24건)","2026-10-10","2026-10-10",None,None,        1.2, 1, 189),

 # ---- 16. FL U.S. Senate (Nixon vs Moody — 평균 R+7.0)
 ("FL","U.S. Senate","St. Pete Polls","2026-10-05","2026-10-07",836,"LV",             -2.0, 0, 191),
 ("FL","U.S. Senate","YouGov","2026-10-02","2026-10-05",3813,"LV",                    -5.0, 0, 173),
 ("FL","U.S. Senate","James Madison Institute","2026-10-01","2026-10-04",1171,"LV",  -10.0, 0, 190),
 ("FL","U.S. Senate","Mason-Dixon Polling & Strategy","2026-09-28","2026-10-01",625,"LV",-10.0,0,190),
 ("FL","U.S. Senate","Change Research (D)","2026-09-24","2026-09-27",1063,"LV",       -1.0, 0, 190),
 ("FL","U.S. Senate","Pollsmax 평균 (14건)","2026-10-07","2026-10-07",None,None,       -7.0, 1, 190),

 # ---- 17. FL Governor (Jolly vs Donalds — AGING 해소, 평균 R+4.7 / St. Pete 동률)
 ("FL","Governor","St. Pete Polls","2026-10-05","2026-10-07",836,"LV",                 0.0, 0, 191),
 ("FL","Governor","YouGov","2026-10-02","2026-10-05",3813,"LV",                       -2.0, 0, 173),
 ("FL","Governor","James Madison Institute","2026-10-01","2026-10-04",1174,"LV",     -10.0, 0, 190),
 ("FL","Governor","Mason-Dixon Polling & Strategy","2026-09-28","2026-10-01",625,"LV",-7.0, 0, 190),
 ("FL","Governor","Change Research (D)","2026-09-24","2026-09-27",1063,"LV",          2.0, 0, 190),
 ("FL","Governor","Stetson University","2026-09-17","2026-09-21",830,"LV",           -12.0, 0, 190),
 ("FL","Governor","St. Pete Polls","2026-09-14","2026-09-17",913,"LV",                -1.0, 0, 191),
 ("FL","Governor","Pollsmax 평균 (29건)","2026-10-07","2026-10-07",None,None,          -4.7, 1, 190),

 # ---- 18. OR Governor (Kotek vs Drazan — AGING 해소, 단건 D+4.0 역전 / 평균 R+0.4 초박빙)
 ("OR","Governor","GBAO (D)","2026-10-01","2026-10-04",800,"LV",                       4.0, 0, 192),
 ("OR","Governor","DHM Research","2026-09-28","2026-10-01",549,"LV",                   2.0, 0, 193),
 ("OR","Governor","DHM Research","2026-09-24","2026-09-27",915,"LV",                  -2.0, 0, 193),
 ("OR","Governor","Pollsmax 평균 (7건)","2026-10-04","2026-10-04",None,None,           -0.4, 1, 192),

 # ---- 19. NY Governor (Hochul vs Blakeman — 평균 D+11.9 우세 확대)
 ("NY","Governor","Emerson College","2026-10-02","2026-10-05",900,"LV",               12.0, 0, 188),
 ("NY","Governor","Marist University","2026-10-01","2026-10-04",1361,"RV",            11.0, 0, 194),
 ("NY","Governor","co/efficient (R)","2026-09-23","2026-09-25",1046,"LV",              7.0, 0, 194),
 ("NY","Governor","Quinnipiac University","2026-09-17","2026-09-20",1026,"LV",        19.0, 0, 177),
 ("NY","Governor","Pollsmax 평균 (28건)","2026-10-05","2026-10-05",None,None,          11.9, 1, 194),

 # ---- 20. NV Governor (Ford vs Lombardo — 76일 AGING 해소, 평균 R+3.5 접전 추격)
 ("NV","Governor","Noble Predictive Insights","2026-09-23","2026-09-26",708,"LV",     -2.0, 0, 195),
 ("NV","Governor","Emerson College","2026-09-05","2026-09-08",680,"LV",                2.0, 0, 195),
 ("NV","Governor","Wedgewood Polls","2026-07-09","2026-07-12",350,"LV",               -3.0, 0, 195),
 ("NV","Governor","Pollsmax 평균 (13건)","2026-09-26","2026-09-26",None,None,          -3.5, 1, 195),

 # ---- 21. AZ Governor (Hobbs vs Biggs — 55일 AGING 해소, 평균 D+6.6)
 ("AZ","Governor","GrayHouse (R)","2026-10-05","2026-10-08",550,"LV",                  6.0, 0, 196),
 ("AZ","Governor","GQR (D)","2026-10-02","2026-10-05",600,"LV",                        4.0, 0, 196),
 ("AZ","Governor","Equis Research","2026-09-06","2026-09-09",1214,"RV",                6.0, 0, 196),
 ("AZ","Governor","BSP Research","2026-09-01","2026-09-04",1300,"LV",                 13.0, 0, 196),
 ("AZ","Governor","Pollsmax 평균 (24건)","2026-10-08","2026-10-08",None,None,           6.6, 1, 196),

 # ---- 22. WI Governor (Crowley vs Tiffany — 격전지 54일 AGING 해소, D+3.0 리드 유지)
 ("WI","Governor","Marquette University","2026-09-16","2026-09-23",692,"LV",           3.0, 0, 197),
 ("WI","Governor","RMG Research","2026-07-20","2026-07-24",800,"RV",                   3.0, 0, 197),

 # ---- 23. IL U.S. Senate (Stratton vs Tracy — PJM High 사각지대 신규 해소)
 ("IL","U.S. Senate","Public Policy Polling (D)","2026-09-29","2026-10-01",569,"LV",  13.0, 0, 198),
 ("IL","U.S. Senate","Pollsmax 평균 (1건)","2026-10-01","2026-10-01",None,None,        12.0, 1, 198),

 # ---- 24. IL Governor (Pritzker vs Bailey — PJM High 사각지대 신규 해소)
 ("IL","Governor","Public Policy Polling (D)","2026-09-29","2026-10-01",569,"LV",     20.0, 0, 198),
 ("IL","Governor","Pollsmax 평균 (2건)","2026-10-01","2026-10-01",None,None,           18.5, 1, 198),

 # ---- 25. MD Governor (Moore vs Cox — PJM High 사각지대 신규 해소)
 ("MD","Governor","University of Maryland","2026-09-24","2026-09-27",776,"LV",        27.0, 0, 199),
 ("MD","Governor","University of Maryland, Baltimore County","2026-09-19","2026-09-22",776,"LV",27.0,0,199),
 ("MD","Governor","Zenith Research (D)","2026-08-01","2026-08-03",800,"LV",           27.0, 0, 199),
 ("MD","Governor","Pollsmax 평균 (3건)","2026-09-27","2026-09-27",None,None,           27.0, 1, 199),

 # ---- 26. AR U.S. Senate (Shoffner vs Cotton — 정책이벤트 주 사각지대 신규 해소)
 ("AR","U.S. Senate","GrayHouse (R)","2026-10-01","2026-10-04",550,"LV",             -11.0, 0, 200),
 ("AR","U.S. Senate","J.L. Partners (R)","2026-08-15","2026-08-18",803,"LV",         -15.8, 0, 200),
 ("AR","U.S. Senate","Hendrix College","2026-08-09","2026-08-12",1217,"LV",           3.0, 0, 200),
 ("AR","U.S. Senate","2040 Strategy Group (D)","2026-07-17","2026-07-25",586,"LV",    -3.0, 0, 200),
 ("AR","U.S. Senate","Pollsmax 평균 (5건)","2026-10-04","2026-10-04",None,None,       -10.8, 1, 200),

 # ---- 27. AR Governor (Love vs Sanders — 정책이벤트 주 사각지대 신규 해소)
 ("AR","Governor","J.L. Partners (R)","2026-08-15","2026-08-18",803,"LV",             -5.0, 0, 200),
 ("AR","Governor","Hendrix College","2026-08-11","2026-08-12",1217,"LV",              -5.0, 0, 200),
 ("AR","Governor","Pollsmax 평균 (2건)","2026-08-18","2026-08-18",None,None,           -7.4, 1, 200),

 # ---- 28. TN Governor (Green vs Blackburn — PJM High 사각지대 신규 해소)
 ("TN","Governor","TargetSmart (D)","2026-09-09","2026-09-12",600,"LV",               -9.0, 0, 201),
 ("TN","Governor","Targoz Market Research","2026-08-23","2026-08-26",1200,"RV",      -13.0, 0, 201),
 ("TN","Governor","Pollsmax 평균 (4건)","2026-09-12","2026-09-12",None,None,          -15.4, 1, 201),

 # ---- 29. TN U.S. Senate (Bradshaw vs Hagerty — PJM High 사각지대 신규 해소)
 ("TN","U.S. Senate","Targoz Market Research","2026-08-23","2026-08-26",1200,"RV",   -20.0, 0, 201),
 ("TN","U.S. Senate","Pollsmax 평균 (1건)","2026-08-26","2026-08-26",None,None,       -22.5, 1, 201),
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

# ================================================================ 5. v_poll_coverage 10/13 기준 재정의
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
            ELSE CAST(julianday('2026-10-13') - julianday(l.last_poll_date) AS INTEGER)
       END AS poll_age_days,
       CASE
         WHEN l.poll_count = 0                       THEN 'NO_POLLING'
         WHEN julianday('2026-10-13') - julianday(l.last_poll_date) > 90 THEN 'STALE'
         WHEN julianday('2026-10-13') - julianday(l.last_poll_date) > 30 THEN 'AGING'
         ELSE 'CURRENT'
       END AS coverage_status
FROM latest l
LEFT JOIN comp c ON c.race_id = l.race_id
LEFT JOIN marg m ON m.race_id = l.race_id;
""")

# ================================================================ 6. change_log 기록 (19건)
cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
CHANGES = [
 ("NEW_CANDIDATE","FL","FL 연방상원 Angie Nixon(민주) 8/18 경선 승리 공식 후보 확정 및 Alexander Vindman(Withdrawn) 분리 등재",
  "Alexander Vindman / Angie Nixon (I-Declared)","Angie Nixon (D-Nominee)",NOW,190),
 ("NEW_CANDIDATE","TN","TN 주지사 Marsha Blackburn(공화)·Jerri Green(민주) 및 연방상원 Marquita Bradshaw(민주) 8/6 경선 승리 후보 등재",
  None,"Blackburn(R) vs Green(D) / Bradshaw(D)",NOW,201),
 ("NEW_CANDIDATE","VA","VA 연방상원 Bert Mizusawa(공화) 8/4 경선 승리 공식 후보 등재 (Mark Warner와 본선 대진)",
  None,"Bert Mizusawa (R-Nominee)",NOW,202),
 ("WATER_REGULATION","TX","Greg Abbott 주지사 TCEQ에 데이터센터 환경·폐수·수리권 인허가 전면 중단 지시(9/21) — 레버리지 63.7→85.0, 지지도 -39.3→-45.3",
  "leverage: 63.7 / support: -39.3","leverage: 85.0 / support: -45.3 (실효 -38.5)",NOW,203),
 ("NEW_LEGISLATION","OR","Tina Kotek 주지사 주 단위 데이터센터 모라토리엄 공식 지지 및 2027년 7월까지 주유지 인허가·임대 중단 지시(9/8) — 레버리지 60.0→85.0, 지지도 -44.0→-55.3",
  "leverage: 60.0 / support: -44.0 (3축)","leverage: 85.0 / support: -55.3 (4축, 실효 -47.0)",NOW,204),
 ("TAX_INCENTIVE_CHANGE","OH","Vivek Ramaswamy 'Ohioans-First' 정책안(재산세 전액 감면·세제특혜 중단) 발표 — TAX(-60) 축 추가 및 레버리지 25.0→45.0 상향",
  "leverage: 25.0 / support: -58.5 (3축)","leverage: 45.0 / support: -58.8 (4축, 실효 -26.5)",NOW,205),
 ("TAX_INCENTIVE_CHANGE","PA","Josh Shapiro 행정명령 2026-05호(GRID 기준) 판매세 면제 및 수질·환경 인허가 연계 — TAX(-55)·WATER(-45) 보강으로 5대 축 완비",
  "축 3개 (support: -49.6)","축 5개 완비 (support: -50.3, 실효 -35.8)",NOW,176),
 ("WATER_REGULATION","OH","Sherrod Brown 농촌 상수원 고갈·우량 농지 잠식 비판 캠페인 반영 — WATER(-55) 4번째 축 보강 및 신뢰도 High 상향",
  "축 3개 (support: -57.3, Medium)","축 4개 (support: -57.1, High)",NOW,205),
 ("POLLING_CHANGE","IA","아이오와 연방상원 Hinson(공화) R+0.1 리드 재역전 (Emerson R+2, SSRS R+2 등 6건 추가, Pollsmax 평균 28건)",
  "Turek D+2.1","Hinson R+0.1 (리드 재역전)",NOW,187),
 ("POLLING_CHANGE","GA","조지아 주지사 Jackson(공화) R+0.2 리드 역전 (Wedgewood R+2 반영, Pollsmax 평균 13건)",
  "Bottoms D+2.8","Jackson R+0.2 (리드 역전)",NOW,180),
 ("POLLING_CHANGE","OR","오리건 주지사 Kotek(민주) 모라토리엄 지지 이후 10월 단건 조사 역전 우세 (GBAO D+4, DHM D+2 / 평균 Drazan R+0.4 초박빙, AGING 해소)",
  "Drazan R+2.0 (평균 R+0.5, AGING)","Kotek 단건 D+4.0 / 평균 R+0.4 (CURRENT 복귀)",NOW,192),
 ("POLLING_CHANGE","WI","위스콘신 주지사 Marquette 9월 조사(Crowley D+3.0) 적재로 격전지 노후화(54일 AGING) 해소 및 CURRENT 복귀",
  "Crowley D+3.3 (54일 AGING)","Crowley D+3.0 (20일 CURRENT)",NOW,197),
 ("POLLING_CHANGE","NV","네바다 주지사 Noble(R+2)·Emerson(D+2) 등 4건 적재로 장기 노후화(76일 AGING) 해소 및 Lombardo R+3.5 접전 추격 반영",
  "Lombardo R+9.0 (76일 AGING)","Lombardo R+3.5 (17일 CURRENT)",NOW,195),
 ("POLLING_CHANGE","AZ","애리조나 주지사 GrayHouse(D+6)·GQR(D+4) 등 5건 적재로 노후화(55일 AGING) 해소 — Hobbs D+6.6 우세 유지",
  "Hobbs D+6.7 (55일 AGING)","Hobbs D+6.6 (5일 CURRENT)",NOW,196),
 ("POLLING_CHANGE","FL","플로리다 주지사·상원 10월 최신 조사 14건 적재로 주지사 AGING 해소 — 주지사 Donalds R+4.7(St. Pete 동률), 상원 Moody R+7.0",
  "주지사 R+3.6 (34일 AGING) / 상원 R+6.0","주지사 R+4.7 (6일 CURRENT) / 상원 R+7.0",NOW,190),
 ("POLLING_CHANGE","IL","일리노이 연방상원(Stratton D+12.0)·주지사(Pritzker D+18.5) 신규 조사 4건 적재 — PJM High 고노출 사각지대(NO_POLLING) 2곳 해소",
  "NO_POLLING","상원 Stratton D+12.0 / 주지사 Pritzker D+18.5 (CURRENT)",NOW,198),
 ("POLLING_CHANGE","MD","메릴랜드 주지사(Moore vs Cox) UMD·UMBC·Zenith 4건 적재 — PJM High 고노출 사각지대(NO_POLLING) 해소 (Moore D+27.0)",
  "NO_POLLING","Moore D+27.0 (CURRENT)",NOW,199),
 ("POLLING_CHANGE","AR","아칸소 연방상원(Cotton R+10.8)·주지사(Sanders R+7.4) 8건 적재 — 데이터센터 정책이벤트 주 사각지대(NO_POLLING) 2곳 해소",
  "NO_POLLING","상원 Cotton R+10.8 (CURRENT) / 주지사 Sanders R+7.4",NOW,200),
 ("POLLING_CHANGE","TN","테네시 주지사(Blackburn R+15.4)·연방상원(Hagerty R+22.5) 5건 적재 — PJM High 사각지대(NO_POLLING) 2곳 해소",
  "NO_POLLING","주지사 Blackburn R+15.4 / 상원 Hagerty R+22.5",NOW,201),
]

for et, st, note, ov, nv, when, sid in CHANGES:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,target_pk,
        field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'election_race',?,'poll/position/candidate',?,?,?,?,?)""",
        (cid, et, st, st, ov, nv, when, sid, note))

con.commit()

print(f"✔ 2026-10-13 갱신 완료:")
print(f"  - 후보 명단 동기화: 5명 (FL Nixon 확정/Vindman 사퇴, TN Blackburn/Green/Bradshaw, VA Mizusawa)")
print(f"  - 정책 입장·레버리지 갱신: 5명 (TX Abbott, OR Kotek, OH Ramaswamy, PA Shapiro, OH Brown)")
print(f"  - 신규 조사 적재: {len(NEW_POLLS)}건 (29개 레이스)")
print(f"  - 변경 이력 기록: {len(CHANGES)}건")

con.close()
