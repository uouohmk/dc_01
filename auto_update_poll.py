# scripts/auto_monitor_polls.py
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import os
import sys
import datetime
import re
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("GEMINI_API_KEY 미설정")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)
TRACKED_FILE = "data/processed_urls.txt"

# 1. 이미 처리한 기사 URL 로드
os.makedirs("data", exist_ok=True)
processed_urls = set()
if os.path.exists(TRACKED_FILE):
    with open(TRACKED_FILE, "r", encoding="utf-8") as f:
        processed_urls = set(line.strip() for line in f if line.strip())

# 2. 감시할 검색 키워드 (Google News RSS 활용)
queries = [
    '"2026 senate" poll data center',
    '"2026 senate poll" ohio OR michigan OR texas',
    '"2026 governor poll" texas OR oregon OR "new york"',
    'data center moratorium "2026"'
]

new_articles = []
for q in queries:
    encoded_q = urllib.parse.quote(q)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        xml_data = urllib.request.urlopen(req, timeout=10).read()
        root = ET.fromstring(xml_data)
        for item in root.findall(".//item"):
            link = item.find("link").text
            title = item.find("title").text
            pub_date = item.find("pubDate").text
            if link not in processed_urls:
                new_articles.append({"title": title, "link": link, "date": pub_date})
                processed_urls.add(link)
    except Exception as e:
        print(f"검색 실패 ({q}): {e}")

if not new_articles:
    print("새롭게 발견된 기사/여론조사가 없습니다.")
    sys.exit(0)

print(f"새로운 기사/신호 {len(new_articles)}건 발견. Gemini 검증 시작...")

# 3. Gemini에게 유효 여론조사인지 판별 및 스크립트 작성 요청
articles_summary = "\n".join([f"- 제목: {a['title']} (일자: {a['date']}, 링크: {a['link']})" for a in new_articles[:10]])

prompt = f"""
당신은 U.S. Midterm × Data Center Political Risk Tracker의 데이터 엔지니어입니다.
아래의 최근 뉴스/자료 목록을 검토하세요.

[자료 목록]:
{articles_summary}

[작업 지침]
1. 위 목록 중 '2026년 미국 중간선거(상원·주지사) 본선 여론조사 수치' 또는 '데이터센터 주 단위 규제/후보 공식 입장'이 포함된 유효 데이터가 있는지 확인하세요.
2. 2024년 과거 선거 대진이거나 단순 추측 기사라면 오직 'NO_VALID_DATA'라고만 출력하세요.
3. 실제 2026 선거 여론조사/정책 데이터가 있다면, P1~P4 원칙에 맞게 SQLite DB(data/tracker.db)의 polling, source, change_log 테이블에 적재하는 단독 실행 파이썬 코드를 작성하세요.
4. 유효한 경우 설명 없이 순수 파이썬 코드만 마크다운 코드블록(```python ... ```)으로 출력하세요.
"""

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt
)

res_text = response.text.strip()
if "NO_VALID_DATA" in res_text or not res_text.startswith("```python"):
    print("유효한 2026 선거 신규 여론조사/정책 데이터가 발견되지 않았습니다.")
    # URL 히스토리만 저장하여 중복 재조회 방지
    with open(TRACKED_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(processed_urls))
    sys.exit(0)

# 4. 새 스크립트 파일 저장
today_str = datetime.date.today().strftime("%m%d")
script_filename = f"scripts/12_update_{today_str}.py"

code = re.sub(r"^```python\s*", "", res_text, flags=re.MULTILINE)
code = re.sub(r"^```\s*$", "", code, flags=re.MULTILINE)

with open(script_filename, "w", encoding="utf-8") as f:
    f.write(code)

with open(TRACKED_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(processed_urls))

print(f"새로운 여론조사 반영 스크립트 자동 생성 완료: {script_filename}")
