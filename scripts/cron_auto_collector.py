import os
import sys
import datetime
import re
import sqlite3
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("오류: GEMINI_API_KEY가 없습니다.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

today_str = datetime.date.today().strftime("%m%d")
script_filename = f"scripts/12_update_{today_str}.py"

# Gemini에게 실시간 검색(Search Grounding) 도구를 쥐어주고 270toWin 및 최신 여론조사 추적 지시
prompt = """
당신은 U.S. Midterm × Data Center Political Risk Tracker의 수석 데이터 엔지니어입니다.
https://www.270towin.com/content/2026-senate-polling 페이지 및 2026년 미국 연방 상원/주지사 선거의 최신 여론조사(Polling)를 검색하세요.

[수집 및 검증 규칙]
1. 2026년 대진만 수집할 것 (2024년 과거 대진인 Brown vs Moreno, Cruz vs Allred 등은 엄격히 제외).
2. 출마하지 않는 가상 대진(예: GA Kemp vs Ossoff)은 제외할 것.
3. 확인 가능한 사실(조사기관, 조사일자, 샘플 수, 후보별 지지율)만 수집할 것.
4. 만약 최근 1~2주 내에 새로운 유효 여론조사가 전혀 없다면, 정확히 "NO_NEW_POLL" 이라고만 출력하세요.
5. 새로운 조사가 있다면, data/tracker.db의 polling, source, change_log 테이블에 적재하는 독립된 실행 가능 파이썬 스크립트 코드만 마크다운(```python ... ```)으로 출력하세요. 설명 문장은 일절 금지합니다.
"""

print("최신 여론조사 자동 검색 및 분석 중...")
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt,
    config=types.GenerateContentConfig(
        tools=[{"google_search": {}}] # 실시간 웹 검색 활성화
    )
)

text = response.text.strip()

if "NO_NEW_POLL" in text or len(text) < 50:
    print("새로운 여론조사가 없거나 변동 사항이 없습니다. 파이프라인을 종료합니다.")
    sys.exit(0)

code = re.sub(r"^```python\s*", "", text, flags=re.MULTILINE)
code = re.sub(r"^```\s*$", "", code, flags=re.MULTILINE)

with open(script_filename, "w", encoding="utf-8") as f:
    f.write(code.strip() + "\n")

print(f"새로운 여론조사 감지! 갱신 스크립트 작성 완료: {script_filename}")
