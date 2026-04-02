"""
HTML 렌더링 헬퍼 — 주간·월간 공통 모듈
generate_report_v2.py 함수들을 임포터블 모듈로 이식
"""
import os, math, base64
from config import ACADEMY, TRAFFIC

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
TMPL_DIR   = os.path.join(BASE_DIR, 'templates')


# ─────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────

def load_logo_b64() -> str:
    with open(ACADEMY['logo_path'], 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def load_template(name: str) -> str:
    """name: 'weekly' 또는 'monthly'"""
    path = os.path.join(TMPL_DIR, f'{name}.html')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def gauge_color(pct: float) -> str:
    if pct >= 90: return '#1f5c30'
    if pct >= 70: return '#34a853'
    if pct >= 60: return '#b8860b'
    return '#c53030'


def gauge_offset(pct: float) -> float:
    return round(2 * math.pi * 34 * (1 - pct / 100), 1)


def traffic_light(r_score, r_total, k_score, k_total):
    """
    신호등 판정. 반환: ('green'|'yellow'|'red', label)
    """
    r_p = round(r_score / r_total * 100) if r_total else 0
    k_p = round(k_score / k_total * 100) if k_total else 0
    g = TRAFFIC['green']
    r = TRAFFIC['red']
    if r_p >= g['r_min'] and k_p >= g['k_min']:
        return 'green',  '우수'
    if r_p < r['r_max'] or k_p < r['k_max']:
        return 'red',    '보강 필요'
    return 'yellow', '안정적'


def traffic_label(score, total):
    pct = round(score / total * 100) if total else 0
    if pct >= 80: return ('traffic-green', '우수')
    if pct >= 60: return ('traffic-yellow', '안정적')
    return ('traffic-red', '보강 필요')


def stars_html(n: int) -> str:
    return '★' * n + '<span class="dim">☆</span>' * (5 - n)


def class_avg(students: list):
    scores = [s['monthly_score'] for s in students
              if s.get('monthly_score') is not None]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


# ─────────────────────────────────────────────────────────────
# SVG 차트
# ─────────────────────────────────────────────────────────────

def build_trend_chart(history: list) -> str:
    W, H = 220, 80
    PAD_X, PAD_Y = 28, 14
    valid  = [(i, h) for i, h in enumerate(history) if h.get('score') is not None]
    months = [h['month'] for h in history]
    if not valid:
        return ''
    n    = len(history)
    step = (W - PAD_X * 2) / max(n - 1, 1)
    pts  = []
    for i, h in valid:
        pct = h['score'] / h['total'] * 100
        x   = round(PAD_X + i * step, 1)
        y   = round(H - PAD_Y - (pct / 100) * (H - PAD_Y * 2), 1)
        pts.append((x, y, h['score'], h['total'], h['month'], pct))

    polyline = ' '.join(f'{x},{y}' for x, y, *_ in pts)
    line_svg = (f'<polyline points="{polyline}" fill="none" stroke="#1f5c30" '
                f'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
    if len(pts) >= 2:
        fp = polyline + f' {pts[-1][0]},{H-PAD_Y} {pts[0][0]},{H-PAD_Y}'
        line_svg += f'<polygon points="{fp}" fill="#1f5c30" opacity="0.08"/>'

    dots_svg = ''
    for x, y, score, total, month, pct in pts:
        col = gauge_color(pct)
        dots_svg += (f'<circle cx="{x}" cy="{y}" r="5" fill="{col}" stroke="white" stroke-width="2"/>'
                     f'<text x="{x}" y="{y-10}" text-anchor="middle" font-size="11" '
                     f'font-weight="700" fill="{col}">{score}</text>')

    labels_svg = ''
    for i, m in enumerate(months):
        x = round(PAD_X + i * step, 1)
        labels_svg += (f'<text x="{x}" y="{H-2}" text-anchor="middle" '
                       f'font-size="10" fill="#8a9b90">{m}</text>')

    y80   = round(H - PAD_Y - 0.8 * (H - PAD_Y * 2), 1)
    guide = (f'<line x1="{PAD_X}" y1="{y80}" x2="{W-PAD_X}" y2="{y80}" '
             f'stroke="#e4ebe6" stroke-width="1" stroke-dasharray="4,3"/>'
             f'<text x="{PAD_X-4}" y="{y80+4}" text-anchor="end" font-size="9" fill="#b0bcb4">80</text>')

    return (f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px;display:block;">'
            f'{guide}{line_svg}{dots_svg}{labels_svg}</svg>')


def build_avg_chart(student_score, student_total, avg) -> str:
    if student_score is None or avg is None:
        return ''
    s_pct   = round(student_score / student_total * 100, 1)
    a_pct   = avg
    s_color = gauge_color(s_pct)
    a_color = '#94a3b8'
    max_w   = 160
    s_bar   = round(s_pct / 100 * max_w)
    a_bar   = round(a_pct / 100 * max_w)
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


# ─────────────────────────────────────────────────────────────
# 카드 빌더
# ─────────────────────────────────────────────────────────────

def build_score_overview(s: dict) -> str:
    if s.get('monthly_score') is None:
        return ''
    cls, label = traffic_label(s['monthly_score'], s['monthly_total'])
    pct = round(s['monthly_score'] / s['monthly_total'] * 100)
    col = gauge_color(pct)
    return f'''<div class="metric">
  <div class="bar" style="background:linear-gradient(90deg,#059669,#34d399);"></div>
  <div class="cap">월간 평가</div>
  <div class="big-num">{s['monthly_score']}<span class="of">/{s['monthly_total']}</span></div>
  <span class="traffic-badge {cls}">{label}</span>
  <div class="prog-wrap"><div class="prog">
    <div class="prog-fill" style="width:{pct}%;background:{col};"></div>
  </div></div>
</div>'''


def build_score_detail(s: dict) -> str:
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
    return (f'<div class="section"><div class="section-head">'
            f'<div class="section-dot" style="background:var(--green);"></div>'
            f'<div class="section-label">평가 결과</div></div>'
            f'<div class="score-table">{rows}</div></div>')


def build_insight_card(label, text, dot_color, tag_icon, tag_label) -> str:
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


def build_diagnosis_card(enhanced: dict) -> str:
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


# ─────────────────────────────────────────────────────────────
# 렌더
# ─────────────────────────────────────────────────────────────

def render_monthly(template: str, s: dict, logo_b64: str, enhanced: dict, avg, this_month: str, school_year: str) -> str:
    enc = enhanced or {}
    trend_svg = build_trend_chart(s.get('score_history', []))
    avg_chart = build_avg_chart(s.get('monthly_score'), s.get('monthly_total', 100), avg)

    repl = {
        '{{logo_base64}}':          logo_b64,
        '{{student_name}}':         s['name'],
        '{{school}}':               s.get('school', ''),
        '{{grade}}':                s.get('grade', ''),
        '{{this_month}}':           this_month,
        '{{school_year}}':          school_year,
        '{{homework_pct}}':         str(s.get('homework_pct', 0)),
        '{{gauge_color}}':          gauge_color(s.get('homework_pct', 0)),
        '{{gauge_offset}}':         str(gauge_offset(s.get('homework_pct', 0))),
        '{{score_overview_card}}':  build_score_overview(s),
        '{{score_detail_section}}': build_score_detail(s),
        '{{participation_stars}}':  stars_html(s.get('participation', 0)),
        '{{participation_label}}':  s.get('participation_label', ''),
        '{{observation_text}}':     enc.get('observation_text') or s.get('observation_text', ''),
        '{{growth_card}}':          build_insight_card('이달의 성장', enc.get('growth_text') or s.get('growth_text'), 'var(--green)', '↑', '성장 포인트'),
        '{{improve_card}}':         build_insight_card('함께 다듬어갈 부분', enc.get('improve_text') or s.get('improve_text'), 'var(--orange)', '→', '다음 목표'),
        '{{diagnosis_card}}':       build_diagnosis_card(enc),
        '{{trend_chart}}':          trend_svg,
        '{{avg_chart}}':            avg_chart,
        '{{teacher_comment}}':      enc.get('teacher_comment') or s.get('teacher_comment', ''),
        '{{teacher_name}}':         s.get('teacher_name', ''),
        '{{teacher_initial}}':      s.get('teacher_name', ' ')[0],
        '{{cta_link}}':             ACADEMY['cta_link'],
    }
    html = template
    for k, v in repl.items():
        html = html.replace(k, str(v))
    return html


def build_exam_bars(exams: list) -> str:
    """영어 시험유형별 가로막대 HTML. 70% 기준선 + 재시상태 뱃지 포함."""
    if not exams:
        return '<p style="color:#9ca3af;font-size:13px;">시험 데이터 없음</p>'
    rows = ''
    for e in exams:
        correct      = int(e.get('맞은수', 0) or 0)
        total        = int(e.get('전체수',  1) or 1)
        pct          = round(correct / total * 100) if total else 0
        retest_stat  = str(e.get('재시상태', '')).strip()
        color        = '#2563EB' if pct >= 70 else '#c53030'

        if not retest_stat:
            badge = '<span class="en-badge en-pass">통과</span>'
        elif retest_stat == '당일완료':
            badge = '<span class="en-badge en-done">당일완료</span>'
        elif retest_stat == '이번완료':
            badge = '<span class="en-badge en-done">이번완료</span>'
        else:  # 예정
            retest_date = e.get('재시약속일', '')
            badge_text  = f'재시 {retest_date}' if retest_date else '재시예정'
            badge       = f'<span class="en-badge en-retest">{badge_text}</span>'

        rows += (
            f'<div class="en-exam-row">'
            f'<div class="en-exam-label">{e.get("시험유형","")}</div>'
            f'<div class="en-bar-wrap">'
            f'<div class="en-bar-bg">'
            f'<div class="en-bar-fill" style="width:{pct}%;background:{color};"></div>'
            f'<div class="en-pass-line"></div>'
            f'</div>'
            f'<div class="en-exam-score">{correct}/{total}&nbsp;<span class="en-pct">({pct}%)</span></div>'
            f'{badge}'
            f'</div>'
            f'</div>'
        )
    return f'<div class="en-exam-bars">{rows}</div>'


def render_english_weekly(template: str, s: dict, logo_b64: str, week_label: str,
                          report_url: str) -> str:
    pct = s.get('overall_pct', 0)
    if pct >= 85:
        tclass, tlabel = 'traffic-green', '우수'
    elif pct >= 70:
        tclass, tlabel = 'traffic-yellow', '안정적'
    else:
        tclass, tlabel = 'traffic-red', '보강 필요'

    trend_svg      = build_trend_chart(s.get('history', []))
    exam_bars      = build_exam_bars(s.get('exams', []))
    lesson_content = s.get('lesson_content', '')
    lesson_html    = (
        f'<div class="card">'
        f'<div class="card-title">이번 회차 수업 내용</div>'
        f'<p style="font-size:13px;line-height:1.7;color:#374151;">{lesson_content}</p>'
        f'</div>'
        if lesson_content else ''
    )
    memo_html = (
        f'<div class="card">'
        f'<div class="en-memo"><span class="en-memo-icon">💬</span>{s["memo"]}</div>'
        f'</div>'
        if s.get('memo') else ''
    )

    repl = {
        '{{logo_base64}}':      logo_b64,
        '{{student_name}}':     s['name'],
        '{{school}}':           s.get('school', ''),
        '{{grade}}':            s.get('grade', ''),
        '{{week_label}}':       week_label,
        '{{overall_pct}}':      str(pct),
        '{{traffic_class}}':    tclass,
        '{{traffic_label}}':    tlabel,
        '{{lesson_section}}':   lesson_html,
        '{{exam_bars}}':        exam_bars,
        '{{trend_chart}}':      trend_svg,
        '{{memo_section}}':     memo_html,
        '{{report_url}}':       report_url,
        '{{cta_link}}':         ACADEMY['cta_link'],
        '{{teacher_name}}':     s.get('teacher_name', ''),
    }
    html = template
    for k, v in repl.items():
        html = html.replace(k, str(v))
    return html


def render_weekly(template: str, s: dict, logo_b64: str, week_label: str,
                  ai_comment: str, report_url: str) -> str:
    r_p = round(s['r_score'] / s['r_total'] * 100) if s.get('r_total') else 0
    k_p = round(s['k_score'] / s['k_total'] * 100) if s.get('k_total') else 0
    light, light_label = traffic_light(s['r_score'], s['r_total'], s['k_score'], s['k_total'])
    combined_score = s['r_score'] + s['k_score']
    combined_total = s['r_total'] + s['k_total']
    combined_pct   = round(combined_score / combined_total * 100) if combined_total else 0

    repl = {
        '{{logo_base64}}':    logo_b64,
        '{{student_name}}':   s['name'],
        '{{school}}':         s.get('school', ''),
        '{{grade}}':          s.get('grade', ''),
        '{{week_label}}':     week_label,
        '{{r_score}}':        str(s['r_score']),
        '{{r_total}}':        str(s['r_total']),
        '{{r_pct}}':          str(r_p),
        '{{k_score}}':        str(s['k_score']),
        '{{k_total}}':        str(s['k_total']),
        '{{k_pct}}':          str(k_p),
        '{{combined_pct}}':   str(combined_pct),
        '{{traffic_class}}':  f'traffic-{light}',
        '{{traffic_label}}':  light_label,
        '{{homework}}':       s.get('homework', 'O'),
        '{{attendance}}':     s.get('attendance', 'O'),
        '{{ai_comment}}':     ai_comment,
        '{{report_url}}':     report_url,
        '{{cta_link}}':       ACADEMY['cta_link'],
        '{{teacher_name}}':   s.get('teacher_name', ''),
    }
    html = template
    for k, v in repl.items():
        html = html.replace(k, str(v))
    return html
