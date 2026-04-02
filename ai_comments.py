"""
AI 코멘트 자동 생성
  - 주간: Claude Haiku → 1~2문장 한줄 평
  - 월간: Claude Sonnet → 6개 필드 JSON (enhance_comments_v2.py 로직 통합)
"""
import json, os
import anthropic

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QB_PATH  = os.path.join(BASE_DIR, 'question_bank_v2.json')

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _load_qb():
    if not os.path.exists(QB_PATH):
        return {}
    with open(QB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _wrong_summary(wrong_answers: list, grade: str, qb: dict) -> str:
    """틀린 문항 → 스킬 요약 (question_bank 조회)"""
    # grade 예: '중3', '고1' → key '3.0', '1.0'
    num = ''.join(c for c in grade if c.isdigit())
    key = str(float(num)) if num else '0'
    bank = qb.get(key, {})
    lines = []
    for q in sorted(wrong_answers or []):
        info = bank.get(str(q), {})
        lines.append(f'  {q}번 [{info.get("area","미분류")}] {info.get("concept","정보 없음")}')
    return '\n'.join(lines) if lines else '데이터 없음'


# ──────────────────────────────────────────────────────────────
# 주간: 한줄 평
# ──────────────────────────────────────────────────────────────

def weekly_comment(student: dict) -> str:
    """
    student: {name, grade, school, r_score, r_total, k_score, k_total,
              homework, attendance, teacher_note(optional)}
    반환: 1~2문장 한줄 평 (plain text)
    """
    r_p = round(student['r_score'] / student['r_total'] * 100) if student.get('r_total') else 0
    k_p = round(student['k_score'] / student['k_total'] * 100) if student.get('k_total') else 0
    note = student.get('teacher_note') or ''

    prompt = f"""리마크영어국어학원 {student.get('grade','')} {student['name']} 학생의 이번 주 수업 결과입니다.

- R(개념) 점수: {student['r_score']}/{student['r_total']} ({r_p}%)
- K(유지) 점수: {student['k_score']}/{student['k_total']} ({k_p}%)
- 과제 이행: {student.get('homework','O')}
- 출결: {student.get('attendance','O')}
{f"- 강사 메모: {note}" if note else ""}

학부모에게 보낼 한줄 평을 1~2문장으로 작성해주세요.
- 따뜻하고 전문적인 톤, 해요체
- 성적이 좋으면 격려, 아쉬우면 구체적 보완점 1가지
- 문장만 출력 (따옴표, 접두사 없이)"""

    msg = _get_client().messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=200,
        messages=[{'role': 'user', 'content': prompt}],
    )
    return msg.content[0].text.strip()


# ──────────────────────────────────────────────────────────────
# 월간: 6개 필드 JSON
# ──────────────────────────────────────────────────────────────

def monthly_comment(student: dict) -> dict:
    """
    student: {name, grade, school, teacher, monthly_score, monthly_total,
              homework_pct, wrong_answers, raw_growth, raw_improve, raw_comment,
              attendance_note(optional)}
    반환: {weakness_diagnosis, improvement_actions, observation_text,
            growth_text, teacher_comment, kakao_text, name}
    """
    qb = _load_qb()
    ws = _wrong_summary(student.get('wrong_answers', []), student.get('grade', ''), qb)
    note = student.get('attendance_note') or ''
    teacher = student.get('teacher', '담당 강사')

    prompt = f"""리마크영어국어학원 {student.get('grade','')} {student['name']} 학생의 월간 학습 리포트를 작성합니다.

【기본 정보】
- 학생: {student['name']} ({student.get('grade','')}, {student.get('school','')})
- 담당 강사: {teacher}
- 월간 테스트: {student.get('monthly_score',0)}점 / {student.get('monthly_total',100)}점
- 과제 수행률: {student.get('homework_pct',0)}%
{f"- 특이사항: {note}" if note else ""}

【강사 원본 관찰 메모】
- 성장 포인트: {student.get('raw_growth') or "(없음)"}
- 보완점: {student.get('raw_improve') or "(없음)"}
- 종합 코멘트: {student.get('raw_comment') or "(없음)"}

【틀린 문항 스킬 분석】
{ws}

아래 6개 필드를 JSON으로 작성해 주세요.

작성 지침:
1. weakness_diagnosis (3~4문장): 틀린 문항의 공통 패턴 인지적 관점 서술 ("X번 틀림" 식 나열 금지)
2. improvement_actions (배열, 2~3가지): 즉시 실천 가능한 작은 습관 (예: "문제 바꾸기 전 근거 10초 확인하기")
3. observation_text (2~3문장): 수업 중 태도·참여도·반응 관찰
4. growth_text (2~3문장 또는 null): 성장 근거 없으면 null
5. teacher_comment (4~5문장): 따뜻하고 전문적인 해요체 코멘트
6. kakao_text (3~4문장): 첫줄 "안녕하세요, 리마크학원 {teacher}입니다.\\n\\n" 시작, 핵심만 해요체

JSON만 출력:
{{
  "name": "{student['name']}",
  "weakness_diagnosis": "...",
  "improvement_actions": ["...", "..."],
  "observation_text": "...",
  "growth_text": "..." 또는 null,
  "teacher_comment": "...",
  "kakao_text": "..."
}}"""

    msg = _get_client().messages.create(
        model='claude-sonnet-4-6',
        max_tokens=2000,
        messages=[{'role': 'user', 'content': prompt}],
    )
    raw   = msg.content[0].text
    start = raw.find('{')
    end   = raw.rfind('}') + 1
    return json.loads(raw[start:end])


def monthly_comments_batch(students):
    """여러 학생 월간 코멘트 일괄 생성"""
    results = []
    for s in students:
        print(f'  ⏳ [{s["name"]}] AI 월간 코멘트 생성 중...')
        result = monthly_comment(s)
        results.append(result)
        print(f'  ✅ 완료: {result.get("weakness_diagnosis","")[:40]}...')
    return results
