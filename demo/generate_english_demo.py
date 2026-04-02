#!/usr/bin/env python3
"""
영어 수업 리포트 — 데모 생성기 (Sheets·API 연결 없이 더미 데이터로 즉시 생성)
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
        {'시험유형': '단어',  '맞은수': '20', '전체수': '20', '재시상태': ''},
        {'시험유형': '문법',  '맞은수': '12', '전체수': '20', '재시상태': '예정', '재시약속일': '4/10'},
        {'시험유형': '독해',  '맞은수': '8',  '전체수': '10', '재시상태': '이번완료'},
    ],
    'overall_correct': 40,
    'overall_total':   50,
    'overall_pct':     80,
    'lesson_content':  'Unit 7 관계대명사 who / which / that 구분 및 계속적 용법. 독해 지문: The Secret Life of Trees (p.142~145) 핵심 구문 분석.',
    'memo':            '문법 파트에서 관계대명사 계속적 용법을 어려워했습니다. 재시 약속일까지 p.98 예제 전부 풀어오기로 했습니다.',
    'history': [
        {'month': '03-24', 'score': 38, 'total': 50},
        {'month': '03-31', 'score': 40, 'total': 50},
        {'month': '04-07', 'score': 42, 'total': 50},
    ],
}

WEEK_LABEL  = '2026-04-07'
REPORT_URL  = 'https://www.remarkedu.com/report/english/2026-04-07/lee-seoyeon.html'

# ─────────────────────────────────────────────────────────────
# 생성
# ─────────────────────────────────────────────────────────────
print('⏳ 영어 데모 리포트 생성 중...')

logo_b64 = load_logo_b64()
template = load_template('weekly_en')
html     = render_english_weekly(template, STUDENT, logo_b64, WEEK_LABEL, REPORT_URL)

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'✅ 생성 완료: {OUT_PATH}')
