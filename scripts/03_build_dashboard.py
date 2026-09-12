#!/usr/bin/env python3
"""tracker.db -> 단일 파일 인터랙티브 대시보드 (STEP 2·3 기준)."""
import sqlite3, math, json

con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
con.row_factory = sqlite3.Row
cur = con.cursor()

TILE = {  # (row, col) — US tile cartogram
 "AK":(0,0),"ME":(0,10),
 "VT":(1,9),"NH":(1,10),
 "WA":(2,0),"ID":(2,1),"MT":(2,2),"ND":(2,3),"MN":(2,4),"IL":(2,5),"WI":(2,6),
 "MI":(2,7),"NY":(2,8),"MA":(2,9),"RI":(2,10),
 "OR":(3,0),"NV":(3,1),"WY":(3,2),"SD":(3,3),"IA":(3,4),"IN":(3,5),"OH":(3,6),
 "PA":(3,7),"NJ":(3,8),"CT":(3,9),
 "CA":(4,0),"UT":(4,1),"CO":(4,2),"NE":(4,3),"MO":(4,4),"KY":(4,5),"WV":(4,6),
 "VA":(4,7),"MD":(4,8),"DE":(4,9),
 "AZ":(5,1),"NM":(5,2),"KS":(5,3),"AR":(5,4),"TN":(5,5),"NC":(5,6),"SC":(5,7),
 "OK":(6,3),"LA":(6,4),"MS":(6,5),"AL":(6,6),"GA":(6,7),
 "HI":(7,0),"TX":(7,3),"FL":(7,8),
}

states = {}
for r in cur.execute("SELECT * FROM state_political_structure ORDER BY state_code").fetchall():
    d = dict(r)
    d["tile"] = TILE[d["state_code"]]
    d["races"] = []
    d["dc_vendor"] = []
    states[d["state_code"]] = d

RATER_SHORT = {"Cook Political Report":"Cook","Sabato Crystal Ball":"Sabato",
               "Almanac of American Politics":"Almanac","Inside Elections":"Inside"}

# 주의: 같은 커서를 루프 안에서 재실행하면 바깥 반복이 끊긴다. 먼저 전량 fetch 한다.
races_rows = cur.execute("SELECT * FROM election_race ORDER BY state_code, office").fetchall()
for r in races_rows:
    race = dict(r)
    race["candidates"] = [dict(c) for c in cur.execute(
        "SELECT candidate_name,candidate_party,is_incumbent,current_status "
        "FROM candidate WHERE race_id=? ORDER BY candidate_party",
        (race["race_id"],)).fetchall()]
    ratings = []
    for rr in cur.execute("""SELECT rr.rater, s.rating_label, s.competitiveness, s.lean,
                             rr.as_of_date FROM race_rating rr
                             JOIN race_rating_scale s ON s.rating_code=rr.rating_code
                             WHERE rr.race_id=? ORDER BY rr.as_of_date DESC""",
                          (race["race_id"],)).fetchall():
        ratings.append({"rater": RATER_SHORT.get(rr[0], rr[0]), "label": rr[1],
                        "comp": rr[2], "lean": rr[3], "asof": rr[4]})
    race["ratings"] = ratings
    race["max_comp"] = max([x["comp"] for x in ratings], default=None)
    states[race["state_code"]]["races"].append(race)

for r in cur.execute("""SELECT v.vendor_name, v.definition_note, c.state_code, c.snapshot_date,
                        c.total_count, c.total_pipeline_mw FROM dc_vendor_count c
                        JOIN dc_vendor v ON v.vendor_id=c.vendor_id"""):
    states[r["state_code"]]["dc_vendor"].append(dict(r))

positions = []
for r in cur.execute("""SELECT * FROM v_effective_position
                        ORDER BY leverage_score DESC""").fetchall():
    d = dict(r)
    d["evidence"] = [dict(e) for e in cur.execute("""
        SELECT e.evidence_type, e.summary, e.evidence_date, e.direction,
               b.label_ko AS binding_label, b.weight AS binding_w,
               s.label_ko AS scope_label,   s.weight AS scope_w,
               src.publisher, src.url, src.tier
        FROM position_evidence e
        LEFT JOIN binding_force b ON b.binding_code=e.binding_code
        LEFT JOIN regulation_scope s ON s.scope_code=e.scope_code
        JOIN source src ON src.source_id=e.source_id
        WHERE e.position_id=? ORDER BY b.weight DESC""", (d["position_id"],)).fetchall()]
    d["axes"] = [dict(a) for a in cur.execute(
        "SELECT axis_code,axis_score FROM position_axis_score WHERE position_id=?",
        (d["position_id"],)).fetchall()]
    d["statement"] = cur.execute(
        "SELECT policy_statement FROM politician_dc_position WHERE position_id=?",
        (d["position_id"],)).fetchone()[0]
    positions.append(d)
    states[d["state_code"]].setdefault("positions", []).append(d["position_id"])

for r in cur.execute("""SELECT r.state_code, r.office, p.pollster, p.field_start, p.field_end,
        p.sample_size, p.population, p.margin_d_minus_r FROM polling p
        JOIN election_race r ON r.race_id=p.race_id ORDER BY p.field_end DESC""").fetchall():
    states[r["state_code"]].setdefault("polls", []).append(dict(r))

national_opinion = []
for r in cur.execute("""SELECT * FROM dc_public_opinion ORDER BY field_end DESC""").fetchall():
    if r["state_code"] is None:
        national_opinion.append(dict(r))       # 전국 조사는 주에 귀속시키지 않는다
    else:
        states[r["state_code"]].setdefault("opinion", []).append(dict(r))

for r in cur.execute("SELECT * FROM state_dc_context").fetchall():
    states[r["state_code"]]["grid"] = dict(r)
capacity = [dict(x) for x in cur.execute("SELECT * FROM grid_capacity_price ORDER BY delivery_year").fetchall()]

for r in cur.execute("SELECT * FROM v_poll_coverage").fetchall():
    states[r["state_code"]].setdefault("coverage", []).append(dict(r))
for r in cur.execute("SELECT * FROM v_polling_blind_spot").fetchall():
    states[r["state_code"]].setdefault("blind", []).append(dict(r))

changes = [dict(x) for x in cur.execute("""SELECT event_type,state_code,old_value,new_value,
    changed_at,note FROM change_log ORDER BY changed_at DESC LIMIT 14""").fetchall()]
conflicts = [dict(x) for x in cur.execute("SELECT * FROM source_conflict").fetchall()]
sources = [dict(x) for x in cur.execute("SELECT * FROM source ORDER BY tier, source_id")]

# 전국 집계
tot = {
 "sen_up": cur.execute("SELECT COUNT(*) FROM election_race WHERE office='U.S. Senate'").fetchone()[0],
 "sen_r": cur.execute("SELECT COUNT(*) FROM election_race WHERE office='U.S. Senate' AND incumbent_party='R'").fetchone()[0],
 "sen_d": cur.execute("SELECT COUNT(*) FROM election_race WHERE office='U.S. Senate' AND incumbent_party='D'").fetchone()[0],
 "sen_open": cur.execute("SELECT COUNT(*) FROM election_race WHERE office='U.S. Senate' AND is_open_seat=1").fetchone()[0],
 "gov_up": cur.execute("SELECT COUNT(*) FROM election_race WHERE office='Governor'").fetchone()[0],
 "gov_tl": cur.execute("SELECT COUNT(*) FROM governor_race_detail WHERE term_limited=1").fetchone()[0],
 "gov_d_all": cur.execute("SELECT COUNT(*) FROM state_political_structure WHERE governor_party='D'").fetchone()[0],
 "gov_r_all": cur.execute("SELECT COUNT(*) FROM state_political_structure WHERE governor_party='R'").fetchone()[0],
 "cands": cur.execute("SELECT COUNT(*) FROM candidate").fetchone()[0],
}
con.close()

DATA = json.dumps({"states": states, "totals": tot, "conflicts": conflicts,
                   "sources": sources, "positions": positions, "changes": changes, "capacity": capacity, "national_opinion": national_opinion}, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2026 미국 중간선거 × 데이터센터 정치 리스크 트래커</title>
<meta name="description" content="2026 미국 중간선거 상원 35석·주지사 36석과 데이터센터 규제 리스크를 함께 추적. 후보별 데이터센터 입장을 구속력·범위·직위권한 3차원으로 측정.">
<meta property="og:type" content="website">
<meta property="og:title" content="2026 미국 중간선거 × 데이터센터 정치 리스크 트래커">
<meta property="og:description" content="상원 35석·주지사 36석 + 후보 12명의 데이터센터 규제 레버리지. 근거 26건 전량 출처 표기.">
<meta name="twitter:card" content="summary_large_image">
<meta name="robots" content="index,follow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+KR:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --panel:#12171F; --raised:#1A212C; --rule:#2A3441; --rule-hi:#3B4757;
  --ink:#DCE2EA; --mute:#78889C; --dim:#4E5B6C;
  --dem:#4A7FD4; --gop:#CE4B41; --ind:#8B6BB5; --none:#3A4452;
  --load:#E9A13B; --alert:#E0523F;
}
*{box-sizing:border-box}
body{margin:0;background:var(--panel);color:var(--ink);
  font-family:"IBM Plex Sans KR",system-ui,sans-serif;font-size:14px;line-height:1.55;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:20px 16px 64px}
h1,h2,h3,.disp{font-family:"Barlow Condensed",sans-serif;font-weight:600;
  letter-spacing:.04em;text-transform:uppercase;margin:0}
.mono{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}

/* ---- header ---- */
header{border-bottom:1px solid var(--rule);padding-bottom:16px;margin-bottom:20px}
h1{font-size:clamp(22px,5vw,34px);line-height:1.05;letter-spacing:.02em}
h1 .x{color:var(--load);font-weight:400;padding:0 .18em}
.sub{color:var(--mute);font-size:12px;margin-top:6px;letter-spacing:.02em}
.countdown{display:inline-block;border:1px solid var(--rule-hi);border-radius:2px;
  padding:1px 7px;margin-left:8px;color:var(--load);font-size:11px}

/* ---- tally strip ---- */
.tally{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:1px;background:var(--rule);border:1px solid var(--rule);margin-bottom:22px}
.cell{background:var(--raised);padding:11px 13px}
.cell .lab{font-size:10px;color:var(--mute);text-transform:uppercase;
  letter-spacing:.11em;font-family:"Barlow Condensed",sans-serif;font-weight:600}
.cell .val{font-size:25px;line-height:1.15;margin-top:2px}
.cell .note{font-size:11px;color:var(--dim)}
.d{color:var(--dem)} .r{color:var(--gop)} .ld{color:var(--load)}

/* ---- controls ---- */
.modes{display:flex;gap:1px;background:var(--rule);border:1px solid var(--rule);
  margin-bottom:14px;flex-wrap:wrap}
.modes button{flex:1 1 120px;background:var(--raised);border:0;color:var(--mute);
  padding:9px 6px;cursor:pointer;font-family:"Barlow Condensed",sans-serif;font-size:13px;
  font-weight:600;letter-spacing:.07em;text-transform:uppercase}
.modes button[aria-pressed=true]{background:#26303D;color:var(--ink);
  box-shadow:inset 0 -2px 0 var(--load)}
.modes button:focus-visible{outline:2px solid var(--load);outline-offset:-2px}

/* ---- tile map: 각 주는 배전반의 차단기 한 칸 ---- */
.grid{display:grid;grid-template-columns:repeat(11,1fr);gap:4px;margin-bottom:8px}
.tile{position:relative;aspect-ratio:1;border:1px solid var(--rule-hi);border-radius:2px;
  background:var(--raised);cursor:pointer;display:flex;align-items:center;
  justify-content:center;padding:0;overflow:hidden;transition:transform .09s}
.tile:hover{transform:translateY(-2px)}
.tile:focus-visible{outline:2px solid var(--load);outline-offset:2px}
.tile .ab{font-family:"IBM Plex Mono",monospace;font-size:clamp(8px,1.5vw,12px);
  font-weight:600;color:#0E1319;letter-spacing:.02em;z-index:2}
.tile.dark .ab{color:#E6EBF1}
.tile .load{position:absolute;top:0;left:0;right:0;height:5px;z-index:2}
.tile.sel{box-shadow:0 0 0 2px var(--load);transform:translateY(-2px)}
.tile.noelec{opacity:.45}
.tile.stale{border-style:dashed;border-color:var(--load);opacity:.75}
.hatch{background-image:repeating-linear-gradient(45deg,var(--dim) 0 2px,transparent 2px 5px)}

/* ---- legend ---- */
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:11px;color:var(--mute);
  padding:10px 0 22px;border-bottom:1px solid var(--rule);margin-bottom:20px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:2px;
  margin-right:5px;vertical-align:-1px}

/* ---- detail ---- */
.detail{border:1px solid var(--rule);background:var(--raised)}
.dhead{padding:14px 16px;border-bottom:1px solid var(--rule);display:flex;
  align-items:baseline;gap:12px;flex-wrap:wrap}
.dhead h2{font-size:24px}
.pill{font-size:10px;letter-spacing:.1em;text-transform:uppercase;padding:2px 8px;
  border-radius:2px;font-family:"Barlow Condensed",sans-serif;font-weight:600}
.dbody{padding:16px}
.kv{display:grid;grid-template-columns:112px 1fr;gap:4px 12px;font-size:13px;
  margin-bottom:18px}
.kv dt{color:var(--mute);font-size:11px;text-transform:uppercase;letter-spacing:.08em;
  font-family:"Barlow Condensed",sans-serif;font-weight:600;padding-top:2px}
.kv dd{margin:0}
h3.sect{font-size:13px;color:var(--mute);border-top:1px solid var(--rule);
  padding-top:12px;margin:18px 0 10px;letter-spacing:.1em}
.race{border-left:2px solid var(--rule-hi);padding:0 0 0 12px;margin-bottom:16px}
.race .top{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;margin-bottom:5px}
.race .office{font-family:"Barlow Condensed",sans-serif;font-weight:600;font-size:16px;
  letter-spacing:.04em;text-transform:uppercase}
.tag{font-size:10px;padding:1px 6px;border:1px solid var(--rule-hi);border-radius:2px;
  color:var(--mute);letter-spacing:.06em;text-transform:uppercase}
.tag.open{border-color:var(--load);color:var(--load)}
.ratings{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}
.rt{font-size:11px;padding:2px 7px;border-radius:2px;font-family:"IBM Plex Mono",monospace}
.cands{list-style:none;padding:0;margin:6px 0 0;font-size:13px}
.cands li{padding:2px 0;display:flex;gap:8px;align-items:baseline}
.bar{width:3px;height:13px;border-radius:1px;flex:none}
.na{color:var(--dim);font-style:normal;font-size:12px}
.pending{border:1px dashed var(--rule-hi);padding:11px 13px;color:var(--mute);
  font-size:12px;border-radius:2px;background:#161D27}
.pending b{color:var(--load);font-weight:600}
.warn{border-left:2px solid var(--alert);background:#1E1719;padding:10px 12px;
  font-size:12px;color:#D8C2C0;margin-top:10px}

/* 정치인 입장 */
.pol{border:1px solid var(--rule);background:#161D27;margin-bottom:10px;border-radius:2px}
.pol summary{list-style:none;cursor:pointer;padding:11px 13px;display:flex;
  align-items:center;gap:10px;flex-wrap:wrap}
.pol summary::-webkit-details-marker{display:none}
.pol summary:focus-visible{outline:2px solid var(--load);outline-offset:-2px}
.pol .nm{font-weight:600;font-size:14px}
.lev{flex:none;width:56px;text-align:right;font-family:"IBM Plex Mono",monospace;
  font-size:17px;font-weight:600}
.levbar{flex:1 1 90px;height:5px;background:#0E1319;border-radius:3px;overflow:hidden;
  min-width:70px;position:relative}
.levbar i{display:block;height:100%;background:var(--load)}
.polbody{padding:0 13px 13px;border-top:1px solid var(--rule)}
.dims{display:grid;grid-template-columns:repeat(auto-fit,minmax(78px,1fr));gap:1px;
  background:var(--rule);border:1px solid var(--rule);margin:11px 0}
.dims div{background:#12171F;padding:7px 8px}
.dims .k{font-size:9px;color:var(--mute);letter-spacing:.09em;text-transform:uppercase;
  font-family:"Barlow Condensed",sans-serif;font-weight:600}
.dims .v{font-family:"IBM Plex Mono",monospace;font-size:13px;margin-top:1px}
.axes{display:flex;gap:3px;margin:10px 0 4px}
.ax{flex:1;text-align:center}
.ax .t{font-size:9px;color:var(--mute);font-family:"Barlow Condensed",sans-serif;
  letter-spacing:.05em;margin-bottom:3px}
.axtrack{height:34px;background:#0E1319;border-radius:2px;position:relative;overflow:hidden}
.axtrack .mid{position:absolute;left:0;right:0;top:50%;height:1px;background:var(--rule-hi)}
.axtrack b{position:absolute;left:15%;right:15%;border-radius:1px}
.ax .n{font-size:10px;font-family:"IBM Plex Mono",monospace;color:var(--mute);margin-top:2px}
.ev{border-left:2px solid var(--rule-hi);padding-left:10px;margin-top:9px;font-size:12px}
.ev.sup{border-left-color:var(--dem)}
.ev .meta{font-size:10px;color:var(--dim);margin-top:3px;font-family:"IBM Plex Mono",monospace}
.ev a{color:var(--mute)}

.badge{display:inline-block;font-size:9px;letter-spacing:.09em;text-transform:uppercase;
  font-family:"Barlow Condensed",sans-serif;font-weight:600;padding:1px 5px;border-radius:2px;
  vertical-align:1px;margin-left:5px}
.badge.fact{border:1px solid var(--rule-hi);color:var(--mute)}
.badge.ai{border:1px solid var(--load);color:var(--load)}

.chg{border:1px solid var(--rule);background:var(--raised);margin-bottom:20px}
.chg h3{font-size:13px;color:var(--mute);padding:11px 14px 0;letter-spacing:.1em}
.chg ul{list-style:none;margin:8px 0 0;padding:0 14px 12px;font-size:12px;max-height:220px;
  overflow-y:auto}
.chg li{padding:6px 0;border-bottom:1px solid #1E2630;display:flex;gap:9px;align-items:baseline}
.chg li:last-child{border-bottom:0}
.chg .dt{font-family:"IBM Plex Mono",monospace;color:var(--dim);flex:none;font-size:11px}
.chg .st{font-family:"IBM Plex Mono",monospace;color:var(--load);flex:none;width:24px}
.opbar{height:22px;display:flex;border-radius:2px;overflow:hidden;margin:5px 0 3px;
  background:#0E1319}
.opbar span{display:block;font-size:10px;line-height:22px;text-align:center;
  font-family:"IBM Plex Mono",monospace;color:#0E1319;font-weight:600}
.oprow{margin-bottom:12px}
.oprow .lab{font-size:12px;color:var(--mute);display:flex;justify-content:space-between}
.notice{border:1px solid var(--load);background:#1E1913;padding:11px 13px;
  font-size:12px;line-height:1.65;margin-bottom:18px;border-radius:2px}
.notice b{color:var(--load)}
.shareline{font-size:11px;color:var(--dim);margin-top:6px}
footer{margin-top:34px;border-top:1px solid var(--rule);padding-top:16px;
  font-size:11px;color:var(--dim);line-height:1.75}
footer a{color:var(--mute);text-decoration:none;border-bottom:1px solid var(--rule)}
footer a:hover{color:var(--ink)}
.srcline{display:block}
@media(max-width:640px){
  .grid{gap:3px}
  .kv{grid-template-columns:90px 1fr}
  .cell .val{font-size:21px}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>U.S. Midterm<span class="x">×</span>Data Center<br>Political Risk Tracker</h1>
  <div class="sub mono">갱신 2026-09-10 — 격전지 여론조사 25건 · MI 리드 역전<span class="countdown" id="cd"></span></div>
</header>

<div class="notice">
  <b>사실과 분석의 구분</b> — 선거 일정·현직·후보·발언 내용은 출처가 확인된
  <span class="badge fact">Fact</span> 입니다.
  레버리지 점수, 5개 축 점수, 구속력·범위 가중치는 공개된 근거를 바탕으로 한
  <span class="badge ai">AI 분석</span> 이며 저자의 판단이 들어갑니다.
  각 후보 항목을 펼치면 점수의 근거와 원문 링크를 모두 확인할 수 있습니다.
  투자 판단이나 정치적 결론의 근거로 삼기 전에 원문을 직접 확인하시기 바랍니다.
  <div class="shareline">데이터 기준일 2026-09-10 · 선거일 2026-11-03 ·
  이 페이지는 특정 정당이나 후보를 지지하지 않습니다.</div>
</div>
<div class="tally" id="tally"></div>

<div class="chg">
  <h3 class="disp">최근 변동 — 자동 기록</h3>
  <ul id="chglist"></ul>
</div>

<div class="modes" role="group" aria-label="지도 표시 기준">
  <button data-mode="party" aria-pressed="true">주지사 정당</button>
  <button data-mode="exposure" aria-pressed="false">2026 선거 노출도</button>
  <button data-mode="compete" aria-pressed="false">접전 등급</button>
  <button data-mode="poll" aria-pressed="false">여론조사 공백</button>
  <button data-mode="lev" aria-pressed="false">규제 레버리지</button>
  <button data-mode="dc" aria-pressed="false">데이터센터 규모</button>
</div>

<div id="pollctl" style="display:none;margin:-4px 0 12px;font-size:12px">
  <label style="display:inline-flex;align-items:center;gap:7px;cursor:pointer;color:var(--mute)">
    <input type="checkbox" id="exBattle" style="accent-color:var(--load);width:15px;height:15px">
    격전지 제외 — Lean 이상 등급이 붙은 레이스를 숨깁니다
  </label>
</div>
<div class="grid" id="grid" role="group" aria-label="미국 50개 주"></div>
<div class="legend" id="legend"></div>

<section class="detail" id="detail" aria-live="polite"></section>

<footer>
  <div style="margin-bottom:10px">
    <span style="color:var(--mute)">데이터 원칙 —</span>
    모든 값은 <b style="color:var(--ink)">Fact</b> 레이어이며 출처가 확인된 항목만 입력했습니다.
    수집하지 않은 항목은 추정하지 않고 <span class="na">미수집</span>으로 표시합니다.
    주의회 의석 구성과 데이터센터 현황(MW)은 아직 수집 전입니다.
    <span style="color:var(--load)">◆</span> 표시 항목은 저자가 부여한 가중치입니다.
  </div>
  <div style="margin-bottom:10px">
    <span style="color:var(--mute)">재사용 —</span>
    이 페이지는 외부 의존성이 없는 단일 HTML 파일입니다. 원본 데이터·스키마·계산 방식은
    함께 배포되는 SQLite DB와 스크립트에서 확인할 수 있습니다.
    인용 시 데이터 기준일(2026-08-27)을 함께 밝혀 주세요.
  </div>
  <div id="srclist"></div>
</footer>

</div>
<script>
const DB = __DATA__;
const P = {D:'var(--dem)', R:'var(--gop)', I:'var(--ind)', L:'var(--ind)', G:'var(--ind)'};
let mode='party', sel='TX';

/* ---------- countdown ---------- */
(function(){
  const d = Math.round((new Date('2026-11-03') - new Date('2026-09-10'))/864e5);
  document.getElementById('cd').textContent = '선거일까지 D-'+d;
})();

/* ---------- tally ---------- */
(function(){
  const t = DB.totals;
  const cells = [
    ['상원 2026 선거 대상', `<span class="mono">${t.sen_up}</span>`,
     `<span class="r">공화 ${t.sen_r}</span> · <span class="d">민주 ${t.sen_d}</span> 보유석`],
    ['상원 오픈시트', `<span class="mono ld">${t.sen_open}</span>`, '현직 은퇴·전직·예비선거 패배'],
    ['주지사 선거', `<span class="mono">${t.gov_up}</span>`,
     `임기제한 ${t.gov_tl}명 · 민주 18 / 공화 18 방어`],
    ['현재 주지사', `<span class="mono r">${t.gov_r_all}</span><span style="color:var(--dim)">/</span><span class="mono d">${t.gov_d_all}</span>`,
     '공화 / 민주'],
    ['등재 후보', `<span class="mono">${t.cands}</span>`, '주요 후보만. 군소후보 제외'],
    ['입장 등재 후보', `<span class="mono ld">${DB.positions.length}</span>`,
     'NY·TX·PA·OH·MI·FL·OR — 근거 기반'],
    ['TX 데이터센터 여론', `<span class="mono" style="color:var(--alert)">-27</span>`,
     '찬성 30 / 반대 57 · UT-TxPP 8월'],
    ['발효 중인 규제', `<span class="mono ld">3</span>`,
     'NY 행정명령 · TX 접속중단 · OR 세제중단'],
    ['본선 여론조사 공백', `<span class="mono" style="color:var(--alert)">63</span>`,
     '71개 레이스 중 조사 있는 곳은 8개'],
  ];
  document.getElementById('tally').innerHTML = cells.map(c =>
    `<div class="cell"><div class="lab">${c[0]}</div><div class="val">${c[1]}</div>
     <div class="note">${c[2]}</div></div>`).join('');
})();

/* ---------- map ---------- */
function maxComp(s){
  let m = null;
  s.races.forEach(r => { if(r.max_comp!=null) m = (m==null)?r.max_comp:Math.max(m,r.max_comp); });
  return m;
}
function tileStyle(s){
  const races = s.races.length;
  if(mode==='party'){
    const c = s.governor_party==='D' ? 'var(--dem)' : 'var(--gop)';
    return {bg:c, dark:false, cls:''};
  }
  if(mode==='exposure'){
    if(!races) return {bg:'var(--none)', dark:true, cls:'noelec'};
    const a = races===1 ? .40 : .85;
    return {bg:`rgba(233,161,59,${a})`, dark:false, cls:''};
  }
  if(mode==='compete'){
    const m = maxComp(s);
    if(m==null) return {bg:'var(--none)', dark:true, cls: races?'':'noelec'};
    if(m>=100) return {bg:'var(--load)', dark:false, cls:''};
    if(m>=65)  return {bg:'rgba(233,161,59,.45)', dark:false, cls:''};
    return {bg:'var(--none)', dark:true, cls:''};
  }
  if(mode==='poll'){
    const cov = (s.coverage||[]);
    if(!cov.length) return {bg:'var(--none)', dark:true, cls:'noelec'};
    const excl = document.getElementById('exBattle')?.checked;
    const use = excl ? cov.filter(c=>!c.is_battleground) : cov;
    if(!use.length) return {bg:'var(--none)', dark:true, cls:'noelec'};
    const polled = use.filter(c=>c.poll_count>0);
    if(!polled.length) return {bg:'var(--none)', dark:true, cls:'hatch'};
    const fresh = polled.filter(c=>c.coverage_status==='CURRENT');
    const pick = (fresh.length?fresh:polled)[0];
    const m = pick.latest_margin;
    if(m==null) return {bg:'var(--none)', dark:true, cls:'hatch'};
    const a = Math.min(1, 0.25 + Math.abs(m)/20);
    const c = m>0 ? `rgba(74,127,212,${a.toFixed(2)})` : `rgba(206,75,65,${a.toFixed(2)})`;
    return {bg:c, dark:false, cls: pick.coverage_status==='CURRENT' ? '' : 'stale'};
  }
  if(mode==='lev'){
    const ids=s.positions||[];
    if(!ids.length) return {bg:'var(--none)', dark:true, cls:'hatch'};
    const mx=Math.max(...DB.positions.filter(p=>ids.includes(p.position_id))
                        .map(p=>p.leverage_score||0));
    return {bg:`rgba(233,161,59,${(0.2+0.8*mx/100).toFixed(2)})`, dark:false, cls:''};
  }
  return {bg:'var(--none)', dark:true, cls:'hatch'};   /* dc: 미수집 */
}
function drawMap(){
  const g = document.getElementById('grid');
  g.innerHTML = '';
  const rows = 8;
  const byPos = {};
  Object.values(DB.states).forEach(s => byPos[s.tile[0]+'-'+s.tile[1]] = s);
  for(let r=0;r<rows;r++) for(let c=0;c<11;c++){
    const s = byPos[r+'-'+c];
    if(!s){ const d=document.createElement('div'); g.appendChild(d); continue; }
    const st = tileStyle(s);
    const b = document.createElement('button');
    b.className = 'tile '+st.cls+(st.dark?' dark':'')+(sel===s.state_code?' sel':'');
    b.style.backgroundColor = st.bg;
    b.setAttribute('aria-label', s.state_name);
    const hasDC = s.dc_vendor.length>0;
    b.innerHTML = `<span class="load ${hasDC?'':'hatch'}" style="${hasDC?'background-color:var(--load)':''}"></span>`
                + `<span class="ab">${s.state_code}</span>`;
    b.onclick = () => { sel = s.state_code; 
document.getElementById('chglist').innerHTML = DB.changes.map(c=>
  `<li><span class="dt">${c.changed_at.slice(5)}</span>
   <span class="st">${c.state_code||''}</span>
   <span>${c.note}</span></li>`).join('');

drawMap(); drawDetail(); };
    g.appendChild(b);
  }
  drawLegend();
}
function drawLegend(){
  const L = {
    party:[['var(--dem)','민주 주지사'],['var(--gop)','공화 주지사']],
    exposure:[['rgba(233,161,59,.85)','상원+주지사 모두 선거'],['rgba(233,161,59,.40)','1개 선거'],
              ['var(--none)','2026 연방·주지사 선거 없음']],
    compete:[['var(--load)','Toss Up 포함'],['rgba(233,161,59,.45)','Lean 포함'],
             ['var(--none)','등급 미수집 또는 비경합']],
    poll:[['rgba(74,127,212,.9)','민주 우세'],['rgba(206,75,65,.9)','공화 우세'],
          ['var(--none)','본선 여론조사 없음']],
    lev:[['rgba(233,161,59,1)','최고 레버리지 후보 보유'],['rgba(233,161,59,.3)','낮음'],
         ['var(--none)','후보 입장 미수집']],
    dc:[['var(--none)','전 주 미수집 — STEP 4']],
  }[mode];
  document.getElementById('pollctl').style.display = (mode==='poll') ? 'block' : 'none';
  document.getElementById('legend').innerHTML =
    L.map(x=>`<span><i style="background-color:${x[0]}"></i>${x[1]}</span>`).join('')
    + (mode==='poll' ? `<span><i style="border:1px dashed var(--load);background:transparent"></i>90일 초과 노후 조사</span>` : '')
    + `<span><i class="hatch" style="background-color:var(--raised)"></i>상단 스트립 = 데이터센터 부하(미수집)</span>`;
}
document.addEventListener('change', e=>{ if(e.target.id==='exBattle') drawMap(); });
document.querySelectorAll('.modes button').forEach(btn=>{
  btn.onclick = () => {
    mode = btn.dataset.mode;
    document.querySelectorAll('.modes button').forEach(b=>
      b.setAttribute('aria-pressed', String(b===btn)));
    drawMap();
  };
});

/* ---------- detail ---------- */
function ratingChip(rt){
  const col = rt.lean==='D'?'var(--dem)':rt.lean==='R'?'var(--gop)':'var(--load)';
  return `<span class="rt" style="border:1px solid ${col};color:${col}">
    ${rt.rater} · ${rt.label} <span style="color:var(--dim)">${rt.asof.slice(5)}</span></span>`;
}
function raceBlock(r){
  const open = r.is_open_seat ? '<span class="tag open">오픈시트 · '+r.open_seat_reason+'</span>' : '';
  const sp = r.election_type==='Special' ? '<span class="tag">보궐</span>' : '';
  const inc = r.incumbent_name
    ? `<span style="color:var(--mute)">현직</span> ${r.incumbent_name}
       <span style="color:${P[r.incumbent_party]||'var(--mute)'}">(${r.incumbent_party})</span>`
    : '';
  const rts = r.ratings.length
    ? `<div class="ratings">${r.ratings.map(ratingChip).join('')}</div>`
    : `<div class="ratings"><span class="na">레이스 등급 미수집</span></div>`;
  const cs = r.candidates.length
    ? `<ul class="cands">${r.candidates.map(c=>
        `<li><span class="bar" style="background:${P[c.candidate_party]||'var(--dim)'}"></span>
         <span>${c.candidate_name}</span>
         <span style="color:var(--dim);font-size:11px">${c.candidate_party}${c.is_incumbent?' · 현직':''}${
           c.current_status==='Withdrawn'?' · <span style="color:var(--alert)">사퇴</span>':''}</span></li>`
      ).join('')}</ul>`
    : `<div class="na" style="margin-top:6px">주요 후보 미수집</div>`;
  return `<div class="race"><div class="top"><span class="office">${r.office}</span>${sp}${open}</div>
    <div style="font-size:12px;color:var(--mute)">${inc}</div>${rts}${cs}</div>`;
}

const AXLAB={GROWTH:'성장',POWER:'전력',RATES:'요금',WATER:'물',TAX:'세제'};
function axBar(a){
  if(a.axis_score==null) return `<div class="ax"><div class="t">${AXLAB[a.axis_code]}</div>
    <div class="axtrack hatch"><span class="mid"></span></div><div class="n">—</div></div>`;
  const v=a.axis_score, h=Math.abs(v)/100*17, neg=v<0;
  const st = neg ? `top:50%;height:${h}px;background:var(--alert)`
                 : `bottom:50%;height:${h}px;background:var(--dem)`;
  return `<div class="ax"><div class="t">${AXLAB[a.axis_code]}</div>
    <div class="axtrack"><span class="mid"></span><b style="${st}"></b></div>
    <div class="n" style="color:${neg?'var(--alert)':'var(--dem)'}">${v>0?'+':''}${v}</div></div>`;
}
function polBlock(p){
  const col=P[p.party]||'var(--mute)';
  const lev=p.leverage_score??0;
  const dir = p.support_score!=null
    ? `<span style="color:${p.support_score<0?'var(--alert)':'var(--dem)'}">${p.support_score>0?'+':''}${p.support_score}</span>`
    : `<span class="na">축 부족</span>`;
  const eff = p.effective_impact!=null ? p.effective_impact : '<span class="na">—</span>';
  const evs = p.evidence.map(e=>`<div class="ev ${e.direction==='SUPPORTIVE'?'sup':''}">
      ${e.summary}
      <div class="meta">${e.binding_label??'—'} × ${e.scope_label??'—'}
        · ${e.evidence_date} · T${e.tier} <a href="${e.url}" target="_blank" rel="noopener">${e.publisher}</a>
        ${e.direction==='SUPPORTIVE'?' · <span style="color:var(--dem)">우호 근거</span>':''}</div>
    </div>`).join('');
  return `<details class="pol">
    <summary>
      <span class="bar" style="background:${col};height:17px"></span>
      <span class="nm">${p.full_name}</span>
      <span class="tag">${p.office}</span>
      <span class="levbar"><i style="width:${lev}%"></i></span>
      <span class="lev" style="color:var(--load)">${lev}</span>
    </summary>
    <div class="polbody">
      <div style="font-size:12px;color:var(--mute);margin-top:10px">${p.statement}</div>
      <div class="dims">
        <div><div class="k">구속력 <span style="color:var(--load)">◆</span></div><div class="v">${p.top_binding_label??'—'}</div></div>
        <div><div class="k">범위 <span style="color:var(--load)">◆</span></div><div class="v">${p.top_scope_label??'—'}</div></div>
        <div><div class="k">직위권한 <span style="color:var(--load)">◆</span></div><div class="v">${p.office_power??'—'}</div></div>
        <div><div class="k">방향 종합</div><div class="v">${dir}</div></div>
        <div><div class="k">실효치</div><div class="v">${eff}</div></div>
        <div><div class="k">신뢰도</div><div class="v">${p.confidence_level}</div></div>
      </div>
      <div class="axes">${p.axes.map(axBar).join('')}</div>
      <div style="font-size:10px;color:var(--dim);text-align:center;margin-bottom:4px">
        위=우호 / 아래=규제 · 빗금=근거 없음</div>
      <h3 class="sect" style="margin-top:14px">근거 (구속력 높은 순)<span class="badge fact">Fact</span></h3>
      ${evs}
    </div></details>`;
}
function drawDetail(){
  const s = DB.states[sel];
  const pc = s.governor_party==='D'?'var(--dem)':'var(--gop)';
  const dc = s.dc_vendor.length
    ? s.dc_vendor.map(v=>`<div style="font-size:12px;margin-bottom:6px">
        <span class="mono" style="color:var(--load)">${v.total_count??'—'}</span>
        <span style="color:var(--mute)"> 개 · ${v.vendor_name} (${v.snapshot_date})</span>
        ${v.total_pipeline_mw?`<span class="mono" style="color:var(--load)"> · ${v.total_pipeline_mw.toLocaleString()} MW</span>`:''}
        <div style="color:var(--dim);font-size:11px">${v.definition_note}</div></div>`).join('')
      + `<div class="warn">벤더마다 카운팅 단위와 포함 단계가 다릅니다. 이 수치들은 서로 더하거나
         직접 비교할 수 없습니다. 운영 중 / 건설 중 / 계획 분리는 STEP 4에서 수행합니다.</div>`
    : `<div class="pending">데이터센터 현황 <b>미수집</b> — STEP 4에서 운영 중 · 건설 중 ·
       승인 · 계획 · 발표 5단계로 분리 수집합니다.</div>`;



  const g = s.grid;
  const grid = g && g.grid_operator ? `<h3 class="sect">전력망<span class="badge fact">Fact</span></h3>
    <div style="font-size:13px;margin-bottom:8px">
      <span class="mono" style="color:var(--load);font-size:16px">${g.grid_operator}</span>
      <span style="color:var(--mute)"> · 스트레스 </span>
      <span style="color:${g.grid_stress_level==='Severe'?'var(--alert)':'var(--load)'}">${g.grid_stress_level||'—'}</span>
    </div>`
    + (g.grid_operator==='PJM' ? `<div style="font-size:12px;color:var(--mute);margin-bottom:10px">
        용량시장 낙찰가 (MW-day)</div>` + DB.capacity.map(c=>
        `<div style="display:flex;justify-content:space-between;font-size:12px;padding:2px 0">
         <span class="mono" style="color:var(--dim)">${c.delivery_year}</span>
         <span class="mono" style="color:${c.at_cap?'var(--alert)':'var(--ink)'}">$${c.price_mw_day.toFixed(2)}${c.at_cap?' 상한':''}</span></div>`).join('')
        + `<div style="font-size:11px;color:var(--dim);margin:6px 0 12px">
           4년간 11.5배. 13개 주·약 6,700만 명의 전기요금에 반영됩니다.</div>` : '')
    : '';


  const cov = s.coverage||[];
  const blind = (s.blind||[]).filter(b=>b.blind_spot_flag);
  const CS = {NO_POLLING:['조사 없음','var(--dim)'],STALE:['노후 (90일 초과)','var(--alert)'],
              AGING:['30일 경과','var(--load)'],CURRENT:['최신','var(--dem)']};
  const coverage = cov.length ? `<h3 class="sect">여론조사 커버리지<span class="badge fact">Fact</span></h3>`
    + cov.map(c=>{
        const st = CS[c.coverage_status]||['—','var(--dim)'];
        return `<div style="display:flex;justify-content:space-between;font-size:12px;padding:4px 0;
          border-bottom:1px solid #1E2630">
          <span>${c.office}${c.is_battleground?' <span class="tag">격전지</span>':''}</span>
          <span style="color:${st[1]};font-family:'IBM Plex Mono',monospace">${st[0]}${
            c.poll_age_days!=null?` · ${c.poll_age_days}일`:''}</span></div>`;
      }).join('')
    + (blind.length ? `<div class="warn" style="border-left-color:var(--load);background:#1E1913">
        <b style="color:var(--load)">관측 사각지대</b> — 데이터센터 정책이 실제로 움직이는데
        본선 여론조사가 없습니다. 선거 리스크를 여론으로 검증할 수 없는 상태입니다.</div>` : '')
    : '';

  const pl = s.polls||[];
  const polls = pl.length ? `<h3 class="sect">여론조사<span class="badge fact">Fact</span></h3>`
    + pl.map(p=>{
        const m=p.margin_d_minus_r, lead=m>0?'D':'R';
        return `<div style="font-size:13px;padding:6px 0;border-bottom:1px solid #1E2630">
          <span style="color:${m>0?'var(--dem)':'var(--gop)'};font-family:'IBM Plex Mono',monospace;
          font-weight:600">${lead}+${Math.abs(m)}</span>${p.is_average?' <span class="tag">평균</span>':''}
          <span style="color:var(--mute)"> · ${p.office}</span> · ${p.pollster}
          <div style="font-size:11px;color:var(--dim);font-family:'IBM Plex Mono',monospace">
          ${p.field_start}~${p.field_end} · n=${p.sample_size} ${p.population}</div></div>`;
      }).join('') : '';

  const op = (s.opinion||[]).filter(o=>o.metric==='LOCAL_CONSTRUCTION');
  const opImp = (s.opinion||[]).filter(o=>o.metric.startsWith('IMPACT_'));
  const IMPLAB={IMPACT_ENERGY_BILLS:'전기요금',IMPACT_WATER:'물 공급',IMPACT_GRID:'전력망 신뢰도',
                IMPACT_ENVIRONMENT:'주변 자연환경',IMPACT_LOCAL_ECONOMY:'지역경제'};
  const opinion = op.length ? `<h3 class="sect">데이터센터 여론<span class="badge fact">Fact</span></h3>`
    + op.map(o=>`<div class="oprow"><div class="lab"><span>${
        {ALL:'전체',REPUBLICAN:'공화당 지지',DEMOCRAT:'민주당 지지',INDEPENDENT:'무당층',
         RURAL:'농촌',SUBURBAN:'교외'}[o.subgroup]||o.subgroup}</span>
        <span style="font-family:'IBM Plex Mono',monospace;color:${o.net_pct<0?'var(--alert)':'var(--dem)'}">
        ${o.net_pct>0?'+':''}${o.net_pct}</span></div>
        <div class="opbar">
          <span style="width:${o.support_pct}%;background:var(--dem)">${o.support_pct}</span>
          <span style="width:${o.oppose_pct}%;background:var(--alert)">${o.oppose_pct}</span>
        </div></div>`).join('')
    + `<div style="font-size:11px;color:var(--dim);margin-bottom:12px">
       파랑=지역 내 건설 찬성 · 빨강=반대</div>`
    + (opImp.length ? `<div style="font-size:12px;color:var(--mute);margin-bottom:6px">
       영향 인식 (부정 우세 항목)</div>` + opImp.map(o=>
       `<div style="font-size:12px;padding:3px 0;display:flex;justify-content:space-between">
        <span>${IMPLAB[o.metric]||o.metric}</span>
        <span style="font-family:'IBM Plex Mono',monospace;color:var(--alert)">
        긍정 ${o.support_pct} / 부정 ${o.oppose_pct}</span></div>`).join('') : '')
    : '';

  const pids = s.positions||[];
  const pols = pids.length
    ? DB.positions.filter(p=>pids.includes(p.position_id)).map(polBlock).join('')
      + `<div style="font-size:11px;color:var(--dim);margin-top:8px">
         레버리지 = 구속력 × 범위 × 직위권한 × 100. 근거 1건만 있어도 산출됩니다.
         방향 종합은 5개 축 중 3개 이상 확보된 경우에만 표시합니다.</div>`
    : `<div class="pending">이 주의 후보 입장 <b>미수집</b> — 근거 기반으로만 입력하므로
       확인된 발언·법안·명령이 있는 주부터 채워집니다.</div>`;
  document.getElementById('detail').innerHTML = `
   <div class="dhead">
     <h2>${s.state_name}</h2>
     <span class="pill" style="background:${pc};color:#0E1319">${s.governor_party==='D'?'민주 주지사':'공화 주지사'}</span>
     <span class="mono" style="color:var(--dim);font-size:12px">${s.state_code}</span>
   </div>
   <div class="dbody">
     <dl class="kv">
       <dt>주지사</dt><dd>${s.governor}${s.governor_term_limited?' <span class="tag">임기제한</span>':''}</dd>
       <dt>2026 주지사선거</dt><dd>${s.governor_election_2026?'있음':'<span class="na">없음</span>'}</dd>
       <dt>2026 선거 수</dt><dd class="mono">${s.races.length}</dd>
       <dt>주의회 구성</dt><dd class="na">미수집 — 정당 통제(Trifecta) 판정 보류</dd>
       <dt>정치 리스크</dt><dd class="na">미산출 — STEP 7</dd>
     </dl>
     <h3 class="sect">2026 선거<span class="badge fact">Fact</span></h3>
     ${s.races.length ? s.races.map(raceBlock).join('')
        : '<div class="pending">이 주는 2026년 연방 상원·주지사 선거가 없습니다. 하원 선거는 STEP 2 후속에서 추가됩니다.</div>'}
     ${grid}
     ${coverage}
     ${polls}
     ${opinion}
     <h3 class="sect">후보 데이터센터 입장 — 규제 레버리지 순<span class="badge ai">AI 분석</span></h3>
     ${pols}
     <h3 class="sect">데이터센터 현황</h3>
     ${dc}
   </div>`;
}

/* ---------- sources ---------- */
document.getElementById('srclist').innerHTML =
  '<span style="color:var(--mute)">출처 (Tier 낮을수록 우선) — </span>' +
  DB.sources.map(s=>`<span class="srcline">T${s.tier} · ${s.publisher} · `
    + `<a href="${s.url}" target="_blank" rel="noopener">${s.title}</a>`
    + `${s.published_date?` <span class="mono">${s.published_date}</span>`:''}</span>`).join('');


document.getElementById('chglist').innerHTML = DB.changes.map(c=>
  `<li><span class="dt">${c.changed_at.slice(5)}</span>
   <span class="st">${c.state_code||''}</span>
   <span>${c.note}</span></li>`).join('');

drawMap(); drawDetail();
</script>
</body>
</html>
"""

open("index.html", "w", encoding="utf-8").write(
    HTML.replace("__DATA__", DATA))
print("dashboard written, bytes:", len(HTML) + len(DATA))
