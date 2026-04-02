#!/usr/bin/env python3
"""
영어 주간 리포트 — 데모 생성기 (Sheets·API 연결 없이 더미 데이터로 즉시 생성)
실행: python3 demo/generate_english_demo.py
출력: demo/english-sample.html
"""
import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from report_engine import load_logo_b64, load_template, render_english_weekly

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'english-sample.html')

# ─────────────────────────────────────────────────────────────
# 더미 데이터
# ─────────────────────────────────────────────────────────────
STUDENT = {
    'name':            '이서연',
    'school':          '미사고',
    'grade':           '고2',
    'teacher_name':    '권보경',
    'phone':           '010-0000-0000',
    'slug':            'lee-seoyeon',
    'exams': [
        {'시험유형': '단어',  '맞은수': '20', '전체수': '20', '재시여부': 'X'},
        {'시험유형': '문법',  '맞은수': '14', '전체수': '20', '재시여부': 'X'},
        {'시험유형': '독해',  '맞은수': '8',  '전체수': '10', '재시여부': 'X'},
    ],
    'overall_correct': 42,
    'overall_total':   50,
    'overall_pct':     84,
    'memo':            '이번 주 문법 파트에서 관계대명사 구분을 어려워했지만, 수업 후 재확인에서 깔끔하게 정리했어요. 독해 속도도 눈에 띄게 빨라지고 있습니다.',
    'history': [
        {'month': '03-24', 'score': 38, 'total': 50},
        {'month': '03-31', 'score': 40, 'total': 50},
        {'month': '04-07', 'score': 42, 'total': 50},
    ],
}

WEEK_LABEL  = '2026-04-07'
AI_COMMENT  = '이번 주 단어 시험을 완벽하게 마무리하며 꾸준한 암기 습관을 잘 보여주었어요. 독해 속도와 정확도가 함께 오르고 있어 다음 주 결과도 기대됩니다.'
REPORT_URL  = 'https://www.remarkedu.com/report/english/2026-04-07/lee-seoyeon.html'
CTA_LINK    = 'https://open.kakao.com/o/XXXXXXXX'

# ─────────────────────────────────────────────────────────────
# 생성
# ─────────────────────────────────────────────────────────────
print('⏳ 영어 데모 리포트 생성 중...')

logo_b64 = load_logo_b64()
template = load_template('weekly_en')
html     = render_english_weekly(template, STUDENT, logo_b64, WEEK_LABEL, AI_COMMENT, REPORT_URL)

# CTA 링크 데모용으로 교체
html = html.replace(CTA_LINK, CTA_LINK)

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'✅ 생성 완료: {OUT_PATH}')
