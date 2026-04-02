"""
REMARK 월간 학부모 리포트 엔진 v2
─────────────────────────────────
주요 개선사항:
  · 3개월 추이 그래프 (SVG 스파크라인)
  · 반 평균 vs 개인 비교 차트
  · AI 맞춤 코멘트 자동 생성 (enhance_comments_v2.py 연동)
  · 상담 예약 CTA 버튼

사용법:
  1. STUDENTS 리스트에 이번 달 데이터 입력
  2. python3 enhance_comments_v2.py   ← AI 코멘트 생성
  3. python3 generate_report_v2.py    ← HTML 생성
"""

import os, json, math, base64

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
TMPL_PATH  = os.path.join(BASE_DIR, 'report_template_v2.html')
LOGO_PATH  = os.path.expanduser(
    '~/Desktop/0.REMARK_MASTER/1. 행정/03.마케팅/디자인/로고/리마크영어국어/png/리마크영어국어-화이트.png')
ENHANCED_PATH = os.path.join(BASE_DIR, 'enhanced_students.json')

# ─────────────────────────────────────────────────────────────
# ★ 여기만 매달 수정 ★
# ─────────────────────────────────────────────────────────────
THIS_MONTH  = "4월"
SCHOOL_YEAR = "2026"
CTA_LINK    = "https://open.kakao.com/o/XXXXXXXX"   # 오픈채팅 or 전화번호 링크

STUDENTS = [
    # ── 중3 ──
    {
        "name": "김준섭",    "nickname": "준섭이",
        "school": "미강중",  "grade": "3",
        "teacher_name": "김세령",
        "homework_pct": 85,
        "monthly_score": 94, "monthly_total": 100,
        "weekly_score": 26,  "weekly_total": 28,
        "participation": 4,  "participation_label": "좋음",
        # 최근 3개월 점수 (없으면 None)
        "score_history": [
            {"month": "2월", "score": None,  "total": 100},
            {"month": "3월", "score": 92,    "total": 100},
            {"month": "4월", "score": 94,    "total": 100},
        ],
        "wrong_answers": [12, 19],
    },
    # ── 필요한 만큼 추가 ──
]
# ─────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════
# 헬퍼
# ══════════════════════════════════════════════════════════════

def load_logo_b64():
    with open(LOGO_PATH, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def load_enhanced():
    if not os.path.exists(ENHANCED_PATH):
        print("  [주의] enhanced_students.json 없음 — AI 코멘트 미포함")
        return {}
    with open(ENHANCED_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {d['name']: d for d in data}


def gauge_color(pct):
    if pct >= 90:   return '#1f5c30'
    if pct >= 70:   return '#34a853'
    if pct >= 60:   return '#b8860b'
    return '#c53030'


def gauge_offset(pct):
    return round(2 * math.pi * 34 * (1 - pct / 100), 1)


def traffic_label(score, total):
    pct = round(score / total * 100)
    if pct >= 80: return ('traffic-green', '우수')
    if pct >= 60: return ('traffic-yellow', '안정적')
    return ('traffic-red', '보강 필요')


def stars_html(n):
    return '★' * n + '<span class="dim">☆</span>' * (5 - n)


# ── 반 평균 계산 ────────────────────────────────────────────

def class_avg(students):
    scores = [s['monthly_score'] for s in students if s.get('monthly_score') is not None]
    if not scores: return None
    return round(sum(scores) / len(scores), 1)


# ── SVG 스파크라인 (3개월 추이) ─────────────────────────────

def build_trend_chart(history):
    """history: [{"month":str, "score":int|None, "total":int}]"""
    W, H = 220, 80
    PAD_X, PAD_Y = 28, 14

    valid = [(i, h) for i, h in enumerate(history) if h.get('score') is not None]
    months = [h['month'] for h in history]

    if len(valid) < 1:
        return ''

    # 점 좌표 계산
    n = len(history)
    step = (W - PAD_X * 2) / max(n - 1, 1)
    pts = []
    for i, h in valid:
        pct = h['score'] / h['total'] * 100
        x = round(PAD_X + i * step, 1)
        y = round(H - PAD_Y - (pct / 100) * (H - PAD_Y * 2), 1)
        pts.append((x, y, h['score'], h['total'], h['month'], pct))

    # 연결선
    polyline = ' '.join(f'{x},{y}' for x, y, *_ in pts)
    line_svg = f'<polyline points="{polyline}" fill="none" stroke="#1f5c30" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'

    # 음영 채우기
    if len(pts) >= 2:
        fill_pts = polyline + f' {pts[-1][0]},{H-PAD_Y} {pts[0][0]},{H-PAD_Y}'
        line_svg += f'<polygon points="{fill_pts}" fill="#1f5c30" opacity="0.08"/>'

    # 점 + 라벨
    dots_svg = ''
    for x, y, score, total, month, pct in pts:
        color = gauge_color(pct)
        dots_svg += f'''
        <circle cx="{x}" cy="{y}" r="5" fill="{color}" stroke="white" stroke-width="2"/>
        <text x="{x}" y="{y-10}" text-anchor="middle" font-size="11" font-weight="700" fill="{color}">{score}</text>'''

    # 월 라벨 (X축)
    labels_svg = ''
    for i, m in enumerate(months):
        x = round(PAD_X + i * step, 1)
        labels_svg += f'<text x="{x}" y="{H-2}" text-anchor="middle" font-size="10" fill="#8a9b90">{m}</text>'

    # 기준선 (80%)
    y80 = round(H - PAD_Y - 0.8 * (H - PAD_Y * 2), 1)
    guide = f'<line x1="{PAD_X}" y1="{y80}" x2="{W-PAD_X}" y2="{y80}" stroke="#e4ebe6" stroke-width="1" stroke-dasharray="4,3"/>'
    guide += f'<text x="{PAD_X-4}" y="{y80+4}" text-anchor="end" font-size="9" fill="#b0bcb4">80</text>'

    svg = f'''<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px;display:block;">
  {guide}{line_svg}{dots_svg}{labels_svg}
</svg>'''
    return svg


# ── 반 평균 비교 가로 막대 ───────────────────────────────────

def build_avg_chart(student_score, student_total, avg):
    if student_score is None or avg is None:
        return ''
    s_pct  = round(student_score / student_total * 100, 1)
    a_pct  = avg
    s_color = gauge_color(s_pct)
    a_color = '#94a3b8'
    max_w   = 160  # px 기준 최대 너비

    s_bar = round(s_pct / 100 * max_w)
    a_bar = round(a_pct / 100 * max_w)

    return f'''<div class="avg-chart">
  <div class="avg-row">
    <div class="avg-label">내 점수</div>
    <div class="avg-bar-wrap">
      <div class="avg-bar" style="width:{s_bar}px;background:{s_color};"></div>
      <span class="avg-val" style="color:{s_color};">{student_score}점 ({s_pct:.0f}%)</span>
    </div>
  </div>
  <div class="avg-row">
    <div class="avg-label">반 평균</div>
    <div class="avg-bar-wrap">
      <div class="avg-bar" style="width:{a_bar}px;background:{a_color};"></div>
      <span class="avg-val" style="color:{a_color};">{avg}점 ({a_pct:.0f}%)</span>
    </div>
  </div>
</div>'''


# ── 점수 개요 카드 ───────────────────────────────────────────

def build_score_overview(s):
    if s.get('monthly_score') is None:
        return ''
    cls, label = traffic_label(s['monthly_score'], s['monthly_total'])
    pct  = round(s['monthly_score'] / s['monthly_total'] * 100)
    col  = gauge_color(pct)
    return f'''<div class="metric">
  <div class="bar" style="background:linear-gradient(90deg,#059669,#34d399);"></div>
  <div class="cap">월간 평가</div>
  <div class="big-num">{s['monthly_score']}<span class="of">/{s['monthly_total']}</span></div>
  <span class="traffic-badge {cls}">{label}</span>
  <div class="prog-wrap"><div class="prog">
    <div class="prog-fill" style="width:{pct}%;background:{col};"></div>
  </div></div>
</div>'''


def build_score_detail(s):
    if s.get('monthly_score') is None:
        return ''
    rows = f'''<div class="score-tr">
    <span class="k">월간 테스트</span>
    <span class="v">{s['monthly_score']} / {s['monthly_total']}점</span>
  </div>'''
    if s.get('weekly_score') is not None:
        rows += f'''<div class="score-tr">
    <span class="k">주간 테스트</span>
    <span class="v">{s['weekly_score']} / {s['weekly_total']}점</span>
  </div>'''
    return f'<div class="section"><div class="section-head"><div class="section-dot" style="background:var(--green);"></div><div class="section-label">평가 결과</div></div><div class="score-table">{rows}</div></div>'


def build_insight_card(label, text, dot_color, tag_icon, tag_label):
    if not text:
        return ''
    return f'''<div class="section">
  <div class="section-head">
    <div class="section-dot" style="background:{dot_color};"></div>
    <div class="section-label">{label}</div>
  </div>
  <div class="insight">
    <div class="insight-tag"><span class="pip">{tag_icon}</span> {tag_label}</div>
    <div class="insight-body">{text}</div>
  </div>
</div>'''


def build_diagnosis_card(enhanced):
    if not enhanced:
        return ''
    diag    = enhanced.get('weakness_diagnosis', '')
    actions = enhanced.get('improvement_actions', [])
    if not diag and not actions:
        return ''
    acts_html = ''.join(
        f'<div class="diag-action-item"><div class="diag-dot"></div><span>{a}</span></div>'
        for a in actions
    )
    return f'''<div class="section">
  <div class="section-head">
    <div class="section-dot" style="background:#6b3fa0;"></div>
    <div class="section-label">이달의 학습 진단</div>
  </div>
  <div class="diag-box">
    <div class="diag-pattern-label"><span class="pip">🔍</span> 핵심 취약 패턴</div>
    <div class="diag-pattern-body">{diag}</div>
    <div class="diag-actions-label"><span class="pip">💡</span> 이렇게 해봐요</div>
    {acts_html}
  </div>
</div>'''


# ══════════════════════════════════════════════════════════════
# 렌더
# ══════════════════════════════════════════════════════════════

def render(template, s, logo_b64, enhanced_map, avg):
    enc = enhanced_map.get(s['name'], {})
    teacher_comment = enc.get('teacher_comment') or s.get('teacher_comment', '')
    growth_text     = enc.get('growth_text')     or s.get('growth_text')
    improve_text    = enc.get('improve_text')    or s.get('improve_text')
    observation     = enc.get('observation_text') or s.get('observation_text', '')

    trend_svg   = build_trend_chart(s.get('score_history', []))
    avg_chart   = build_avg_chart(s.get('monthly_score'), s.get('monthly_total', 100), avg)

    repl = {
        '{{logo_base64}}':          logo_b64,
        '{{student_name}}':         s['name'],
        '{{school}}':               s['school'],
        '{{grade}}':                s['grade'],
        '{{this_month}}':           THIS_MONTH,
        '{{school_year}}':          SCHOOL_YEAR,
        '{{homework_pct}}':         str(s['homework_pct']),
        '{{gauge_color}}':          gauge_color(s['homework_pct']),
        '{{gauge_offset}}':         str(gauge_offset(s['homework_pct'])),
        '{{score_overview_card}}':  build_score_overview(s),
        '{{score_detail_section}}': build_score_detail(s),
        '{{participation_stars}}':  stars_html(s['participation']),
        '{{participation_label}}':  s['participation_label'],
        '{{observation_text}}':     observation,
        '{{growth_card}}':          build_insight_card('이달의 성장', growth_text, 'var(--green)', '↑', '성장 포인트'),
        '{{improve_card}}':         build_insight_card('함께 다듬어갈 부분', improve_text, 'var(--orange)', '→', '다음 목표'),
        '{{diagnosis_card}}':       build_diagnosis_card(enc),
        '{{trend_chart}}':          trend_svg,
        '{{avg_chart}}':            avg_chart,
        '{{teacher_comment}}':      teacher_comment,
        '{{teacher_name}}':         s['teacher_name'],
        '{{teacher_initial}}':      s['teacher_name'][0] if s['teacher_name'] else '',
        '{{cta_link}}':             CTA_LINK,
    }
    html = template
    for k, v in repl.items():
        html = html.replace(k, str(v))
    return html


# ══════════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════════

def main():
    with open(TMPL_PATH, 'r', encoding='utf-8') as f:
        template = f.read()
    logo_b64     = load_logo_b64()
    enhanced_map = load_enhanced()
    avg          = class_avg(STUDENTS)

    out_dir = os.path.join(BASE_DIR, f'output_{THIS_MONTH}')
    os.makedirs(out_dir, exist_ok=True)

    kakao_list = []
    for s in STUDENTS:
        html = render(template, s, logo_b64, enhanced_map, avg)
        fname = f"{s['name']}_{THIS_MONTH}_월간리포트.html"
        path  = os.path.join(out_dir, fname)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'  ✅ {path}')

        enc = enhanced_map.get(s['name'], {})
        kakao_list.append({
            'name':      s['name'],
            'nickname':  s['nickname'],
            'kakao_text': enc.get('kakao_text') or s.get('kakao_text', ''),
        })

    kakao_path = os.path.join(out_dir, '카톡_발송_목록.json')
    with open(kakao_path, 'w', encoding='utf-8') as f:
        json.dump(kakao_list, f, ensure_ascii=False, indent=2)

    print(f'\n  반 평균: {avg}점')
    print(f'  완료: {len(STUDENTS)}명 → {out_dir}')


if __name__ == '__main__':
    main()
