-- =====================================================================
-- U.S. Midterm Election x Data Center Political Risk Tracker
-- STEP 1 : DATABASE SCHEMA (SQLite 3 호환 / PostgreSQL 이식 주석 포함)
-- v1.0  2026-08-27
--
-- 설계 원칙
--   P1. Fact 레이어에는 분석값을 넣지 않는다. 파생값은 전부 v_ 접두 뷰 또는
--       data_type='AI Analysis' 가 강제된 테이블에만 존재한다.
--   P2. 모르는 값은 0이 아니라 NULL + status_code 이다.
--   P3. 정치인 입장은 근거(position_evidence) 없이 저장할 수 없다. (트리거로 강제)
--   P4. 데이터센터 수치는 벤더별로 병렬 저장한다. 벤더 간 수치를 합치지 않는다.
-- =====================================================================

-- 실행 전 주의:
--   SQLite 는 log() 를 기본 제공하지 않는다 (3.35+ 에서 math extension 필요).
--   Python 사용 시: con.create_function('log',1,lambda x: math.log(x) if x and x>0 else None)
--   PostgreSQL 이식 시: log(x) -> ln(x), INTEGER PRIMARY KEY -> GENERATED ALWAYS AS IDENTITY,
--                       TEXT 날짜 -> DATE, CHECK 제약은 그대로 유효, 트리거는 PL/pgSQL 로 재작성.
--   검증 완료: 27 tables / 7 views / 4 triggers / 8 indexes 정상 생성 (2026-08-27)

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- L0. SOURCE LAYER
-- ---------------------------------------------------------------------

CREATE TABLE source (
    source_id        INTEGER PRIMARY KEY,
    tier             INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 9),
    -- 1 공식선거기관 2 주정부 3 미의회 4 후보공식 5 법안DB
    -- 6 공공기관 7 기업공식발표 8 산업리서치 9 주요언론
    publisher        TEXT    NOT NULL,
    title            TEXT,
    url              TEXT    NOT NULL,
    archive_url      TEXT,
    published_date   TEXT,                     -- ISO-8601. 불명 시 NULL
    retrieved_at     TEXT    NOT NULL,
    is_primary       INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0,1)),
    note             TEXT
);
CREATE INDEX ix_source_tier ON source(tier, published_date);

-- 동일 사실에 대해 출처가 충돌할 때 양쪽을 모두 보존
CREATE TABLE source_conflict (
    conflict_id      INTEGER PRIMARY KEY,
    target_table     TEXT    NOT NULL,
    target_pk        TEXT    NOT NULL,
    target_field     TEXT    NOT NULL,
    source_id_a      INTEGER NOT NULL REFERENCES source(source_id),
    value_a          TEXT    NOT NULL,
    source_id_b      INTEGER NOT NULL REFERENCES source(source_id),
    value_b          TEXT    NOT NULL,
    resolution       TEXT    CHECK (resolution IN
                        ('UNRESOLVED','PREFER_A','PREFER_B','BOTH_VALID_DIFFERENT_DEFINITION')),
    note             TEXT,
    logged_at        TEXT    NOT NULL
);

-- ---------------------------------------------------------------------
-- LOOKUPS
-- ---------------------------------------------------------------------

CREATE TABLE status_code (
    status_code      TEXT PRIMARY KEY,
    description      TEXT NOT NULL
);
INSERT INTO status_code VALUES
 ('OK',                       '정상 수집'),
 ('UNKNOWN',                  '조사했으나 확인 불가'),
 ('NOT_AVAILABLE',            '공개되지 않음'),
 ('NO_CLEAR_PUBLIC_POSITION', '정치인이 공개 입장을 밝힌 바 없음'),
 ('DISPUTED',                 '출처 간 충돌. source_conflict 참조'),
 ('NOT_YET_COLLECTED',        '수집 예정'),
 ('INSUFFICIENT_DATA',        '커버리지 미달로 점수 미산출');

CREATE TABLE party (
    party_code       TEXT PRIMARY KEY,
    party_name       TEXT NOT NULL
);
INSERT INTO party VALUES
 ('D','Democratic'),('R','Republican'),('I','Independent'),
 ('L','Libertarian'),('G','Green'),('O','Other'),('V','Vacant');

CREATE TABLE race_rating_scale (
    rating_code      TEXT PRIMARY KEY,
    rating_label     TEXT NOT NULL,
    lean             TEXT NOT NULL CHECK (lean IN ('D','R','N')),
    competitiveness  INTEGER NOT NULL   -- 0=Safe .. 100=Toss Up. 리스크 계산 입력
);
INSERT INTO race_rating_scale VALUES
 ('SAFE_D',   'Safe Democratic',  'D',   5),
 ('LIKELY_D', 'Likely Democratic','D',  30),
 ('LEAN_D',   'Lean Democratic',  'D',  65),
 ('TOSSUP',   'Toss Up',          'N', 100),
 ('LEAN_R',   'Lean Republican',  'R',  65),
 ('LIKELY_R', 'Likely Republican','R',  30),
 ('SAFE_R',   'Safe Republican',  'R',   5);

CREATE TABLE policy_category (
    category_id      INTEGER PRIMARY KEY,
    category_name    TEXT NOT NULL UNIQUE
);
INSERT INTO policy_category VALUES
 (1,'Data Center Expansion'),(2,'AI Infrastructure'),(3,'Electricity Grid'),
 (4,'Nuclear Power'),(5,'Natural Gas Power'),(6,'Renewable Energy'),
 (7,'Water Usage'),(8,'Electricity Prices'),(9,'Tax Incentives'),
 (10,'Local Zoning'),(11,'Environmental Regulation'),(12,'Community Consent');

CREATE TABLE dc_status_stage (
    stage_code       TEXT PRIMARY KEY,
    stage_label      TEXT NOT NULL,
    stage_order      INTEGER NOT NULL,
    counts_as_built  INTEGER NOT NULL CHECK (counts_as_built IN (0,1))
);
INSERT INTO dc_status_stage VALUES
 ('OPERATIONAL',       'A. 현재 운영 중', 1, 1),
 ('UNDER_CONSTRUCTION','B. 건설 중',      2, 0),
 ('APPROVED',          'C. 승인 완료',    3, 0),
 ('PLANNED',           'D. 계획 단계',    4, 0),
 ('ANNOUNCED',         'E. 발표만 된 프로젝트', 5, 0),
 ('CANCELLED',         'X. 취소/보류',    9, 0);

-- 데이터센터 수치 제공 벤더. 정의가 서로 다르므로 절대 합산하지 않는다.
CREATE TABLE dc_vendor (
    vendor_id        INTEGER PRIMARY KEY,
    vendor_name      TEXT NOT NULL UNIQUE,
    counting_unit    TEXT NOT NULL CHECK (counting_unit IN ('SITE','FACILITY','BUILDING','CAMPUS','HALL')),
    includes_stages  TEXT NOT NULL,   -- 콤마구분 stage_code
    definition_note  TEXT NOT NULL
);
INSERT INTO dc_vendor (vendor_id,vendor_name,counting_unit,includes_stages,definition_note) VALUES
 (1,'Aterio','FACILITY','OPERATIONAL,UNDER_CONSTRUCTION,ANNOUNCED',
    '활성 파이프라인 기준. 발표 단계까지 포함하여 카운트가 가장 큼'),
 (2,'DataCenterMap','FACILITY','OPERATIONAL,UNDER_CONSTRUCTION,APPROVED,PLANNED',
    '전 상태 시설 단위'),
 (3,'Statista','SITE','OPERATIONAL',
    '운영 중만, 사이트 단위. 카운트가 가장 작음'),
 (4,'CBRE','FACILITY','OPERATIONAL,UNDER_CONSTRUCTION',
    '시장(Market) 단위 인벤토리 MW 중심. 주 단위 아님에 주의'),
 (5,'EIA/LBNL','FACILITY','OPERATIONAL',
    '전력 소비(TWh) 기준. 시설 수 아님');

-- 튜닝 가능한 스코어링 가중치 (하드코딩 금지)
CREATE TABLE scoring_weight (
    scheme           TEXT NOT NULL,
    component        TEXT NOT NULL,
    weight           REAL NOT NULL,
    rationale        TEXT,
    updated_at       TEXT NOT NULL,
    PRIMARY KEY (scheme, component)
);
INSERT INTO scoring_weight VALUES
 ('SUPPORT_SCORE','GROWTH',0.30,'산업 유치 의지가 기본축','2026-08-27'),
 ('SUPPORT_SCORE','POWER', 0.15,'발전원 선호는 별도 필드로 분리 기록','2026-08-27'),
 ('SUPPORT_SCORE','RATES', 0.25,'2026 사이클의 실제 쟁점축','2026-08-27'),
 ('SUPPORT_SCORE','WATER', 0.10,'주별 편차 큼(서부 중심)','2026-08-27'),
 ('SUPPORT_SCORE','TAX',   0.20,'세제혜택 일몰이 직접적 재무영향','2026-08-27'),
 ('EXPOSURE','OPERATIONAL_MW',0.40,'스펙 §4','2026-08-27'),
 ('EXPOSURE','UNDER_CONSTRUCTION_MW',0.30,'스펙 §4','2026-08-27'),
 ('EXPOSURE','PLANNED_MW',0.20,'스펙 §4','2026-08-27'),
 ('EXPOSURE','FACILITY_COUNT',0.10,'스펙 §4','2026-08-27'),
 ('ELECTION_RISK','COMPETITIVE_RATIO',0.30,NULL,'2026-08-27'),
 ('ELECTION_RISK','GOV_FLIP',0.25,NULL,'2026-08-27'),
 ('ELECTION_RISK','TRIFECTA_BREAK',0.20,NULL,'2026-08-27'),
 ('ELECTION_RISK','OPEN_SEAT_RATIO',0.15,NULL,'2026-08-27'),
 ('ELECTION_RISK','POLL_VOLATILITY',0.10,NULL,'2026-08-27'),
 ('DC_POLICY_RISK','CANDIDATE_STANCE',0.25,NULL,'2026-08-27'),
 ('DC_POLICY_RISK','GRID_STRESS',0.20,NULL,'2026-08-27'),
 ('DC_POLICY_RISK','COMMUNITY_OPPOSITION',0.15,NULL,'2026-08-27'),
 ('DC_POLICY_RISK','TAX_INCENTIVE_RISK',0.15,NULL,'2026-08-27'),
 ('DC_POLICY_RISK','REGULATORY_PIPELINE',0.15,NULL,'2026-08-27'),
 ('DC_POLICY_RISK','WATER_STRESS',0.10,NULL,'2026-08-27'),
 ('OVERALL','ELECTION_RISK',0.45,'선거 불확실성','2026-08-27'),
 ('OVERALL','DC_POLICY_RISK',0.55,'양당 수렴 시 선거결과와 무관하게 규제 진행','2026-08-27');

-- ---------------------------------------------------------------------
-- TABLE 1 : STATE_POLITICAL_STRUCTURE
-- ---------------------------------------------------------------------

CREATE TABLE state_political_structure (
    state_code                TEXT PRIMARY KEY CHECK (length(state_code)=2),
    state_name                TEXT NOT NULL UNIQUE,
    population                INTEGER,
    population_source_id      INTEGER REFERENCES source(source_id),

    governor                  TEXT,
    governor_party            TEXT REFERENCES party(party_code),
    governor_term_end         TEXT,
    governor_election_2026    INTEGER CHECK (governor_election_2026 IN (0,1)),
    governor_term_limited     INTEGER CHECK (governor_term_limited IN (0,1)),

    state_senate_total        INTEGER,
    state_senate_democrat     INTEGER,
    state_senate_republican   INTEGER,
    state_senate_other        INTEGER,

    state_house_total         INTEGER,
    state_house_democrat      INTEGER,
    state_house_republican    INTEGER,
    state_house_other         INTEGER,

    federal_house_seats       INTEGER,
    federal_house_democrat    INTEGER,
    federal_house_republican  INTEGER,
    federal_house_vacant      INTEGER DEFAULT 0,

    federal_senate_seats      INTEGER DEFAULT 2,
    federal_senate_democrat   INTEGER,
    federal_senate_republican INTEGER,

    political_control         TEXT CHECK (political_control IN
                                ('Democratic Trifecta','Republican Trifecta','Divided Government')),
    -- 네브래스카는 단원제·비당파 의회 → 'Divided Government' 강제 대신 note 기록
    legislature_note          TEXT,

    status_code               TEXT NOT NULL DEFAULT 'NOT_YET_COLLECTED' REFERENCES status_code(status_code),
    source_id                 INTEGER REFERENCES source(source_id),
    last_updated              TEXT
);

-- ---------------------------------------------------------------------
-- TABLE 2 (정규화) : ELECTION_RACE  +  CANDIDATE  +  RACE_RATING
-- ---------------------------------------------------------------------

CREATE TABLE election_race (
    race_id              INTEGER PRIMARY KEY,
    state_code           TEXT NOT NULL REFERENCES state_political_structure(state_code),
    office               TEXT NOT NULL CHECK (office IN
                            ('U.S. Senate','U.S. House','Governor',
                             'State Senate','State House','Attorney General',
                             'Lieutenant Governor','Public Utility Commission')),
    district             TEXT,                 -- 상원/주지사는 NULL
    election_type        TEXT NOT NULL CHECK (election_type IN ('Regular','Special','Runoff')),
    senate_class         INTEGER CHECK (senate_class IN (1,2,3)),

    incumbent_name       TEXT,
    incumbent_party      TEXT REFERENCES party(party_code),
    incumbent_running    INTEGER CHECK (incumbent_running IN (0,1)),
    is_open_seat         INTEGER CHECK (is_open_seat IN (0,1)),
    open_seat_reason     TEXT CHECK (open_seat_reason IN
                            ('Retirement','Term Limited','Seeking Other Office',
                             'Resigned','Deceased','Primary Defeat','Not Open')),

    primary_date         TEXT,
    general_election_date TEXT NOT NULL DEFAULT '2026-11-03',

    winner_candidate_id  INTEGER,              -- 선거 후 채움
    winner_party         TEXT REFERENCES party(party_code),

    status_code          TEXT NOT NULL DEFAULT 'NOT_YET_COLLECTED' REFERENCES status_code(status_code),
    source_id            INTEGER REFERENCES source(source_id),
    last_updated         TEXT,
    UNIQUE (state_code, office, district, election_type)
);
CREATE INDEX ix_race_state ON election_race(state_code, office);

CREATE TABLE candidate (
    candidate_id         INTEGER PRIMARY KEY,
    race_id              INTEGER NOT NULL REFERENCES election_race(race_id),
    politician_id        INTEGER REFERENCES politician(politician_id),
    candidate_name       TEXT NOT NULL,
    candidate_party      TEXT NOT NULL REFERENCES party(party_code),
    is_incumbent         INTEGER NOT NULL DEFAULT 0 CHECK (is_incumbent IN (0,1)),
    current_position     TEXT,                 -- 현직 직함
    current_status       TEXT NOT NULL CHECK (current_status IN
                            ('Declared','Likely Candidate','Filed','Primary',
                             'Nominee','General Election','Withdrawn','Lost Primary','Won','Lost')),
    campaign_url         TEXT,
    status_code          TEXT NOT NULL DEFAULT 'OK' REFERENCES status_code(status_code),
    source_id            INTEGER REFERENCES source(source_id),
    last_updated         TEXT
);
CREATE INDEX ix_candidate_race ON candidate(race_id);

-- 등급 제공기관별 스냅샷. 이 테이블의 이력이 곧 RACE_RATING_CHANGE 추적 원천.
CREATE TABLE race_rating (
    rating_id            INTEGER PRIMARY KEY,
    race_id              INTEGER NOT NULL REFERENCES election_race(race_id),
    rater                TEXT NOT NULL CHECK (rater IN
                            ('Cook Political Report','Sabato Crystal Ball','Inside Elections',
                             'DDHQ','Almanac of American Politics','RacetotheWH','Other')),
    rating_code          TEXT NOT NULL REFERENCES race_rating_scale(rating_code),
    as_of_date           TEXT NOT NULL,
    source_id            INTEGER REFERENCES source(source_id),
    UNIQUE (race_id, rater, as_of_date)
);

CREATE TABLE polling (
    poll_id              INTEGER PRIMARY KEY,
    race_id              INTEGER NOT NULL REFERENCES election_race(race_id),
    pollster             TEXT NOT NULL,
    field_start          TEXT,
    field_end            TEXT NOT NULL,
    sample_size          INTEGER,
    population           TEXT CHECK (population IN ('RV','LV','A')),
    margin_d_minus_r     REAL,                 -- 양수=민주 우세
    is_average           INTEGER NOT NULL DEFAULT 0 CHECK (is_average IN (0,1)),
    polling_source       TEXT,
    source_id            INTEGER REFERENCES source(source_id)
);
CREATE INDEX ix_poll_race ON polling(race_id, field_end);

-- ---------------------------------------------------------------------
-- TABLE 3 (확장) : GOVERNOR_RACE_DETAIL
-- ---------------------------------------------------------------------

CREATE TABLE governor_race_detail (
    race_id                  INTEGER PRIMARY KEY REFERENCES election_race(race_id),
    current_governor         TEXT,
    current_party            TEXT REFERENCES party(party_code),
    term_limited             INTEGER CHECK (term_limited IN (0,1)),
    running_for_reelection   INTEGER CHECK (running_for_reelection IN (0,1)),
    -- flip 확률은 분석값이므로 Fact 테이블에 두지 않고 v_governor_flip_risk 뷰에서 산출
    dc_policy_relevance_note TEXT,
    status_code              TEXT NOT NULL DEFAULT 'NOT_YET_COLLECTED' REFERENCES status_code(status_code),
    source_id                INTEGER REFERENCES source(source_id),
    last_updated             TEXT
);

-- ---------------------------------------------------------------------
-- TABLE 4 (정규화) : DC_PROJECT + DC_VENDOR_COUNT + STATE_DC_CONTEXT
-- ---------------------------------------------------------------------

CREATE TABLE dc_project (
    project_id           INTEGER PRIMARY KEY,
    state_code           TEXT NOT NULL REFERENCES state_political_structure(state_code),
    county               TEXT,
    project_name         TEXT NOT NULL,
    primary_operator     TEXT,                 -- AWS/Microsoft/Google/Meta/Oracle/CoreWeave/xAI/Equinix/...
    other_operators      TEXT,
    is_hyperscale        INTEGER CHECK (is_hyperscale IN (0,1)),

    stage_code           TEXT NOT NULL REFERENCES dc_status_stage(stage_code),
    stage_as_of          TEXT NOT NULL,

    capacity_mw          REAL,                 -- IT 부하 기준. 불명 시 NULL
    capacity_basis       TEXT CHECK (capacity_basis IN ('IT_LOAD','GROSS','UTILITY_CONTRACT','UNKNOWN')),
    sqft                 REAL,
    investment_usd       REAL,
    announced_date       TEXT,
    target_online_date   TEXT,

    water_usage_note     TEXT,
    cooling_type         TEXT CHECK (cooling_type IN ('Air','Evaporative','Closed-loop','Liquid','Hybrid','Unknown')),

    status_code          TEXT NOT NULL DEFAULT 'OK' REFERENCES status_code(status_code),
    source_id            INTEGER NOT NULL REFERENCES source(source_id),
    last_updated         TEXT NOT NULL
);
CREATE INDEX ix_dcproj_state ON dc_project(state_code, stage_code);

-- 프로젝트 상태 전이 이력 (계획→건설→운영). change_log와 연동
CREATE TABLE dc_project_stage_history (
    history_id           INTEGER PRIMARY KEY,
    project_id           INTEGER NOT NULL REFERENCES dc_project(project_id),
    from_stage           TEXT REFERENCES dc_status_stage(stage_code),
    to_stage             TEXT NOT NULL REFERENCES dc_status_stage(stage_code),
    changed_at           TEXT NOT NULL,
    source_id            INTEGER REFERENCES source(source_id)
);

-- 벤더별 주 단위 집계치를 원문 그대로 병렬 보존 (P4)
CREATE TABLE dc_vendor_count (
    vendor_id            INTEGER NOT NULL REFERENCES dc_vendor(vendor_id),
    state_code           TEXT NOT NULL REFERENCES state_political_structure(state_code),
    snapshot_date        TEXT NOT NULL,
    operational_count    INTEGER,
    under_construction_count INTEGER,
    approved_count       INTEGER,
    planned_count        INTEGER,
    announced_count      INTEGER,
    total_count          INTEGER,
    hyperscale_count     INTEGER,
    operational_mw       REAL,
    under_construction_mw REAL,
    planned_mw           REAL,
    total_pipeline_mw    REAL,
    annual_twh           REAL,
    status_code          TEXT NOT NULL DEFAULT 'OK' REFERENCES status_code(status_code),
    source_id            INTEGER NOT NULL REFERENCES source(source_id),
    PRIMARY KEY (vendor_id, state_code, snapshot_date)
);

-- 벤더 수치로 대체 불가능한 주 단위 정성/정책 컨텍스트
CREATE TABLE state_dc_context (
    state_code               TEXT PRIMARY KEY REFERENCES state_political_structure(state_code),
    tax_incentive_summary    TEXT,
    tax_incentive_type       TEXT,   -- 'Sales Tax Exemption','Property Tax Abatement','Both','None'
    tax_incentive_sunset     TEXT,   -- 일몰/재심의 예정일
    tax_incentive_value_usd  REAL,
    electricity_rate_change_pct REAL,-- 최근 12개월 주거용 요금 변동률
    grid_operator            TEXT,   -- PJM/ERCOT/MISO/SPP/CAISO/...
    grid_stress_level        TEXT CHECK (grid_stress_level IN ('Low','Moderate','High','Severe','Unknown')),
    water_stress_level       TEXT CHECK (water_stress_level IN ('Low','Moderate','High','Extreme','Unknown')),
    local_moratorium_count   INTEGER,
    community_opposition_level TEXT CHECK (community_opposition_level IN ('Low','Moderate','High','Severe','Unknown')),
    dc_share_of_state_power_pct REAL,
    pending_legislation_count INTEGER,
    status_code              TEXT NOT NULL DEFAULT 'NOT_YET_COLLECTED' REFERENCES status_code(status_code),
    source_id                INTEGER REFERENCES source(source_id),
    last_updated             TEXT
);

-- ---------------------------------------------------------------------
-- TABLE 5 : POLITICIAN + POSITION + EVIDENCE + AXIS  (핵심 테이블)
-- ---------------------------------------------------------------------

CREATE TABLE politician (
    politician_id        INTEGER PRIMARY KEY,
    full_name            TEXT NOT NULL,
    party                TEXT NOT NULL REFERENCES party(party_code),
    state_code           TEXT REFERENCES state_political_structure(state_code),
    current_office       TEXT,
    district             TEXT,
    bioguide_id          TEXT,                 -- 연방 의원 식별자
    photo_url            TEXT,
    official_url         TEXT,
    last_updated         TEXT
);

CREATE TABLE politician_dc_position (
    position_id          INTEGER PRIMARY KEY,
    politician_id        INTEGER NOT NULL REFERENCES politician(politician_id),
    race_id              INTEGER REFERENCES election_race(race_id),
    candidate_status     TEXT CHECK (candidate_status IN
                            ('Incumbent Running','Incumbent Retiring','Challenger',
                             'Open Seat Candidate','Not On Ballot')),

    dc_position          TEXT NOT NULL CHECK (dc_position IN
                            ('Strongly Supportive','Supportive','Neutral / No Clear Position',
                             'Mixed','Concerned','Restrictive','Strongly Opposed',
                             'No Clear Public Position')),
    -- support_score 는 저장하지 않는다. position_axis_score 로부터 뷰에서 계산한다.

    power_source_pref    TEXT,                 -- 'Nuclear,Natural Gas' 등 다중
    policy_statement     TEXT,                 -- 실제 발언/공약 요약 (짧게)
    confidence_level     TEXT NOT NULL CHECK (confidence_level IN ('High','Medium','Low')),
    data_type            TEXT NOT NULL DEFAULT 'Fact' CHECK (data_type IN ('Fact','AI Analysis')),
    status_code          TEXT NOT NULL DEFAULT 'OK' REFERENCES status_code(status_code),
    last_updated         TEXT NOT NULL
);
CREATE INDEX ix_position_pol ON politician_dc_position(politician_id);

-- P3 : 근거 레코드. 최소 1건 없으면 position 은 유효하지 않다.
CREATE TABLE position_evidence (
    evidence_id          INTEGER PRIMARY KEY,
    position_id          INTEGER NOT NULL REFERENCES politician_dc_position(position_id),
    evidence_type        TEXT NOT NULL CHECK (evidence_type IN
                            ('Public statement','Campaign promise','Introduced bill',
                             'Voted for','Voted against','Signed bill','Vetoed bill',
                             'Supported legislation','Opposed legislation',
                             'Interview','Press release','Campaign ad','Executive order')),
    -- 'Party affiliation' 은 의도적으로 허용하지 않는다 (스펙 §10)
    summary              TEXT NOT NULL,
    bill_number          TEXT,
    evidence_date        TEXT NOT NULL,
    source_id            INTEGER NOT NULL REFERENCES source(source_id)
);
CREATE INDEX ix_evidence_pos ON position_evidence(position_id);

CREATE TABLE position_axis_score (
    position_id          INTEGER NOT NULL REFERENCES politician_dc_position(position_id),
    axis_code            TEXT NOT NULL CHECK (axis_code IN ('GROWTH','POWER','RATES','WATER','TAX')),
    axis_score           INTEGER CHECK (axis_score BETWEEN -100 AND 100),  -- NULL 허용 = 입장 불명
    axis_rationale       TEXT,
    evidence_id          INTEGER REFERENCES position_evidence(evidence_id),  -- 근거 연결
    status_code          TEXT NOT NULL DEFAULT 'OK' REFERENCES status_code(status_code),
    PRIMARY KEY (position_id, axis_code)
);

CREATE TABLE position_policy_category (
    position_id          INTEGER NOT NULL REFERENCES politician_dc_position(position_id),
    category_id          INTEGER NOT NULL REFERENCES policy_category(category_id),
    PRIMARY KEY (position_id, category_id)
);

-- 근거 없는 점수 입력 차단
CREATE TRIGGER trg_axis_requires_evidence
BEFORE INSERT ON position_axis_score
FOR EACH ROW
WHEN NEW.axis_score IS NOT NULL
     AND (SELECT COUNT(*) FROM position_evidence WHERE position_id = NEW.position_id) = 0
BEGIN
    SELECT RAISE(ABORT, 'P3 violation: axis_score requires at least one position_evidence row');
END;

-- ---------------------------------------------------------------------
-- TABLE 6 : DC_ELECTION_RISK  (파생. data_type 강제)
-- ---------------------------------------------------------------------

CREATE TABLE dc_election_risk (
    state_code                    TEXT PRIMARY KEY REFERENCES state_political_structure(state_code),
    computed_at                   TEXT NOT NULL,
    data_type                     TEXT NOT NULL DEFAULT 'AI Analysis'
                                    CHECK (data_type = 'AI Analysis'),

    current_political_control     TEXT,
    election_exposure_2026        REAL,   -- 0-100
    data_center_importance        REAL,
    data_center_growth            REAL,
    political_uncertainty         REAL,
    community_opposition          REAL,
    electricity_stress            REAL,
    water_stress                  REAL,
    tax_incentive_risk            REAL,
    regulatory_risk               REAL,

    election_risk_score           REAL CHECK (election_risk_score BETWEEN 0 AND 100),
    dc_policy_risk_score          REAL CHECK (dc_policy_risk_score BETWEEN 0 AND 100),
    overall_dc_political_risk     REAL CHECK (overall_dc_political_risk BETWEEN 0 AND 100),

    bipartisan_convergence_flag   INTEGER CHECK (bipartisan_convergence_flag IN (0,1)),
    coverage_pct                  REAL,   -- 입력 데이터 충족률. 60 미만이면 점수 미표시
    input_source_ids              TEXT,   -- 계산에 사용된 source_id 목록
    status_code                   TEXT NOT NULL DEFAULT 'NOT_YET_COLLECTED' REFERENCES status_code(status_code),
    method_version                TEXT NOT NULL
);

-- ---------------------------------------------------------------------
-- SCENARIO (§5) — 근거 없는 시나리오 저장 금지
-- ---------------------------------------------------------------------

CREATE TABLE scenario (
    scenario_id              INTEGER PRIMARY KEY,
    state_code               TEXT NOT NULL REFERENCES state_political_structure(state_code),
    scenario_code            TEXT NOT NULL CHECK (scenario_code IN ('A_D_HOLD','B_R_WIN','C_CONTROL_FLIP')),
    scenario_label           TEXT NOT NULL,
    probability_note         TEXT,

    dc_expansion_impact      TEXT,
    electricity_policy_impact TEXT,
    tax_incentive_impact     TEXT,
    water_regulation_impact  TEXT,
    community_opposition_impact TEXT,
    overall_risk_direction   TEXT CHECK (overall_risk_direction IN
                                ('Sharply Lower','Lower','Neutral','Higher','Sharply Higher',
                                 'INSUFFICIENT_EVIDENCE')),

    driver_evidence_ids      TEXT NOT NULL,   -- position_evidence.evidence_id 배열. 빈 값이면 아래 트리거가 차단
    data_type                TEXT NOT NULL DEFAULT 'AI Analysis' CHECK (data_type='AI Analysis'),
    computed_at              TEXT NOT NULL,
    UNIQUE (state_code, scenario_code)
);

CREATE TRIGGER trg_scenario_requires_evidence
BEFORE INSERT ON scenario
FOR EACH ROW
WHEN (NEW.driver_evidence_ids IS NULL OR trim(NEW.driver_evidence_ids) = '')
     AND NEW.overall_risk_direction <> 'INSUFFICIENT_EVIDENCE'
BEGIN
    SELECT RAISE(ABORT, 'Scenario requires driver_evidence_ids or must be INSUFFICIENT_EVIDENCE');
END;

-- ---------------------------------------------------------------------
-- CHANGE LOG (§8)
-- ---------------------------------------------------------------------

CREATE TABLE change_log (
    change_id            INTEGER PRIMARY KEY,
    event_type           TEXT NOT NULL CHECK (event_type IN
                            ('NEW_CANDIDATE','CANDIDATE_WITHDRAWAL','POLLING_CHANGE',
                             'RACE_RATING_CHANGE','GOVERNOR_ELECTION_CHANGE',
                             'NEW_DC_ANNOUNCEMENT','DC_CANCELLATION','NEW_LEGISLATION',
                             'TAX_INCENTIVE_CHANGE','ELECTRICITY_RATE_CHANGE',
                             'COMMUNITY_OPPOSITION','WATER_REGULATION','DC_STAGE_TRANSITION')),
    state_code           TEXT REFERENCES state_political_structure(state_code),
    target_table         TEXT NOT NULL,
    target_pk            TEXT NOT NULL,
    field_name           TEXT,
    old_value            TEXT,
    new_value            TEXT,
    changed_at           TEXT NOT NULL,
    source_id            INTEGER REFERENCES source(source_id),
    note                 TEXT
);
CREATE INDEX ix_changelog_time ON change_log(changed_at DESC);

CREATE TRIGGER trg_rating_change_log
AFTER INSERT ON race_rating
FOR EACH ROW
BEGIN
    INSERT INTO change_log (event_type, state_code, target_table, target_pk,
                            field_name, old_value, new_value, changed_at, source_id)
    SELECT 'RACE_RATING_CHANGE',
           (SELECT state_code FROM election_race WHERE race_id = NEW.race_id),
           'race_rating', CAST(NEW.race_id AS TEXT), NEW.rater,
           (SELECT rating_code FROM race_rating r2
             WHERE r2.race_id = NEW.race_id AND r2.rater = NEW.rater
               AND r2.as_of_date < NEW.as_of_date
             ORDER BY r2.as_of_date DESC LIMIT 1),
           NEW.rating_code, NEW.as_of_date, NEW.source_id
    WHERE EXISTS (SELECT 1 FROM race_rating r3
                   WHERE r3.race_id = NEW.race_id AND r3.rater = NEW.rater
                     AND r3.as_of_date < NEW.as_of_date
                     AND r3.rating_code <> NEW.rating_code);
END;

CREATE TRIGGER trg_dc_stage_log
AFTER INSERT ON dc_project_stage_history
FOR EACH ROW
BEGIN
    INSERT INTO change_log (event_type, state_code, target_table, target_pk,
                            field_name, old_value, new_value, changed_at, source_id)
    VALUES ('DC_STAGE_TRANSITION',
            (SELECT state_code FROM dc_project WHERE project_id = NEW.project_id),
            'dc_project', CAST(NEW.project_id AS TEXT), 'stage_code',
            NEW.from_stage, NEW.to_stage, NEW.changed_at, NEW.source_id);
END;

-- =====================================================================
-- DERIVED VIEWS
-- =====================================================================

-- Data Center Support Score (-100 ~ +100). 축 3개 이상 NULL 이면 NULL.
CREATE VIEW v_support_score AS
SELECT
    p.position_id,
    p.politician_id,
    pol.full_name,
    pol.party,
    pol.state_code,
    p.dc_position,
    CASE WHEN SUM(CASE WHEN a.axis_score IS NULL THEN 1 ELSE 0 END) >= 3
         THEN NULL
         ELSE ROUND( SUM(a.axis_score * w.weight) / NULLIF(SUM(CASE WHEN a.axis_score IS NOT NULL
                                                                   THEN w.weight END),0), 1)
    END AS support_score,
    SUM(CASE WHEN a.axis_score IS NOT NULL THEN 1 ELSE 0 END) AS axes_scored,
    (SELECT COUNT(*) FROM position_evidence e WHERE e.position_id = p.position_id) AS evidence_count,
    p.confidence_level,
    p.last_updated
FROM politician_dc_position p
JOIN politician pol       ON pol.politician_id = p.politician_id
LEFT JOIN position_axis_score a ON a.position_id = p.position_id
LEFT JOIN scoring_weight w      ON w.scheme = 'SUPPORT_SCORE' AND w.component = a.axis_code
GROUP BY p.position_id;

-- 원본 스펙 TABLE 2 형태 복원
CREATE VIEW v_election_tracker AS
SELECT r.state_code AS State, r.office AS Office, r.district AS District,
       c.candidate_name AS Candidate_Name, c.candidate_party AS Candidate_Party,
       CASE c.is_incumbent WHEN 1 THEN 'Yes' ELSE 'No' END AS Incumbent,
       r.election_type AS Election_Type, r.primary_date AS Primary_Date,
       r.general_election_date AS General_Election_Date,
       c.current_status AS Current_Status,
       (SELECT s.rating_label FROM race_rating rr
          JOIN race_rating_scale s ON s.rating_code = rr.rating_code
         WHERE rr.race_id = r.race_id AND rr.rater='Cook Political Report'
         ORDER BY rr.as_of_date DESC LIMIT 1) AS Seat_Status,
       (SELECT pl.margin_d_minus_r FROM polling pl
         WHERE pl.race_id = r.race_id AND pl.is_average=1
         ORDER BY pl.field_end DESC LIMIT 1) AS Polling_Average,
       c.last_updated AS Last_Updated
FROM election_race r LEFT JOIN candidate c ON c.race_id = r.race_id;

-- 주별 2026 선거 노출도 6개 지표 (스펙 TABLE 2 하단 요구사항)
CREATE VIEW v_state_election_exposure AS
SELECT r.state_code,
       SUM(CASE WHEN r.incumbent_party='D' AND r.incumbent_running=1 THEN 1 ELSE 0 END) AS dem_incumbents_up,
       SUM(CASE WHEN r.incumbent_party='R' AND r.incumbent_running=1 THEN 1 ELSE 0 END) AS gop_incumbents_up,
       SUM(CASE WHEN r.is_open_seat=1 THEN 1 ELSE 0 END)                                AS open_seats,
       SUM(CASE WHEN r.open_seat_reason IN ('Retirement','Term Limited') THEN 1 ELSE 0 END) AS retirements,
       SUM(CASE WHEN (SELECT s.competitiveness FROM race_rating rr
                        JOIN race_rating_scale s ON s.rating_code=rr.rating_code
                       WHERE rr.race_id=r.race_id ORDER BY rr.as_of_date DESC LIMIT 1) >= 65
                THEN 1 ELSE 0 END)                                                      AS competitive_races,
       SUM(CASE WHEN (SELECT rr.rating_code FROM race_rating rr
                       WHERE rr.race_id=r.race_id ORDER BY rr.as_of_date DESC LIMIT 1)='TOSSUP'
                THEN 1 ELSE 0 END)                                                      AS tossup_races,
       COUNT(*) AS total_races_2026
FROM election_race r
WHERE r.general_election_date LIKE '2026%'
GROUP BY r.state_code;

-- 데이터센터 집계 (프로젝트 원장 기준). 벤더 수치와 구분됨에 유의.
CREATE VIEW v_data_center_footprint AS
SELECT d.state_code,
       SUM(CASE WHEN stage_code='OPERATIONAL'        THEN 1 ELSE 0 END) AS operational_count,
       SUM(CASE WHEN stage_code='UNDER_CONSTRUCTION' THEN 1 ELSE 0 END) AS under_construction_count,
       SUM(CASE WHEN stage_code='APPROVED'           THEN 1 ELSE 0 END) AS approved_count,
       SUM(CASE WHEN stage_code='PLANNED'            THEN 1 ELSE 0 END) AS planned_count,
       SUM(CASE WHEN stage_code='ANNOUNCED'          THEN 1 ELSE 0 END) AS announced_count,
       SUM(CASE WHEN is_hyperscale=1                 THEN 1 ELSE 0 END) AS hyperscale_count,
       SUM(CASE WHEN stage_code='OPERATIONAL'        THEN capacity_mw END) AS operational_mw,
       SUM(CASE WHEN stage_code='UNDER_CONSTRUCTION' THEN capacity_mw END) AS under_construction_mw,
       SUM(CASE WHEN stage_code IN ('APPROVED','PLANNED','ANNOUNCED') THEN capacity_mw END) AS planned_mw,
       SUM(investment_usd) AS investment_usd,
       COUNT(*) AS total_tracked_projects,
       ROUND(100.0 * SUM(CASE WHEN capacity_mw IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS mw_coverage_pct
FROM dc_project d
WHERE stage_code <> 'CANCELLED'
GROUP BY d.state_code;

-- Exposure Score. 로그 정규화 (max 정규화 시 TX 편중으로 변별력 소실)
CREATE VIEW v_dc_exposure_score AS
WITH m AS (
    SELECT MAX(COALESCE(operational_mw,0))        AS max_op,
           MAX(COALESCE(under_construction_mw,0)) AS max_uc,
           MAX(COALESCE(planned_mw,0))            AS max_pl,
           MAX(total_tracked_projects)            AS max_ct
    FROM v_data_center_footprint
)
SELECT f.state_code,
       ROUND(
         0.40 * 100.0*log(1+COALESCE(f.operational_mw,0))        / NULLIF(log(1+m.max_op),0)
       + 0.30 * 100.0*log(1+COALESCE(f.under_construction_mw,0)) / NULLIF(log(1+m.max_uc),0)
       + 0.20 * 100.0*log(1+COALESCE(f.planned_mw,0))            / NULLIF(log(1+m.max_pl),0)
       + 0.10 * 100.0*log(1+f.total_tracked_projects)            / NULLIF(log(1+m.max_ct),0)
       , 1) AS exposure_score_log,
       ROUND(100.0*f.operational_mw / NULLIF((SELECT SUM(operational_mw) FROM v_data_center_footprint),0),2)
         AS operational_mw_share_pct,
       ROUND(100.0*(COALESCE(f.under_construction_mw,0)+COALESCE(f.planned_mw,0))
             / NULLIF((SELECT SUM(COALESCE(under_construction_mw,0)+COALESCE(planned_mw,0))
                       FROM v_data_center_footprint),0),2) AS future_mw_share_pct,
       f.mw_coverage_pct,
       'AI Analysis' AS data_type
FROM v_data_center_footprint f CROSS JOIN m;

-- 양당 수렴 플래그: 해당 주 주요 레이스에서 양당 후보 support_score 가 모두 음수
CREATE VIEW v_bipartisan_convergence AS
SELECT r.state_code,
       MAX(CASE WHEN c.candidate_party='D' THEN v.support_score END) AS dem_score,
       MAX(CASE WHEN c.candidate_party='R' THEN v.support_score END) AS gop_score,
       CASE WHEN MAX(CASE WHEN c.candidate_party='D' THEN v.support_score END) < 0
             AND MAX(CASE WHEN c.candidate_party='R' THEN v.support_score END) < 0
            THEN 1 ELSE 0 END AS bipartisan_convergence_flag
FROM election_race r
JOIN candidate c ON c.race_id = r.race_id
JOIN v_support_score v ON v.politician_id = c.politician_id
WHERE r.office IN ('U.S. Senate','Governor')
GROUP BY r.state_code;

-- 데이터 커버리지 감사 뷰. 수집 진행률 모니터링용.
CREATE VIEW v_coverage_audit AS
SELECT s.state_code,
       CASE WHEN sps.status_code='OK' THEN 1 ELSE 0 END AS political_structure_ok,
       (SELECT COUNT(*) FROM election_race r WHERE r.state_code=s.state_code)   AS races_loaded,
       (SELECT COUNT(*) FROM dc_project d   WHERE d.state_code=s.state_code)    AS dc_projects_loaded,
       (SELECT COUNT(*) FROM politician p   WHERE p.state_code=s.state_code)    AS politicians_loaded,
       (SELECT COUNT(*) FROM politician_dc_position pp
          JOIN politician p2 ON p2.politician_id=pp.politician_id
         WHERE p2.state_code=s.state_code)                                      AS positions_loaded
FROM state_political_structure s
JOIN state_political_structure sps ON sps.state_code=s.state_code;
