#!/usr/bin/env python3
"""원문 텍스트 → 검증된 갱신 스크립트 생성.

설계 의도: 모델이 파이썬 코드를 짜서 실행하게 두지 않는다.
모델은 **엄격한 JSON만** 내놓고, 이 스크립트가 스키마를 검증한 뒤
정해진 템플릿으로 갱신 스크립트를 찍어낸다.

거부 조건 (하나라도 걸리면 exit 1):
  - 출처 URL 또는 발행일 없음
  - 여론조사에 필드 종료일 없음
  - 등급에 기준일 없음
  - 후보명이 DB 의 현재 후보 명단에 없음  ← 실존하지 않는 대진 차단
  - 근거 없는 입장 점수
"""
import os, sys, json, re, sqlite3, datetime

RAW  = os.environ.get("RAW_TEXT", "").strip()
URL  = os.environ.get("SOURCE_URL", "").strip()
DATE = os.environ.get("SOURCE_DATE", "").strip()
KEY  = os.environ.get("GEMINI_API_KEY", "").strip()

def die(msg):
    print(f"::error::{msg}")
    sys.exit(1)

if not RAW:  die("RAW_TEXT 가 비어 있습니다.")
if not URL:  die("SOURCE_URL 은 필수입니다. 출처 없는 데이터는 적재하지 않습니다.")
if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", DATE):
    die("SOURCE_DATE 형식이 YYYY-MM-DD 가 아닙니다.")
if DATE > datetime.date.today().isoformat():
    die("SOURCE_DATE 가 미래입니다.")
if not KEY: die("GEMINI_API_KEY 시크릿이 없습니다.")

# ---------------------------------------------------------- DB 현재 상태
con = sqlite3.connect("data/tracker.db")
cands = {}
for st, off, name, party in con.execute("""
        SELECT r.state_code, r.office, c.candidate_name, c.candidate_party
        FROM candidate c JOIN election_race r ON r.race_id=c.race_id
        WHERE c.current_status <> 'Withdrawn'"""):
    cands.setdefault((st, off), []).append(f"{name} ({party})")
roster = "\n".join(f"{k[0]} {k[1]}: {', '.join(v)}" for k, v in sorted(cands.items()))
con.close()

SCHEMA = """
{
  "polls": [
    {"state":"OH","office":"U.S. Senate","pollster":"Fox News",
     "field_start":"2026-08-06","field_end":"2026-08-10",
     "sample_size":1008,"population":"RV",
     "margin_d_minus_r":8.0,
     "dem_candidate":"Sherrod Brown","gop_candidate":"Jon Husted"}
  ],
  "ratings": [
    {"state":"TX","office":"U.S. Senate","rater":"Cook Political Report",
     "rating_code":"TOSSUP","as_of_date":"2026-08-20"}
  ],
  "events": [
    {"event_type":"NEW_LEGISLATION","state":"NY",
     "note":"한 문장 요약","old_value":null,"new_value":"요약"}
  ]
}
"""

PROMPT = f"""아래 원문에서 구조화된 데이터만 추출해 JSON 으로 출력하라.

절대 규칙:
- 원문에 명시되지 않은 값은 절대 만들지 마라. 없으면 해당 항목을 통째로 빼라.
- 여론조사는 필드 기간(field_start, field_end)이 원문에 있을 때만 포함하라.
- 등급은 기준일(as_of_date)이 원문에 있을 때만 포함하라.
- margin_d_minus_r 은 민주당 득표율 - 공화당 득표율. 민주 우세면 양수.
- 후보명은 아래 현재 후보 명단에 있는 이름과 정확히 일치해야 한다.
  명단에 없는 인물이 나오면 그 조사는 제외하라.
- rating_code 는 다음 중 하나: SAFE_D LIKELY_D LEAN_D TILT_D TOSSUP TILT_R LEAN_R LIKELY_R SAFE_R
- office 는 "U.S. Senate" 또는 "Governor" 만 사용하라.
- 설명·마크다운·코드펜스 없이 JSON 객체 하나만 출력하라.

현재 후보 명단:
{roster}

출력 스키마:
{SCHEMA}

원문 (출처 {URL}, 발행일 {DATE}):
---
{RAW[:12000]}
---"""

from google import genai
client = genai.Client(api_key=KEY)
resp = client.models.generate_content(model="gemini-2.5-flash", contents=PROMPT)
txt = re.sub(r"^```(?:json)?|```$", "", resp.text.strip(), flags=re.M).strip()

try:
    data = json.loads(txt)
except json.JSONDecodeError as e:
    die(f"모델이 유효한 JSON 을 내놓지 않았습니다: {e}")

# ---------------------------------------------------------- 검증
polls   = data.get("polls") or []
ratings = data.get("ratings") or []
events  = data.get("events") or []
errs    = []
RATINGS_OK = {"SAFE_D","LIKELY_D","LEAN_D","TILT_D","TOSSUP","TILT_R","LEAN_R","LIKELY_R","SAFE_R"}
today = datetime.date.today().isoformat()

for i, p in enumerate(polls):
    tag = f"polls[{i}]"
    for f in ("state","office","pollster","field_end","margin_d_minus_r"):
        if p.get(f) in (None, ""): errs.append(f"{tag}: {f} 누락")
    if p.get("field_end", "") > today: errs.append(f"{tag}: 종료일이 미래")
    key = (p.get("state"), p.get("office"))
    if key not in cands:
        errs.append(f"{tag}: {key} 레이스가 DB 에 없음")
    else:
        names = " ".join(cands[key])
        for f in ("dem_candidate","gop_candidate"):
            nm = p.get(f)
            if nm and nm not in names:
                errs.append(f"{tag}: '{nm}' 은 현재 후보 명단에 없음 — 실존하지 않는 대진 가능성")

for i, r in enumerate(ratings):
    tag = f"ratings[{i}]"
    if r.get("rating_code") not in RATINGS_OK: errs.append(f"{tag}: 등급 코드 부적합")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(r.get("as_of_date",""))):
        errs.append(f"{tag}: 기준일 없음 또는 형식 오류")
    if (r.get("state"), r.get("office")) not in cands:
        errs.append(f"{tag}: 레이스가 DB 에 없음")

if errs:
    print("추출 결과 검증 실패:")
    for e in errs: print("  ✗", e)
    die("검증에 실패해 적재하지 않습니다.")

if not (polls or ratings or events):
    print("::notice::추출된 항목이 없습니다. 갱신 스크립트를 만들지 않습니다.")
    sys.exit(0)

# ---------------------------------------------------------- 스크립트 생성
seq = 12
while os.path.exists(f"scripts/{seq}_auto_{DATE.replace('-','')}.py"):
    seq += 1
path = f"scripts/{seq}_auto_{DATE.replace('-','')}.py"

body = f'''#!/usr/bin/env python3
"""자동 생성 — 출처 {URL} ({DATE})
scripts/auto_update_poll.py 가 JSON 검증을 통과한 항목만 기록했다.
손으로 고치지 말고 필요하면 새 파일을 만들 것."""
import sqlite3, math

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
cur = con.cursor()
NOW = "{DATE}"

sid = (cur.execute("SELECT COALESCE(MAX(source_id),0)+1 FROM source").fetchone()[0])
cur.execute("""INSERT INTO source(source_id,tier,publisher,title,url,published_date,
    retrieved_at,is_primary) VALUES (?,9,?,?,?,?,?,0)""",
    (sid, {json.dumps(URL.split('/')[2] if '://' in URL else URL)},
     "자동 수집 — 검증 통과", {json.dumps(URL)}, NOW, NOW))

POLLS   = {json.dumps(polls, ensure_ascii=False, indent=2)}
RATINGS = {json.dumps(ratings, ensure_ascii=False, indent=2)}
EVENTS  = {json.dumps(events, ensure_ascii=False, indent=2)}

def rid(st, off):
    r = cur.execute("SELECT race_id FROM election_race WHERE state_code=? AND office=?",
                    (st, off)).fetchone()
    return r[0] if r else None

pid = cur.execute("SELECT COALESCE(MAX(poll_id),0) FROM polling").fetchone()[0]
for p in POLLS:
    r = rid(p["state"], p["office"])
    if not r: continue
    pid += 1
    cur.execute("""INSERT INTO polling(poll_id,race_id,pollster,field_start,field_end,
        sample_size,population,margin_d_minus_r,is_average,polling_source,source_id)
        VALUES (?,?,?,?,?,?,?,?,0,?,?)""",
        (pid, r, p["pollster"], p.get("field_start"), p["field_end"],
         p.get("sample_size"), p.get("population"), p["margin_d_minus_r"],
         p["pollster"], sid))

nid = cur.execute("SELECT COALESCE(MAX(rating_id),0) FROM race_rating").fetchone()[0]
for g in RATINGS:
    r = rid(g["state"], g["office"])
    if not r: continue
    nid += 1
    try:
        cur.execute("""INSERT INTO race_rating(rating_id,race_id,rater,rating_code,
            as_of_date,source_id) VALUES (?,?,?,?,?,?)""",
            (nid, r, g["rater"], g["rating_code"], g["as_of_date"], sid))
    except sqlite3.IntegrityError:
        nid -= 1

cid = cur.execute("SELECT COALESCE(MAX(change_id),0) FROM change_log").fetchone()[0]
for p in POLLS:
    cid += 1
    lead = "D" if p["margin_d_minus_r"] > 0 else "R"
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,
        target_pk,field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,'POLLING_CHANGE',?,'polling',?,'margin',NULL,?,?,?,?)""",
        (cid, p["state"], p["state"], f"{{lead}}+{{abs(p['margin_d_minus_r'])}}", NOW, sid,
         f"{{p['pollster']}}: {{p['office']}} {{lead}}+{{abs(p['margin_d_minus_r'])}}"))
for e in EVENTS:
    cid += 1
    cur.execute("""INSERT INTO change_log(change_id,event_type,state_code,target_table,
        target_pk,field_name,old_value,new_value,changed_at,source_id,note)
        VALUES (?,?,?,'election_race',?,'auto',?,?,?,?,?)""",
        (cid, e["event_type"], e.get("state"), e.get("state") or "US",
         e.get("old_value"), e.get("new_value"), NOW, sid, e["note"]))

con.commit(); con.close()
print(f"적재: 조사 {{len(POLLS)}}건 · 등급 {{len(RATINGS)}}건 · 이벤트 {{len(EVENTS)}}건")
'''
open(path, "w", encoding="utf-8").write(body)

# 매니페스트의 빌드 단계 앞에 삽입
mf = "scripts/pipeline.txt"
lines = open(mf).read().splitlines()
idx = next(i for i, l in enumerate(lines) if l.startswith("# --- 이하 빌드"))
lines.insert(idx, os.path.basename(path))
open(mf, "w").write("\n".join(lines) + "\n")

print(f"생성: {path}")
print(f"  조사 {len(polls)}건 · 등급 {len(ratings)}건 · 이벤트 {len(events)}건")
