"""
REMARK 월간 리포트 AI 코멘트 자동 생성 v2
─────────────────────────────────────────
실행: python3 enhance_comments_v2.py
출력: enhanced_students.json  (generate_report_v2.py가 읽음)

입력 형식 (RAW_STUDENTS):
  - 강사가 짧은 메모(raw_*)만 입력하면 나머지는 AI가 완성
  - 틀린 문항은 question_bank_v2.json에서 스킬명 자동 조회
"""

import json, os, anthropic

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QB_PATH  = os.path.join(BASE_DIR, 'question_bank_v2.json')
OUT_PATH = os.path.join(BASE_DIR, 'enhanced_students.json')

# ─────────────────────────────────────────────────────────────
# ★ 여기만 매달 수정 ★
# ─────────────────────────────────────────────────────────────
THIS_MONTH = "4월"

RAW_STUDENTS = [
    {
        "name": "김준섭",     "grade": "중3",  "school": "미강중",
        "teacher": "김세령",
        "homework_pct": 85,   "monthly_score": 94,
        "wrong_answers": [12, 19],
        "raw_growth":   "독서 추론 능력이 더 향상됨",
        "raw_improve":  "문학 작품 세부 표현 분석 보완 필요",
        "raw_comment":  "심화 내용으로 올려가도 될 것 같음",
        "attendance_note": None,
    },
    # ── 학생 추가 ──
]
# ─────────────────────────────────────────────────────────────


def load_qb():
    if not os.path.exists(QB_PATH):
        return {}
    with open(QB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def wrong_summary(wrong_answers, grade_num, qb):
    key  = str(float(grade_num.replace('중', '')))
    bank = qb.get(key, {})
    lines = []
    for q in sorted(wrong_answers):
        info = bank.get(str(q), {})
        lines.append(f"  {q}번 [{info.get('area','미분류')}] {info.get('concept','정보 없음')}")
    return "\n".join(lines) if lines else "데이터 없음"


def enhance_one(s, qb, client):
    ws = wrong_summary(s['wrong_answers'], s['grade'], qb)
    note = s.get('attendance_note') or ''

    prompt = f"""리마크영어국어학원 {s['grade']} {s['name']} 학생의 {THIS_MONTH} 월간 학습 리포트를 작성합니다.

【기본 정보】
- 학생: {s['name']} ({s['grade']}, {s['school']})
- 담당 강사: {s['teacher']}
- 월간 테스트: {s['monthly_score']}점 / 100점
- 과제 수행률: {s['homework_pct']}%
{f"- 특이사항: {note}" if note else ""}

【강사 원본 관찰 메모】
- 성장 포인트: {s['raw_growth'] or "(없음)"}
- 보완점: {s['raw_improve'] or "(없음)"}
- 종합 코멘트: {s['raw_comment'] or "(없음)"}

【틀린 문항 스킬 분석】
{ws}

아래 6개 필드를 JSON으로 작성해 주세요.

작성 지침:
1. weakness_diagnosis (3~4문장)
   - 틀린 문항의 공통 패턴을 인지적 관점으로 서술 ("X번 틀림" 식 나열 금지)
   - 출석 적은 경우 한계 솔직히 언급
   - 거의 다 맞힌 경우 "현재 강점"과 "한 단계 더 갈 방향" 서술

2. improvement_actions (배열, 2~3가지)
   - 즉시 실천 가능한 작은 습관
   - "매일 2시간 공부" 같은 거창한 것 금지
   - 좋은 예: "문제 바꾸기 전 근거 10초 확인하기"

3. observation_text (2~3문장)
   - 수업 중 태도·참여도·반응 관찰 (강사 원본 메모 기반)
   - "선생님이 호명하지 않아도 / 호명 시" 패턴으로 시작

4. growth_text (2~3문장 또는 null)
   - 성장 근거 없으면 null

5. teacher_comment (4~5문장)
   - 따뜻하고 전문적인 학원 강사 톤
   - 해요체 사용, 합쇼체 금지

6. kakao_text (3~4문장)
   - 첫줄: "안녕하세요, 리마크학원 {s['teacher']}입니다.\\n\\n"
   - 핵심만, 해요체

JSON만 출력:
{{
  "name": "{s['name']}",
  "weakness_diagnosis": "...",
  "improvement_actions": ["...", "..."],
  "observation_text": "...",
  "growth_text": "..." 또는 null,
  "teacher_comment": "...",
  "kakao_text": "..."
}}"""

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw   = msg.content[0].text
    start = raw.find('{')
    end   = raw.rfind('}') + 1
    return json.loads(raw[start:end])


def main():
    qb     = load_qb()
    client = anthropic.Anthropic()
    results = []

    for s in RAW_STUDENTS:
        print(f"  ⏳ [{s['name']}] AI 생성 중...")
        result = enhance_one(s, qb, client)
        results.append(result)
        print(f"  ✅ 완료: {result['weakness_diagnosis'][:40]}...")

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n  저장: {OUT_PATH}")
    print(f"  총 {len(results)}명 처리 완료")


if __name__ == '__main__':
    main()
