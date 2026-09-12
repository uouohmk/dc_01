#!/usr/bin/env python3
"""
STEP 6 (부분): 데이터센터 입장 3차원 측정
  방향(axis_score) × 구속력(binding_force) × 범위(scope) × 직위권한(office_power)

원칙: 근거 레코드 없이는 점수를 넣을 수 없다 (trg_axis_requires_evidence).
"""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
TODAY = "2026-08-27"

# ==================================================== 1. 스키마 확장
cur.executescript("""
-- 구속력: 그 입장이 실제로 얼마나 강제되는가
CREATE TABLE IF NOT EXISTS binding_force (
    binding_code   TEXT PRIMARY KEY,
    label_ko       TEXT NOT NULL,
    weight         REAL NOT NULL,     -- 0~1
    note           TEXT
);
DELETE FROM binding_force;
INSERT INTO binding_force VALUES
 ('SIGNED_LAW',      '법률 서명·공포',        1.00,'이미 발효'),
 ('SIGNED_EO',       '행정명령 서명',          0.95,'즉시 효력, 후임자가 뒤집을 수 있음'),
 ('EXEC_DIRECTIVE',  '규제기관 지시',          0.85,'집행은 기관 재량'),
 ('VOTE_RECORD',     '표결 기록',             0.70,'실제 행동이나 과거형'),
 ('BILL_FILED',      '법안 발의·공동발의',      0.60,'통과 여부 불확실'),
 ('POLICY_PLAN',     '공식 정책안 발표',        0.45,'문서화됐으나 미집행'),
 ('CAMPAIGN_PROMISE','선거 공약',             0.40,'당선 전제'),
 ('PUBLIC_STATEMENT','공개 발언',             0.25,'구속력 없음'),
 ('CAMPAIGN_AD',     '선거 광고',             0.20,'수사(rhetoric) 중심');

-- 범위: 규제가 무엇에 걸리는가
CREATE TABLE IF NOT EXISTS regulation_scope (
    scope_code     TEXT PRIMARY KEY,
    label_ko       TEXT NOT NULL,
    weight         REAL NOT NULL,
    note           TEXT
);
DELETE FROM regulation_scope;
INSERT INTO regulation_scope VALUES
 ('NEW_TOTAL',        '신규 전면 중단',          1.00,'모라토리엄'),
 ('EXISTING_INCLUDED','기존 시설 포함 규제',      0.90,'소급 적용'),
 ('NEW_CONDITIONAL',  '신규 조건부 허용',        0.75,'감사·심사 통과 시 허용'),
 ('SITING_BAN',       '입지 제한',              0.70,'특정 지역 금지'),
 ('LOCAL_CONSENT',    '지역 동의 의무',          0.65,'사실상 거부권'),
 ('INCENTIVE_REPEAL', '세제혜택 폐지',           0.60,'수익성 훼손, 건설은 가능'),
 ('COST_ALLOCATION',  '전력비용 부담 배분',       0.50,'짓되 비용을 내라'),
 ('DISCLOSURE',       '사용량 공개 의무',        0.25,'투명성만');

-- 직위별 실제 권한 (같은 -70 이라도 영향이 다르다)
CREATE TABLE IF NOT EXISTS office_power (
    office         TEXT PRIMARY KEY,
    weight         REAL NOT NULL,
    note           TEXT
);
DELETE FROM office_power;
INSERT INTO office_power VALUES
 ('Governor',    1.00,'행정명령·거부권·규제기관 지시 가능'),
 ('State Senate',0.70,'주 인허가·세제 입법권'),
 ('State House', 0.70,'주 인허가·세제 입법권'),
 ('U.S. Senate', 0.55,'주 인허가 직접 권한 없음. 연방 기준·세법 경유'),
 ('U.S. House',  0.45,'상동, 개별 영향력 더 낮음');

-- position_evidence 확장
ALTER TABLE position_evidence ADD COLUMN binding_code TEXT REFERENCES binding_force(binding_code);
ALTER TABLE position_evidence ADD COLUMN scope_code   TEXT REFERENCES regulation_scope(scope_code);
ALTER TABLE position_evidence ADD COLUMN direction    TEXT
     CHECK (direction IN ('RESTRICTIVE','SUPPORTIVE','NEUTRAL'));
""")

# 추가 출처
for row in [
 (20,9,"CBS Texas","Data centers emerge as key issue in Texas politics",
  "https://www.cbsnews.com/texas/news/data-centers-emerge-as-key-issue-in-texas-politics-where-candidates-for-governor-u-s-senate-stand/","2026-08-25",TODAY,0),
 (21,9,"Texas Tribune","New Texas data center projects frozen until state audits them",
  "https://www.texastribune.org/2026/08/03/texas-data-center-project-audit-greg-abbott/","2026-08-03",TODAY,0),
 (22,9,"E&E News/Politico","Texas governor talks tough on data centers, calls for clampdown",
  "https://www.eenews.net/articles/texas-governor-talks-tough-on-data-centers-calls-for-clampdown/","2026-06-11",TODAY,0),
 (23,9,"KUT (NPR Austin)","Texas leaders are divided on what to do about data centers",
  "https://www.kut.org/energy-environment/2026-08-19/austin-tx-texas-data-centers-regulations-greg-abbott","2026-08-19",TODAY,0),
 (24,9,"The Texan","Abbott, Hinojosa spotlight data centers in gubernatorial campaigns",
  "https://thetexan.news/elections/2026/gov-abbott-challenger-hinojosa-spotlight-data-centers-in-gubernatorial-campaigns/article_64c51f5d-db12-41e9-92ff-29643cbd3e93.html","2026-07-20",TODAY,0),
 (25,9,"Philadelphia Inquirer","The data center backlash bursts into the midterms",
  "https://www.inquirer.com/politics/data-centers-ai-politics-votter-opposition-democrats-republicans-pivot-shapiro-20260823.html","2026-08-23",TODAY,0),
]:
    cur.execute("""INSERT OR REPLACE INTO source(source_id,tier,publisher,title,url,
        published_date,retrieved_at,is_primary) VALUES (?,?,?,?,?,?,?,?)""", row)

# ==================================================== 2. 입장 데이터
# (이름, 주, 직위, 정당, 분류, 발전원선호, 요약)
# evidence: (유형, 요약, binding, scope, direction, 날짜, source_id)
# axes: GROWTH/POWER/RATES/WATER/TAX  (None = 근거 없음)
POSITIONS = [
 dict(name="Greg Abbott", st="TX", office="Governor", party="R",
   cls="Mixed", power="Natural Gas,Nuclear",
   summary="AI 유치를 주도했다가 2026년 6월 이후 급선회. 그리드 접속 승인을 감사 완료 시까지 중단시켰으나 세제혜택 폐지는 요구하지 않음.",
   conf="High",
   ev=[("Executive order","규제기관에 데이터센터가 주거용 전기요금을 낮추고 지역 물을 고갈시키지 않도록 운영할 것을 지시",
        "EXEC_DIRECTIVE","COST_ALLOCATION","RESTRICTIVE","2026-06-10",22),
       ("Executive order","PUC·ERCOT에 제안된 데이터센터의 전력·물 사용 감사가 끝날 때까지 그리드 접속 승인을 중단하도록 지시",
        "EXEC_DIRECTIVE","NEW_CONDITIONAL","RESTRICTIVE","2026-08-03",21),
       ("Public statement","감사에 통과해야 하며 농촌 주거지역에는 건설할 수 없다고 발표",
        "PUBLIC_STATEMENT","SITING_BAN","RESTRICTIVE","2026-08-20",20)],
   axes=dict(GROWTH=-55, POWER=-15, RATES=-70, WATER=-60, TAX=15),
   cats=[1,3,7,8,10,11]),

 dict(name="Gina Hinojosa", st="TX", office="Governor", party="D",
   cls="Restrictive", power=None,
   summary="특별회기 소집 전까지 신규 승인 전면 모라토리엄과 판매세 면제 폐지를 요구. Abbott의 조치는 실효성이 없다고 주장.",
   conf="High",
   ev=[("Campaign promise","주의회가 주민 보호 법안을 의결할 때까지 신규 데이터센터 건설 모라토리엄을 요구",
        "CAMPAIGN_PROMISE","NEW_TOTAL","RESTRICTIVE","2026-08-25",20),
       ("Campaign promise","Abbott가 승인한 데이터센터 대상 보조금 종료와 판매세 면제 폐지를 위한 특별회기 소집을 요구",
        "CAMPAIGN_PROMISE","INCENTIVE_REPEAL","RESTRICTIVE","2026-07-20",24),
       ("Campaign ad","농촌 지역 대상 TV 광고에서 Abbott가 데이터센터 업계에 주민을 팔아넘겼다고 주장",
        "CAMPAIGN_AD","NEW_TOTAL","RESTRICTIVE","2026-08-19",24),
       ("Public statement","물·전기 사용량 투명성과 농촌 주민의 참여 보장을 요구",
        "PUBLIC_STATEMENT","DISCLOSURE","RESTRICTIVE","2026-07-20",24)],
   axes=dict(GROWTH=-80, POWER=-30, RATES=-75, WATER=-70, TAX=-85),
   cats=[1,3,7,8,9,12]),

 dict(name="Ken Paxton", st="TX", office="U.S. Senate", party="R",
   cls="Mixed", power="Natural Gas,Nuclear",
   summary="'Texas First' 정책안. 연방 규제 완화·발전 확충은 지지하면서 동시에 농촌 입지 금지와 세제혜택 폐지를 주장하는 혼합형.",
   conf="High",
   ev=[("Campaign promise","'Texas First Data Center Plan' 발표. 농촌 주거지역 AI 데이터센터 건설 금지와 판매세 면제 등 인센티브 폐지를 포함",
        "POLICY_PLAN","SITING_BAN","RESTRICTIVE","2026-08-24",20),
       ("Introduced bill","DATA Act 공동발의 의사 표명. 낡은 규제를 없애고 데이터센터가 주민 전기요금을 올리지 않도록 새 발전설비를 구축하는 내용",
        "BILL_FILED","COST_ALLOCATION","SUPPORTIVE","2026-08-24",20),
       ("Campaign promise","데이터센터가 자체 전력비용을 부담하고 폐쇄형 냉각수 시스템을 사용하도록 요구",
        "POLICY_PLAN","COST_ALLOCATION","RESTRICTIVE","2026-08-24",20)],
   axes=dict(GROWTH=-55, POWER=45, RATES=-70, WATER=-70, TAX=-85),
   cats=[1,2,3,5,7,8,9,10]),

 dict(name="James Talarico", st="TX", office="U.S. Senate", party="D",
   cls="Restrictive", power=None,
   summary="'Hold Data Centers Accountable' 정책안. 지역사회에 유치 여부 결정권을 주는 조항이 핵심.",
   conf="High",
   ev=[("Campaign promise","주 판매세 인센티브 종료, 전력망·환경·일자리·투명성에 대한 연방 최소기준 설정을 공약",
        "POLICY_PLAN","INCENTIVE_REPEAL","RESTRICTIVE","2026-07-25",20),
       ("Campaign promise","지역사회가 데이터센터 유치 여부를 직접 결정할 권한을 갖도록 하겠다고 공약",
        "POLICY_PLAN","LOCAL_CONSENT","RESTRICTIVE","2026-07-25",20),
       ("Campaign promise","신규 데이터센터에 폐쇄형 냉각수 시스템 사용을 의무화하겠다고 공약",
        "POLICY_PLAN","DISCLOSURE","RESTRICTIVE","2026-07-25",20),
       ("Voted for","2023년 주의회에서 데이터센터 판매세 인센티브에 찬성 표결 (이후 재표결에는 불참, 법안 미성립)",
        "VOTE_RECORD","INCENTIVE_REPEAL","SUPPORTIVE","2023-05-01",20)],
   axes=dict(GROWTH=-60, POWER=-35, RATES=-70, WATER=-75, TAX=-80),
   cats=[1,3,7,8,9,12]),

 dict(name="Josh Shapiro", st="PA", office="Governor", party="D",
   cls="Concerned", power=None,
   summary="데이터센터 투자를 홍보하던 입장에서 선회. 건설을 막지는 않되 전력비용 부담과 지역 승인을 의무화하는 '짓되 비용을 내라' 유형.",
   conf="High",
   ev=[("Executive order","개발사가 프로젝트 관련 전력비용을 부담하고 지역 승인을 확보하도록 하는 동의명령 서명을 의무화",
        "SIGNED_EO","COST_ALLOCATION","RESTRICTIVE","2026-08-18",8),
       ("Executive order","기존·향후 데이터센터 프로젝트의 신속 인허가 프로그램 참여를 금지",
        "SIGNED_EO","NEW_CONDITIONAL","RESTRICTIVE","2026-08-18",8),
       ("Campaign ad","상대 후보 Garrity를 '펜실베이니아 최고의 데이터센터 팬'이라고 지칭하는 광고 집행",
        "CAMPAIGN_AD","COST_ALLOCATION","RESTRICTIVE","2026-08-20",8)],
   axes=dict(GROWTH=-40, POWER=-10, RATES=-85, WATER=None, TAX=None),
   cats=[1,3,8,12]),

 dict(name="Stacy Garrity", st="PA", office="Governor", party="R",
   cls="Restrictive", power=None,
   summary="과거에는 데이터센터 유치 확대를 주장했으나 현재는 향후 개발 '일시 중단'을 요구. 수사는 온건하나 범위는 더 넓음.",
   conf="Medium",
   ev=[("Campaign promise","향후 데이터센터 개발의 '일시 중단(pause)'을 요구",
        "CAMPAIGN_PROMISE","NEW_TOTAL","RESTRICTIVE","2026-08-20",8),
       ("Campaign ad","Shapiro가 아마존 데이터센터 유치로 주민을 배신했다는 취지의 광고 집행",
        "CAMPAIGN_AD","NEW_TOTAL","RESTRICTIVE","2026-08-18",8),
       ("Public statement","과거 펜실베이니아가 데이터센터 유치에 더 적극적이어야 한다고 발언",
        "PUBLIC_STATEMENT","COST_ALLOCATION","SUPPORTIVE","2025-01-01",8)],
   axes=dict(GROWTH=-70, POWER=None, RATES=-40, WATER=None, TAX=None),
   cats=[1,8]),

 dict(name="Amy Acton", st="OH", office="Governor", party="D",
   cls="Restrictive", power=None,
   summary="'조건부 모라토리엄' 계획 발표. 상대 후보를 빅테크 억만장자와 연결짓는 프레임.",
   conf="Medium",
   ev=[("Campaign promise","데이터센터에 대한 '조건부 모라토리엄' 계획을 발표",
        "POLICY_PLAN","NEW_CONDITIONAL","RESTRICTIVE","2026-07-15",10),
       ("Public statement","Ramaswamy가 빅테크 억만장자로부터 지역사회를 지킬 것으로 신뢰할 수 없다고 주장",
        "PUBLIC_STATEMENT","NEW_CONDITIONAL","RESTRICTIVE","2026-07-15",10)],
   axes=dict(GROWTH=-75, POWER=None, RATES=-55, WATER=None, TAX=None),
   cats=[1,8,12]),

 dict(name="Vivek Ramaswamy", st="OH", office="Governor", party="R",
   cls="Concerned", power=None,
   summary="건설 자체는 막지 않되 데이터센터 기업이 인근 주민 전기요금을 부담해야 한다고 주장.",
   conf="Medium",
   ev=[("Public statement","데이터센터 기업이 인근 주민의 전기요금을 부담해야 한다고 요구",
        "PUBLIC_STATEMENT","COST_ALLOCATION","RESTRICTIVE","2026-08-05",10),
       ("Public statement","전기요금 상승·소음·오염과 오하이오 가정에 대한 경제적 편익 부재에 관한 민원을 들었다고 언급",
        "PUBLIC_STATEMENT","DISCLOSURE","RESTRICTIVE","2026-08-05",10)],
   axes=dict(GROWTH=-15, POWER=None, RATES=-70, WATER=None, TAX=None),
   cats=[1,8,11]),

 dict(name="Jon Husted", st="OH", office="U.S. Senate", party="R",
   cls="Supportive", power=None,
   summary="부지사 시절 데이터센터 세제 감면을 지원하고 오하이오의 큰 경제 기회로 평가. 이번 사이클에서 방어 위치.",
   conf="High",
   ev=[("Supported legislation","부지사 재임 중 데이터센터에 대한 세제 감면을 지원",
        "VOTE_RECORD","INCENTIVE_REPEAL","SUPPORTIVE","2024-01-01",7),
       ("Public statement","데이터센터를 오하이오 주민에게 엄청난 경제적 기회라고 평가",
        "PUBLIC_STATEMENT","COST_ALLOCATION","SUPPORTIVE","2024-01-01",7)],
   axes=dict(GROWTH=75, POWER=None, RATES=None, WATER=None, TAX=85),
   cats=[1,2,9]),

 dict(name="Sherrod Brown", st="OH", office="U.S. Senate", party="D",
   cls="Concerned", power=None,
   summary="현직 Husted를 '데이터센터의 얼굴'로 공격하는 광고 집행. 수사 강도는 높으나 구체 정책안은 확인되지 않음.",
   conf="Low",
   ev=[("Campaign ad","현직 상원의원 Husted를 데이터센터의 얼굴이라고 지칭하는 광고 집행",
        "CAMPAIGN_AD","COST_ALLOCATION","RESTRICTIVE","2026-08-20",7),
       ("Campaign ad","오하이오 광고에서 데이터센터를 완전한 사기라고 표현",
        "CAMPAIGN_AD","NEW_TOTAL","RESTRICTIVE","2026-08-23",25)],
   axes=dict(GROWTH=-50, POWER=None, RATES=-60, WATER=None, TAX=None),
   cats=[1,8]),

 dict(name="Mike Rogers", st="MI", office="U.S. Senate", party="R",
   cls="Restrictive", power=None,
   summary="신규 데이터센터 건설 1년 모라토리엄 지지. 공화당 후보 중 방향·범위 모두 가장 강한 축.",
   conf="Medium",
   ev=[("Campaign promise","신규 데이터센터 건설에 대한 1년 모라토리엄을 지지한다고 표명",
        "CAMPAIGN_PROMISE","NEW_TOTAL","RESTRICTIVE","2026-08-20",9)],
   axes=dict(GROWTH=-85, POWER=None, RATES=None, WATER=None, TAX=None),
   cats=[1,10]),

 dict(name="Byron Donalds", st="FL", office="Governor", party="R",
   cls="Concerned", power=None,
   summary="데이터센터 규제를 제안하며 공화당 예비선거 승리. 구체 조치 범위는 아직 확인되지 않음.",
   conf="Low",
   ev=[("Campaign promise","플로리다 내 데이터센터에 대한 규제 도입을 제안",
        "CAMPAIGN_PROMISE","NEW_CONDITIONAL","RESTRICTIVE","2026-08-18",9)],
   axes=dict(GROWTH=-50, POWER=None, RATES=None, WATER=None, TAX=None),
   cats=[1]),
]

pos_id = 0
ev_id = 0
for p in POSITIONS:
    row = cur.execute("SELECT politician_id FROM politician WHERE full_name=? AND state_code=?",
                      (p["name"], p["st"])).fetchone()
    if not row:
        cur.execute("""INSERT INTO politician(politician_id,full_name,party,state_code,
            current_office,last_updated) VALUES ((SELECT MAX(politician_id)+1 FROM politician),
            ?,?,?,?,?)""", (p["name"], p["party"], p["st"], p["office"], TODAY))
        pid = cur.execute("SELECT MAX(politician_id) FROM politician").fetchone()[0]
    else:
        pid = row[0]

    race = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                       (p["st"], p["office"])).fetchone()
    pos_id += 1
    cur.execute("""INSERT INTO politician_dc_position(position_id,politician_id,race_id,
        candidate_status,dc_position,power_source_pref,policy_statement,confidence_level,
        data_type,status_code,last_updated)
        VALUES (?,?,?,?,?,?,?,?,'Fact','OK',?)""",
        (pos_id, pid, race[0] if race else None, "Challenger", p["cls"],
         p["power"], p["summary"], p["conf"], TODAY))

    first_ev = None
    for et, summ, bind, scope, dirn, dt, src in p["ev"]:
        ev_id += 1
        cur.execute("""INSERT INTO position_evidence(evidence_id,position_id,evidence_type,
            summary,evidence_date,source_id,binding_code,scope_code,direction)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (ev_id, pos_id, et, summ, dt, src, bind, scope, dirn))
        if first_ev is None:
            first_ev = ev_id

    for axis, score in p["axes"].items():
        cur.execute("""INSERT INTO position_axis_score(position_id,axis_code,axis_score,
            evidence_id,status_code) VALUES (?,?,?,?,?)""",
            (pos_id, axis, score, first_ev if score is not None else None,
             'OK' if score is not None else 'NO_CLEAR_PUBLIC_POSITION'))
    for c in p["cats"]:
        cur.execute("INSERT INTO position_policy_category VALUES (?,?)", (pos_id, c))

# ==================================================== 3. 실효 강도 뷰
cur.executescript("""
DROP VIEW IF EXISTS v_effective_position;
CREATE VIEW v_effective_position AS
WITH ev AS (
    -- 규제 방향 근거 중 (구속력 x 범위)가 최대인 건을 대표로 삼는다
    SELECT e.position_id,
           MAX(b.weight * s.weight) AS peak_leverage,
           MAX(b.weight) AS peak_binding,
           MAX(s.weight) AS peak_scope
    FROM position_evidence e
    JOIN binding_force    b ON b.binding_code = e.binding_code
    JOIN regulation_scope s ON s.scope_code   = e.scope_code
    WHERE e.direction = 'RESTRICTIVE'
    GROUP BY e.position_id
)
SELECT v.position_id, v.full_name, v.party, v.state_code, v.dc_position,
       v.support_score, v.axes_scored, v.evidence_count, v.confidence_level,
       p.current_office AS office, o.weight AS office_power,
       ev.peak_binding, ev.peak_scope,
       -- (A) 규제 레버리지: 근거 1건만 있어도 산출 가능. 항상 표시.
       ROUND(COALESCE(ev.peak_leverage,0) * o.weight * 100, 1) AS leverage_score,
       -- (B) 방향까지 반영한 실효치: 5개 축 중 3개 이상 확보된 경우에만 산출.
       CASE WHEN v.support_score IS NULL THEN NULL
            ELSE ROUND(v.support_score * COALESCE(ev.peak_leverage,0) * o.weight, 1) END
            AS effective_impact,
       CASE WHEN v.support_score IS NULL THEN 'AXES_INSUFFICIENT' ELSE 'OK' END
            AS direction_status,
       (SELECT b2.label_ko FROM position_evidence e2 JOIN binding_force b2
          ON b2.binding_code=e2.binding_code WHERE e2.position_id=v.position_id
          AND e2.direction='RESTRICTIVE' ORDER BY b2.weight DESC LIMIT 1) AS top_binding_label,
       (SELECT s2.label_ko FROM position_evidence e2 JOIN regulation_scope s2
          ON s2.scope_code=e2.scope_code WHERE e2.position_id=v.position_id
          AND e2.direction='RESTRICTIVE' ORDER BY s2.weight DESC LIMIT 1) AS top_scope_label
FROM v_support_score v
JOIN politician p ON p.politician_id = v.politician_id
LEFT JOIN office_power o ON o.office = p.current_office
LEFT JOIN ev ON ev.position_id = v.position_id;
""")
con.commit()

print(f"{'주':<3}{'이름':<19}{'당':<3}{'레버리지':>9}{'방향':>8}{'실효':>8}  근거")
for r in cur.execute("""SELECT state_code,full_name,party,leverage_score,support_score,
    effective_impact,top_binding_label,top_scope_label,office,evidence_count
    FROM v_effective_position ORDER BY leverage_score DESC"""):
    dd = f"{r[4]:>8}" if r[4] is not None else f"{'미확정':>7}"
    ee = f"{r[5]:>8}" if r[5] is not None else f"{'—':>9}"
    print(f"  {r[0]:<3}{r[1]:<19}{r[2]:<3}{r[3]:>8}{dd}{ee}  [{r[6]} / {r[7]}]")
con.close()
