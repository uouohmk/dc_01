import os
import sys
import datetime
import re
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("오류: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# 인자들을 하나의 문자열로 결합 (버그 수정 부분)
new_poll_text = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
if not new_poll_text:
    print("입력된 여론조사 데이터가 없습니다.")
    sys.exit(0)

today_str = datetime.date.today().strftime("%m%d")
script_filename = f"scripts/12_update_{today_str}.py"

prompt = f"""
당신은 U.S. Midterm × Data Center Political Risk Tracker의 데이터 엔지니어입니다.
아래의 [새 여론조사/뉴스 데이터]를 분석하여 SQLite DB(data/tracker.db)에 적재하는 독립된 파이썬 스크립트를 작성해주세요.

[규칙]
1. P1~P4 원칙을 반드시 준수할 것 (Fact와 Analysis 분리, 정당 소속만으로 입장 추론 금지, 근거 필수).
2. 기존 2024년 과거 대진이나 출마하지 않는 인물(예: GA Kemp)은 배제할 것.
3. scripts/06_update_0829.py 또는 10_update_0902.py와 동일한 코딩 스타일로 작성할 것.
4. SQLite connection을 열고 polling, source, change_log 등의 테이블에 정확히 INSERT 할 것.
5. 오직 실행 가능한 파이썬 코드만 마크다운 코드블록(```python ... ```)으로 출력할 것. 설명 문장은 일절 배제할 것.

[새 여론조사/뉴스 데이터]:
{new_poll_text}
"""

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt
)

code = response.text
code = re.sub(r"^```python\s*", "", code, flags=re.MULTILINE)
code = re.sub(r"^```\s*$", "", code, flags=re.MULTILINE)

with open(script_filename, "w", encoding="utf-8") as f:
    f.write(code.strip() + "\n")

print(f"새 갱신 스크립트 생성 완료: {script_filename}")
