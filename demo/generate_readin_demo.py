#!/usr/bin/env python3
"""
리드인 독서논술 학원 — 학부모 월간 리포트 데모 생성기
실행: python3 demo/generate_readin_demo.py
출력: demo/readin-sample.html
"""
import os, sys, math

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from report_engine import build_trend_chart, gauge_color

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'readin-sample.html')

# ─────────────────────────────────────────────────────────────
# 샘플 데이터
# ─────────────────────────────────────────────────────────────
STUDENT = {
    'name':         '김지율',
    'nickname':     '지율이',
    'school':       '미사초',
    'grade':        '4학년',
    'teacher':      '박선생님',
    'academy':      '미사리드인독서논술',
    'month':        '4월',
    # 이달의 책
    'book_title':   '내 이름은 삐삐롱 스타킹',
    'book_level':   '레벨 3-B',
    'book_author':  '아스트리드 린드그렌',
    # 독서이해도
    'comprehension': 84,
    # 4영역 (100점 만점)
    'vocab':        78,
    'fact':         92,
    'inference':    74,
    'critical':     68,
    # 독서노트
    'notes_done':   4,
    'notes_total':  4,
    # 3개월 추이
    'history': [
        {'month': '2월', 'score': 71,  'total': 100},
        {'month': '3월', 'score': 79,  'total': 100},
        {'month': '4월', 'score': 84,  'total': 100},
    ],
    # 반 평균
    'class_avg': 76,
    # 강사 코멘트 (AI 시뮬레이션)
    'growth_text':   '삐삐의 독특한 시각으로 세상을 바라보는 주인공의 감정을 놀라울 정도로 정확하게 포착했어요. 사실 영역에서 만점에 가까운 점수를 기록한 것은 꼼꼼하게 읽는 독서 습관이 자리 잡혔다는 증거입니다.',
    'improve_text':  '비판 영역에서 "이 이야기에서 무엇이 옳고 그른가?"를 스스로 판단하는 연습이 필요해요. 다음 달에는 읽으면서 "나라면 어떻게 했을까?"를 메모하는 습관을 들여볼게요.',
    'teacher_comment': '지율이는 이번 달 삐삐 롱스타킹을 읽으며 주인공의 자유로운 정신에 깊이 공감하는 모습을 보여주었어요. 특히 등장인물의 마음을 헤아리는 공감 능력이 또래보다 훨씬 뛰어납니다. 비판적 사고는 아직 성장 중이지만, 이 부분은 책을 많이 읽을수록 자연스럽게 발전하는 영역이니 걱정하지 않으셔도 됩니다. 다음 달에는 생각을 글로 표현하는 힘을 더 길러볼 예정입니다. 꾸준히 잘 따라오고 있어서 정말 든든해요.',
    # 추천 도서 (비판 영역 보강)
    'next_book':     '사자왕 형제의 모험',
    'next_reason':   '선악의 경계와 용기의 의미를 스스로 판단하는 비판적 사고 훈련에 최적',
    'next_level':    '레벨 3-B',
}


# ─────────────────────────────────────────────────────────────
# SVG 빌더 — 4영역 가로 막대
# ─────────────────────────────────────────────────────────────
AREA_COLORS = {
    'vocab':     '#4ECDC4',
    'fact':      '#45B7D1',
    'inference': '#96CEB4',
    'critical':  '#FF6B6B',
}
AREA_LABELS = {
    'vocab': '어휘', 'fact': '사실', 'inference': '추론', 'critical': '비판'
}

def build_area_chart(s):
    items = [
        ('vocab',     s['vocab']),
        ('fact',      s['fact']),
        ('inference', s['inference']),
        ('critical',  s['critical']),
    ]
    rows = ''
    for key, score in items:
        color  = AREA_COLORS[key]
        label  = AREA_LABELS[key]
        bar_w  = round(score / 100 * 160)
        weak   = '(취약 영역)' if score < 70 else ''
        style  = 'font-weight:700;' if score < 70 else ''
        rows += f'''
        <div class="area-row">
          <div class="area-label" style="{style}">{label} {weak}</div>
          <div class="area-bar-wrap">
            <div class="area-bar-bg">
              <div class="area-bar-fill" style="width:{bar_w}px;background:{color};"></div>
            </div>
            <span class="area-val" style="color:{color};{style}">{score}</span>
          </div>
        </div>'''
    return f'<div class="area-chart">{rows}</div>'


# ─────────────────────────────────────────────────────────────
# SVG 원형 게이지 (독서이해도)
# ─────────────────────────────────────────────────────────────
def build_comprehension_gauge(pct):
    r       = 54
    circ    = 2 * math.pi * r
    offset  = round(circ * (1 - pct / 100), 1)
    color   = '#FF6B6B' if pct < 70 else ('#F9A825' if pct < 80 else '#4ECDC4')
    label   = '노력 필요' if pct < 70 else ('양호' if pct < 80 else '우수')
    badge_c = '#FF6B6B' if pct < 70 else ('#F9A825' if pct < 80 else '#4ECDC4')
    return f'''<div class="gauge-wrap">
  <svg viewBox="0 0 140 140" width="140" height="140">
    <circle cx="70" cy="70" r="{r}" fill="none" stroke="#f0f0f0" stroke-width="12"/>
    <!-- 70% 기준선 -->
    <circle cx="70" cy="70" r="{r}" fill="none" stroke="#ffe0e0" stroke-width="2"
      stroke-dasharray="{round(circ*0.7,1)} {round(circ*0.3,1)}"
      stroke-dashoffset="{round(circ*0.25,1)}"
      transform="rotate(-90 70 70)"/>
    <circle cx="70" cy="70" r="{r}" fill="none" stroke="{color}" stroke-width="12"
      stroke-linecap="round"
      stroke-dasharray="{round(circ - offset,1)} {round(offset,1)}"
      stroke-dashoffset="{round(circ*0.25,1)}"
      transform="rotate(-90 70 70)"/>
    <text x="70" y="64" text-anchor="middle" font-size="26" font-weight="800" fill="{color}">{pct}%</text>
    <text x="70" y="82" text-anchor="middle" font-size="11" fill="#9ca3af">독서이해도</text>
    <text x="70" y="96" text-anchor="middle" font-size="10" fill="#c0c0c0">통과 기준 70%</text>
  </svg>
  <div class="gauge-badge" style="background:{badge_c};">{label}</div>
</div>'''


# ─────────────────────────────────────────────────────────────
# 반 평균 비교 막대
# ─────────────────────────────────────────────────────────────
def build_class_avg_bar(my_pct, avg_pct):
    my_color  = '#4ECDC4'
    avg_color = '#94a3b8'
    max_w     = 160
    return f'''<div class="avg-chart">
  <div class="avg-row">
    <div class="avg-label">지율이</div>
    <div class="avg-bar-wrap">
      <div class="avg-bar" style="width:{round(my_pct/100*max_w)}px;background:{my_color};"></div>
      <span class="avg-val" style="color:{my_color};">{my_pct}%</span>
    </div>
  </div>
  <div class="avg-row">
    <div class="avg-label">반 평균</div>
    <div class="avg-bar-wrap">
      <div class="avg-bar" style="width:{round(avg_pct/100*max_w)}px;background:{avg_color};"></div>
      <span class="avg-val" style="color:{avg_color};">{avg_pct}%</span>
    </div>
  </div>
</div>'''


# ─────────────────────────────────────────────────────────────
# HTML 렌더
# ─────────────────────────────────────────────────────────────
def render(s):
    trend_svg  = build_trend_chart(s['history'])
    gauge_html = build_comprehension_gauge(s['comprehension'])
    area_html  = build_area_chart(s)
    avg_html   = build_class_avg_bar(s['comprehension'], s['class_avg'])
    notes_pct  = round(s['notes_done'] / s['notes_total'] * 100)

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{s["name"]} — {s["month"]} 독서 성장 리포트</title>
<style>
  :root {{
    --teal:   #4ECDC4;
    --coral:  #FF6B6B;
    --sky:    #45B7D1;
    --green:  #96CEB4;
    --gray:   #6b7280;
    --bg:     #f8f9fc;
    --card:   #ffffff;
    --radius: 16px;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Pretendard', 'Noto Sans KR', sans-serif;
    background: var(--bg);
    color: #1a1a1a;
    min-height: 100vh;
  }}

  /* ── 데모 배너 ── */
  .demo-banner {{
    background: #fff3cd;
    text-align: center;
    font-size: 11px;
    color: #856404;
    padding: 6px;
    font-weight: 600;
    letter-spacing: .04em;
  }}

  /* ── 헤더 ── */
  .header {{
    background: linear-gradient(135deg, #4ECDC4 0%, #45B7D1 100%);
    padding: 24px 20px 20px;
  }}
  .header-academy {{
    font-size: 11px;
    color: rgba(255,255,255,.85);
    letter-spacing: .1em;
    text-transform: uppercase;
    font-weight: 600;
  }}
  .header-name {{
    font-size: 26px;
    font-weight: 800;
    color: white;
    margin-top: 4px;
  }}
  .header-sub {{
    font-size: 13px;
    color: rgba(255,255,255,.8);
    margin-top: 3px;
  }}
  .header-badge {{
    display: inline-block;
    background: rgba(255,255,255,.25);
    color: white;
    font-size: 11px;
    font-weight: 700;
    border-radius: 20px;
    padding: 4px 12px;
    margin-top: 10px;
    letter-spacing: .05em;
  }}

  /* ── 본문 ── */
  .body {{ padding: 14px; max-width: 480px; margin: 0 auto; }}

  /* ── 카드 ── */
  .card {{
    background: var(--card);
    border-radius: var(--radius);
    padding: 16px 18px;
    margin-bottom: 10px;
    box-shadow: 0 1px 6px rgba(0,0,0,.06);
  }}
  .card-title {{
    font-size: 11px;
    font-weight: 700;
    color: var(--gray);
    letter-spacing: .08em;
    text-transform: uppercase;
    margin-bottom: 12px;
  }}

  /* ── 이달의 책 ── */
  .book-card {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: var(--radius);
    padding: 18px 20px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 14px;
  }}
  .book-icon {{ font-size: 36px; }}
  .book-info {{ flex: 1; }}
  .book-sub  {{ font-size: 11px; color: rgba(255,255,255,.75); margin-bottom: 3px; }}
  .book-title {{ font-size: 16px; font-weight: 800; color: white; line-height: 1.3; }}
  .book-meta  {{ font-size: 11px; color: rgba(255,255,255,.7); margin-top: 4px; }}
  .book-level {{
    display: inline-block;
    background: rgba(255,255,255,.25);
    color: white;
    font-size: 10px;
    font-weight: 700;
    border-radius: 10px;
    padding: 2px 8px;
    margin-top: 6px;
  }}

  /* ── 게이지 ── */
  .gauge-wrap {{ text-align: center; }}
  .gauge-badge {{
    display: inline-block;
    color: white;
    font-size: 12px;
    font-weight: 700;
    border-radius: 20px;
    padding: 4px 16px;
    margin-top: 4px;
  }}

  /* ── 4영역 차트 ── */
  .area-chart {{ display: flex; flex-direction: column; gap: 10px; }}
  .area-row   {{ display: flex; align-items: center; gap: 10px; }}
  .area-label {{ font-size: 12px; color: var(--gray); width: 80px; flex-shrink: 0; }}
  .area-bar-wrap {{ flex: 1; display: flex; align-items: center; gap: 8px; }}
  .area-bar-bg   {{ flex: 1; height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden; }}
  .area-bar-fill {{ height: 100%; border-radius: 4px; }}
  .area-val      {{ font-size: 12px; font-weight: 700; width: 32px; text-align: right; flex-shrink: 0; }}

  /* ── 반평균 비교 ── */
  .avg-chart {{ display: flex; flex-direction: column; gap: 8px; }}
  .avg-row   {{ display: flex; align-items: center; gap: 10px; }}
  .avg-label {{ font-size: 12px; color: var(--gray); width: 50px; flex-shrink: 0; }}
  .avg-bar-wrap {{ flex: 1; display: flex; align-items: center; gap: 8px; }}
  .avg-bar   {{ height: 8px; border-radius: 4px; }}
  .avg-val   {{ font-size: 12px; font-weight: 700; flex-shrink: 0; }}

  /* ── 독서노트 ── */
  .notes-row {{ display: flex; align-items: center; gap: 12px; }}
  .notes-count {{ font-size: 32px; font-weight: 800; color: var(--teal); }}
  .notes-label {{ font-size: 12px; color: var(--gray); line-height: 1.5; }}
  .notes-badge {{
    margin-left: auto;
    background: #e8faf8;
    color: var(--teal);
    font-size: 12px;
    font-weight: 700;
    border-radius: 20px;
    padding: 5px 14px;
  }}

  /* ── 인사이트 카드 ── */
  .insight-card {{ margin-bottom: 10px; }}
  .insight-head {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }}
  .insight-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
  .insight-label {{ font-size: 12px; font-weight: 700; color: #374151; }}
  .insight-body {{
    background: #f8f9fc;
    border-radius: 10px;
    padding: 12px 14px;
    font-size: 13px;
    line-height: 1.7;
    color: #374151;
  }}

  /* ── 강사 코멘트 ── */
  .teacher-box {{
    background: linear-gradient(135deg, #f0fffe 0%, #e8f4f8 100%);
    border-radius: var(--radius);
    padding: 16px 18px;
    border-left: 4px solid var(--teal);
    margin-bottom: 10px;
  }}
  .teacher-name {{ font-size: 11px; color: var(--teal); font-weight: 700; margin-bottom: 6px; }}
  .teacher-text {{ font-size: 13px; line-height: 1.8; color: #374151; }}

  /* ── 추천 도서 ── */
  .next-book {{
    background: linear-gradient(135deg, #fff8e1 0%, #fff3cd 100%);
    border-radius: var(--radius);
    padding: 16px 18px;
    margin-bottom: 10px;
    border-left: 4px solid #F9A825;
  }}
  .next-label {{ font-size: 11px; font-weight: 700; color: #7c6200; margin-bottom: 6px; }}
  .next-title {{ font-size: 16px; font-weight: 800; color: #4a3800; }}
  .next-level {{
    display: inline-block;
    background: rgba(249,168,37,.2);
    color: #7c6200;
    font-size: 10px;
    font-weight: 700;
    border-radius: 10px;
    padding: 2px 8px;
    margin: 4px 0;
  }}
  .next-reason {{ font-size: 12px; color: #5a4a00; margin-top: 4px; line-height: 1.5; }}

  /* ── CTA ── */
  .cta-wrap {{ text-align: center; padding: 10px 0 28px; }}
  .btn {{
    display: inline-block;
    background: linear-gradient(135deg, #4ECDC4 0%, #45B7D1 100%);
    color: white;
    font-size: 14px;
    font-weight: 700;
    border-radius: 50px;
    padding: 14px 36px;
    text-decoration: none;
    letter-spacing: .02em;
    box-shadow: 0 4px 14px rgba(78,205,196,.4);
  }}

  /* ── 푸터 ── */
  .footer {{
    text-align: center;
    font-size: 11px;
    color: #9ca3af;
    padding: 8px 16px 20px;
  }}
</style>
</head>
<body>

<div class="demo-banner">📋 이 리포트는 데모 샘플입니다 — 실제 학원 도입 시 맞춤 제작</div>

<div class="header">
  <div class="header-academy">{s["academy"]}</div>
  <div class="header-name">{s["name"]}</div>
  <div class="header-sub">{s["school"]} {s["grade"]} · 담당 {s["teacher"]}</div>
  <div class="header-badge">{s["month"]} 독서 성장 리포트</div>
</div>

<div class="body">

  <!-- 이달의 책 -->
  <div class="book-card">
    <div class="book-icon">📖</div>
    <div class="book-info">
      <div class="book-sub">이번 달 이 책을 함께 읽었어요</div>
      <div class="book-title">《{s["book_title"]}》</div>
      <div class="book-meta">{s["book_author"]}</div>
      <div class="book-level">{s["book_level"]}</div>
    </div>
  </div>

  <!-- 독서이해도 게이지 -->
  <div class="card" style="text-align:center;">
    <div class="card-title">독서 이해도</div>
    {gauge_html}
  </div>

  <!-- 4영역 분석 -->
  <div class="card">
    <div class="card-title">4영역 분석 · 어휘 / 사실 / 추론 / 비판</div>
    {area_html}
  </div>

  <!-- 3개월 성장 추이 + 반 평균 비교 -->
  <div class="card">
    <div class="card-title">3개월 성장 추이</div>
    {trend_svg}
    <div style="margin-top:14px;">
      <div class="card-title">레벨 내 비교</div>
      {avg_html}
    </div>
  </div>

  <!-- 독서노트 -->
  <div class="card">
    <div class="card-title">독서노트 완성</div>
    <div class="notes-row">
      <div class="notes-count">{s["notes_done"]}</div>
      <div class="notes-label">이번 달 독서노트<br><span style="font-size:11px;">목표 {s["notes_total"]}회</span></div>
      <div class="notes-badge">{'완료 🎉' if notes_pct == 100 else f'{notes_pct}%'}</div>
    </div>
  </div>

  <!-- 이달의 성장 -->
  <div class="card insight-card">
    <div class="card-title">이달의 성장</div>
    <div class="insight-head">
      <div class="insight-dot" style="background:var(--teal);"></div>
      <div class="insight-label">성장 포인트</div>
    </div>
    <div class="insight-body">{s["growth_text"]}</div>
  </div>

  <!-- 함께 다듬어갈 부분 -->
  <div class="card insight-card">
    <div class="card-title">함께 다듬어갈 부분</div>
    <div class="insight-head">
      <div class="insight-dot" style="background:var(--coral);"></div>
      <div class="insight-label">다음 목표</div>
    </div>
    <div class="insight-body">{s["improve_text"]}</div>
  </div>

  <!-- 강사 코멘트 -->
  <div class="teacher-box">
    <div class="teacher-name">✏️ {s["teacher"]}의 종합 코멘트</div>
    <div class="teacher-text">{s["teacher_comment"]}</div>
  </div>

  <!-- 다음 달 추천 도서 -->
  <div class="next-book">
    <div class="next-label">📚 다음 달 추천 도서 (비판 영역 집중 보강)</div>
    <div class="next-title">《{s["next_book"]}》</div>
    <div class="next-level">{s["next_level"]}</div>
    <div class="next-reason">{s["next_reason"]}</div>
  </div>

  <!-- CTA -->
  <div class="cta-wrap">
    <a href="#" class="btn">원장님과 상담 예약하기</a>
  </div>

</div>

<div class="footer">{s["academy"]} · 본 리포트는 자동 생성됩니다</div>

</body>
</html>'''


# ─────────────────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    html = render(STUDENT)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✅ 생성 완료: {OUT_PATH}')
