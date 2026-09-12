#!/usr/bin/env python3
"""카드뉴스 5장. 1080x1350. 대시보드와 동일한 배전반(switchgear) 톤."""
from PIL import Image, ImageDraw, ImageFont
import sqlite3, math, os

W, H = 1080, 1350
OUT = "cards"
os.makedirs(OUT, exist_ok=True)

BG, RAISED, RULE, RULE_HI = "#12171F", "#1A212C", "#2A3441", "#3B4757"
INK, MUTE, DIM = "#DCE2EA", "#78889C", "#4E5B6C"
DEM, GOP, LOAD, ALERT = "#4A7FD4", "#CE4B41", "#E9A13B", "#E0523F"

if os.path.exists("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
    NP = "/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"
    def F(style, size):
        return ImageFont.truetype(NP % style, size, index=1)
elif os.path.exists("C:/Windows/Fonts/NotoSansKR-Regular.otf"):
    def F(style, size):
        return ImageFont.truetype(f"C:/Windows/Fonts/NotoSansKR-{style}.otf", size)
else:
    def F(style, size):
        return ImageFont.load_default()

if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
    def M(size, bold=False):
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono%s.ttf" % ("-Bold" if bold else ""), size)
elif os.path.exists("C:/Windows/Fonts/DejaVuSansMono.ttf"):
    def M(size, bold=False):
        return ImageFont.truetype(
            "C:/Windows/Fonts/DejaVuSansMono%s.ttf" % ("-Bold" if bold else ""), size)
else:
    def M(size, bold=False):
        return ImageFont.load_default()

def tw(d, t, f):
    b = d.textbbox((0, 0), t, font=f); return b[2] - b[0]

def base(page):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # 상단 부하 스트립 — 대시보드 타일의 시그니처 요소
    d.rectangle([0, 0, W, 9], fill=LOAD)
    # 하단 러너
    d.line([(72, H - 96), (W - 72, H - 96)], fill=RULE, width=1)
    d.text((72, H - 78), "2026 미국 중간선거 × 데이터센터 정치 리스크 트래커 · 9/10 기준",
           font=F("Regular", 20), fill=DIM)
    d.text((W - 72, H - 78), f"{page}/6", font=M(21), fill=DIM, anchor="ra")
    return im, d

def eyebrow(d, y, txt, col=LOAD):
    d.rectangle([72, y, 72 + 34, y + 4], fill=col)
    d.text((72, y + 18), txt, font=F("Bold", 23), fill=col)
    return y + 60

def wrap(d, txt, f, maxw):
    out, line = [], ""
    for ch in txt:
        if ch == "\n":
            out.append(line); line = ""; continue
        if tw(d, line + ch, f) > maxw:
            out.append(line); line = ch
        else:
            line += ch
    if line: out.append(line)
    return out

def para(d, x, y, txt, f, fill, maxw, lh):
    for ln in wrap(d, txt, f, maxw):
        d.text((x, y), ln, font=f, fill=fill); y += lh
    return y

# ============================================================ DATA
con = sqlite3.connect("data/tracker.db")
con.create_function("log", 1, lambda x: math.log(x) if x and x > 0 else None)
con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute("""SELECT state_code,full_name,party,leverage_score,
    support_score,top_binding_label,top_scope_label,office,confidence_level
    FROM v_effective_position ORDER BY leverage_score DESC""")]
paxton = [dict(r) for r in con.execute("""SELECT axis_code,axis_score FROM position_axis_score
    WHERE position_id=(SELECT position_id FROM politician_dc_position p
    JOIN politician pl ON pl.politician_id=p.politician_id WHERE pl.full_name='Ken Paxton')""")]
opin = {r["subgroup"]: dict(r) for r in con.execute("""SELECT * FROM dc_public_opinion
    WHERE metric='LOCAL_CONSTRUCTION' AND field_end='2026-08-13'""")}
imp = [dict(r) for r in con.execute("""SELECT * FROM dc_public_opinion
    WHERE metric LIKE 'IMPACT_%' ORDER BY net_pct""")]
polls = [dict(r) for r in con.execute("""SELECT r.office,p.pollster,p.field_start,p.field_end,
    p.margin_d_minus_r,p.sample_size FROM polling p JOIN election_race r ON r.race_id=p.race_id
    WHERE r.state_code='TX' ORDER BY p.field_end DESC""")]
con.close()
AX = {a["axis_code"]: a["axis_score"] for a in paxton}

# ============================================================ 1. 표지
im, d = base(1)
y = eyebrow(d, 150, "2026 미국 중간선거 · D-54")
d.text((72, y), "누가 데이터센터를", font=F("Black", 74), fill=INK); y += 92
d.text((72, y), "더 세게 막고 있나", font=F("Black", 74), fill=INK); y += 118

d.text((72, y), "말의 강도로 재면 틀립니다.", font=F("Medium", 34), fill=LOAD); y += 62
y = para(d, 72, y,
  "선거 광고에서 가장 강하게 말하는 후보와\n실제로 규제에 서명한 후보는 다릅니다.\n"
  "후보 12명의 발언·공약·행정명령 26건을\n구속력 · 범위 · 직위권한 3차원으로 measured.",
  F("Regular", 30), MUTE, 900, 50)

# 미니 순위 프리뷰
y += 40
d.line([(72, y), (W - 72, y)], fill=RULE, width=1); y += 34
for r in rows[:3]:
    col = DEM if r["party"] == "D" else GOP
    d.rectangle([72, y + 6, 76, y + 34], fill=col)
    d.text((94, y), f"{r['state_code']}  {r['full_name']}", font=F("Medium", 30), fill=INK)
    d.text((W - 72, y - 4), f"{r['leverage_score']:.0f}", font=M(40, True), fill=LOAD, anchor="ra")
    y += 54
d.text((72, y + 14), "규제 레버리지 (0~100)", font=F("Regular", 22), fill=DIM)
im.save(f"{OUT}/card_1_cover.png")

# ============================================================ 2. 레버리지 순위
im, d = base(2)
y = eyebrow(d, 130, "실제 규제 강도 순위")
d.text((72, y), "레버리지 = 구속력 × 범위 × 직위권한", font=F("Bold", 40), fill=INK); y += 78
d.text((72, y), "근거 1건만 있어도 산출됩니다.", font=F("Regular", 26), fill=MUTE); y += 62

mx = max(r["leverage_score"] for r in rows) or 1
for r in rows[:10]:
    col = DEM if r["party"] == "D" else GOP
    lev = r["leverage_score"]
    d.rectangle([72, y + 4, 77, y + 40], fill=col)
    nm = f"{r['state_code']} {r['full_name']}"
    d.text((94, y + 2), nm, font=F("Medium", 30), fill=INK)
    off = "주지사" if r["office"] == "Governor" else "연방상원"
    d.text((94 + tw(d, nm, F("Medium", 30)) + 14, y + 10), off, font=F("Regular", 21), fill=DIM)
    # 바
    bw = int(560 * lev / mx)
    d.rectangle([394, y + 46, 394 + 560, y + 56], fill="#0E1319")
    if bw > 0:
        d.rectangle([394, y + 46, 394 + bw, y + 56], fill=LOAD)
    d.text((W - 72, y + 2), f"{lev:.0f}", font=M(36, True),
           fill=LOAD if lev > 0 else DIM, anchor="ra")
    d.text((94, y + 44), f"{r['top_binding_label'] or '규제 근거 없음'}",
           font=F("Regular", 21), fill=MUTE)
    y += 84

d.line([(72, y + 6), (W - 72, y + 6)], fill=RULE, width=1)
para(d, 72, y + 26,
  "연방 상원 후보는 주 인허가 권한이 없어 0.55배가 곱해집니다.",
  F("Regular", 24), DIM, 940, 40)
im.save(f"{OUT}/card_2_ranking.png")

# ============================================================ 3. 뒤집힘
im, d = base(3)
y = eyebrow(d, 130, "순위가 뒤집히는 지점", ALERT)
d.text((72, y), "말이 센 쪽과", font=F("Black", 58), fill=INK); y += 72
d.text((72, y), "힘이 센 쪽이 다릅니다", font=F("Black", 58), fill=LOAD); y += 116

pair = [r for r in rows if r["full_name"] in ("Kathy Hochul", "Gina Hinojosa")]
pair.sort(key=lambda r: -r["leverage_score"])
for r in pair:
    col = DEM if r["party"] == "D" else GOP
    box_y = y
    d.rectangle([72, box_y, W - 72, box_y + 296], fill=RAISED, outline=RULE)
    d.rectangle([72, box_y, 78, box_y + 296], fill=col)
    d.text((108, box_y + 34), r["full_name"], font=F("Bold", 44), fill=INK)
    OFF = {"Kathy Hochul":"뉴욕 주지사","Gina Hinojosa":"텍사스 주지사 후보"}
    d.text((108, box_y + 96), f"{OFF.get(r['full_name'],'')} · {r['party']}",
           font=F("Regular", 26), fill=MUTE)

    d.text((108, box_y + 166), "말의 강도", font=F("Regular", 22), fill=DIM)
    d.text((108, box_y + 198), f"{r['support_score']:.0f}", font=M(50, True), fill=ALERT)

    d.text((420, box_y + 166), "실제 강도", font=F("Regular", 22), fill=DIM)
    d.text((420, box_y + 198), f"{r['leverage_score']:.0f}", font=M(50, True), fill=LOAD)

    d.text((700, box_y + 166), "근거", font=F("Regular", 22), fill=DIM)
    para(d, 700, box_y + 200, r["top_binding_label"], F("Medium", 26), INK, 250, 34)
    y += 320

y += 4
d.line([(72, y), (W - 72, y)], fill=RULE, width=1); y += 26
y = para(d, 72, y,
  "Hochul은 7월 14일 행정명령 62호로 50MW 이상 데이터센터의 환경허가를 보류시켰습니다. "
  "전국 최초 주 단위 모라토리엄이고 이미 발효 중입니다. "
  "Hinojosa의 모라토리엄은 당선돼야 집행됩니다.", F("Regular", 28), MUTE, 936, 46)
y += 14
d.text((72, y), "방향은 Hinojosa가 더 세지만, 구속력이 0.42배입니다.",
       font=F("Medium", 27), fill=LOAD)
im.save(f"{OUT}/card_3_reversal.png")

# ============================================================ 4. Paxton 5축
im, d = base(4)
y = eyebrow(d, 130, "단일 점수로는 안 잡히는 것")
d.text((72, y), "Ken Paxton", font=F("Black", 62), fill=INK); y += 78
d.text((72, y), "텍사스 연방상원 공화당 후보", font=F("Regular", 27), fill=MUTE); y += 74

y = para(d, 72, y,
  "농촌 입지 금지와 판매세 면제 폐지를 주장하면서,\n"
  "동시에 낡은 규제를 없애고 발전설비를 새로 짓는 법안을 공동발의합니다.",
  F("Regular", 29), INK, 940, 46)
y += 34

LAB = [("GROWTH", "산업성장"), ("POWER", "전력"), ("RATES", "전기요금"),
       ("WATER", "물사용"), ("TAX", "세제혜택")]
cx0, cw, gap = 72, 168, 16
top, bh = y, 420
mid = top + bh // 2
for i, (code, lab) in enumerate(LAB):
    x = cx0 + i * (cw + gap)
    d.rectangle([x, top, x + cw, top + bh], fill="#0E1319")
    v = AX.get(code)
    if v is None:
        d.text((x + cw // 2, mid), "—", font=M(30), fill=DIM, anchor="mm")
    else:
        h = int(abs(v) / 100 * (bh // 2 - 20))
        if v < 0:
            d.rectangle([x + 22, mid, x + cw - 22, mid + h], fill=ALERT)
        else:
            d.rectangle([x + 22, mid - h, x + cw - 22, mid], fill=DEM)
        d.text((x + cw // 2, mid + (h + 24 if v < 0 else -h - 24)),
               f"{'+' if v > 0 else ''}{v}", font=M(28, True),
               fill=ALERT if v < 0 else DEM, anchor="mm")
    d.line([(x, mid), (x + cw, mid)], fill=RULE_HI, width=2)
    d.text((x + cw // 2, top + bh + 30), lab, font=F("Medium", 27), fill=MUTE, anchor="ma")

y = top + bh + 92
d.text((72, y), "▲ 위 = 우호", font=F("Regular", 23), fill=DEM)
d.text((240, y), "▼ 아래 = 규제", font=F("Regular", 23), fill=ALERT)
y += 56
d.line([(72, y), (W - 72, y)], fill=RULE, width=1); y += 28
para(d, 72, y,
  "전력축만 +45, 나머지 네 축은 전부 음수입니다. "
  "다섯 축을 하나로 뭉개면 이 구조가 사라집니다.",
  F("Regular", 28), MUTE, 936, 46)
im.save(f"{OUT}/card_4_paxton.png")

# ============================================================ 5. 방법·출처
im, d = base(5)
y = eyebrow(d, 130, "측정 방법과 한계")
d.text((72, y), "점수는 어떻게 나왔나", font=F("Black", 54), fill=INK); y += 100

steps = [
 ("구속력", "법률 서명 1.00 · 행정명령 0.95 · 규제기관 지시 0.85\n표결 0.70 · 법안발의 0.60 · 공약 0.40 · 광고 0.20"),
 ("범위", "신규 전면중단 1.00 · 신규 조건부 0.75 · 입지제한 0.70\n지역동의 0.65 · 세제폐지 0.60 · 비용부담 0.50"),
 ("직위권한", "주지사 1.00 · 주의원 0.70 · 연방상원 0.55 · 연방하원 0.45"),
]
for lab, body in steps:
    d.rectangle([72, y, W - 72, y + 150], fill=RAISED, outline=RULE)
    d.rectangle([72, y, 78, y + 150], fill=LOAD)
    d.text((104, y + 22), lab, font=F("Bold", 32), fill=LOAD)
    para(d, 104, y + 70, body, F("Regular", 24), MUTE, 880, 34)
    y += 172

y += 16
d.line([(72, y), (W - 72, y)], fill=RULE, width=1); y += 28
y = para(d, 72, y,
  "한계 — 후보 12명 중 7명은 근거가 부족해 '방향 종합'을 내지 않았습니다. "
  "5개 축 중 3개 이상 확보된 경우에만 산출합니다.",
  F("Regular", 26), MUTE, 936, 42)
y += 20
d.text((72, y), "출처", font=F("Bold", 26), fill=INK); y += 44
for s in ["CBS Texas · Texas Tribune · E&E News · KUT · The Texan",
          "The Hill · CNBC · NPR · Brookings · Philadelphia Inquirer",
          "Wikipedia 2026 선거 · 270toWin · Cook Political Report"]:
    d.text((72, y), s, font=F("Regular", 24), fill=DIM); y += 38

y += 10
d.text((72, y), "데이터 기준일 2026-08-27 · 점수는 공개 근거에 기반한 저자 판단입니다.",
       font=F("Regular", 23), fill=LOAD)
im.save(f"{OUT}/card_5_method.png")


# ============================================================ 6. 여론
im, d = base(6)
y = eyebrow(d, 130, "왜 양당이 같이 움직이나")
d.text((72, y), "공화당 지지층도", font=F("Black", 58), fill=INK); y += 72
d.text((72, y), "찬반이 갈립니다", font=F("Black", 58), fill=LOAD); y += 100
d.text((72, y), "텍사스 · 우리 지역 데이터센터 건설", font=F("Medium", 27), fill=MUTE); y += 58

ORDER = [("ALL","전체"),("REPUBLICAN","공화당 지지"),("INDEPENDENT","무당층"),
         ("DEMOCRAT","민주당 지지"),("RURAL","농촌"),("SUBURBAN","교외")]
for key, lab in ORDER:
    o = opin.get(key)
    if not o: continue
    d.text((72, y), lab, font=F("Medium", 27), fill=INK)
    net = o["net_pct"]
    d.text((W - 72, y), f"{net:+.0f}", font=M(28, True),
           fill=ALERT if net < 0 else DEM, anchor="ra")
    y += 40
    bar_w = 936
    sup_w = int(bar_w * o["support_pct"] / 100)
    opp_w = int(bar_w * o["oppose_pct"] / 100)
    d.rectangle([72, y, 72 + bar_w, y + 34], fill="#0E1319")
    d.rectangle([72, y, 72 + sup_w, y + 34], fill=DEM)
    d.rectangle([72 + sup_w, y, 72 + sup_w + opp_w, y + 34], fill=ALERT)
    d.text((72 + sup_w // 2, y + 17), f"{o['support_pct']:.0f}", font=M(20, True),
           fill="#0E1319", anchor="mm")
    d.text((72 + sup_w + opp_w // 2, y + 17), f"{o['oppose_pct']:.0f}", font=M(20, True),
           fill="#0E1319", anchor="mm")
    y += 54

y += 8
d.text((72, y), "■ 찬성", font=F("Regular", 22), fill=DEM)
d.text((190, y), "■ 반대", font=F("Regular", 22), fill=ALERT)
y += 48
d.line([(72, y), (W - 72, y)], fill=RULE, width=1); y += 26
para(d, 72, y,
  "공화당 지지층만 45 대 43으로 갈립니다. 나머지 모든 집단은 반대가 압도적입니다. "
  "양당 후보가 나란히 규제로 가는 이유가 여기 있습니다.",
  F("Regular", 27), MUTE, 936, 44)
im.save(f"{OUT}/card_6_opinion.png")

print("saved:", sorted(os.listdir(OUT)))
