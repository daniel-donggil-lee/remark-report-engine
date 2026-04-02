#!/usr/bin/env python3
"""
REMARK 학부모 리포트 엔진 — 단일 진입점
─────────────────────────────────────────
사용법:
  python3 run.py weekly               # 주간 리포트 전체 발송
  python3 run.py weekly --dry-run     # 발송 없이 HTML만 생성
  python3 run.py weekly --student 이름  # 1명만 처리

  python3 run.py monthly              # 월간 리포트 전체 발송
  python3 run.py monthly --dry-run
  python3 run.py monthly --student 이름
"""

import os, sys, json, argparse
from datetime import datetime
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(BASE_DIR, 'output')
os.makedirs(os.path.join(OUT_DIR, 'weekly'),  exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'monthly'), exist_ok=True)

from config        import ACADEMY, SHEETS
from sheets_client import (
    read_students, read_weekly_scores, read_monthly_scores,
    read_teacher_memos, read_monthly_history, log_send,
)
from ai_comments   import weekly_comment, monthly_comments_batch
from report_engine import (
    load_logo_b64, load_template, class_avg,
    render_weekly, render_monthly,
)
from sender import send_batch

SID = ACADEMY['spreadsheet_id']


# ══════════════════════════════════════════════════════════════
# 공통 유틸
# ══════════════════════════════════════════════════════════════

def _student_filter(students, name_filter):
    if not name_filter:
        return students
    return [s for s in students if s.get('이름', '') == name_filter or s.get('name', '') == name_filter]


def _slug_url(slug, report_type, label):
    base = ACADEMY['report_base_url'].rstrip('/')
    return f'{base}/{report_type}/{label}/{slug}.html'


# ══════════════════════════════════════════════════════════════
# 주간 파이프라인
# ══════════════════════════════════════════════════════════════

def run_weekly(dry_run=False, student_filter=None, target_date=None):
    print('\n══════════════════════════════════════')
    print('  주간 리포트 파이프라인')
    print('══════════════════════════════════════')

    # [1] Sheets 읽기
    print('\n[1/5] Google Sheets 읽기')
    master_rows = read_students(SID, SHEETS['학생명단'])
    master      = {r['이름']: r for r in master_rows}

    weekly_rows, week_date = read_weekly_scores(SID, SHEETS['주간점수'], target_date)
    if not weekly_rows:
        print('  ❌ 주간 데이터 없음')
        return
    week_label = week_date or datetime.now().strftime('%Y-%m-%d')
    print(f'  날짜: {week_label}, {len(weekly_rows)}명 데이터')

    if student_filter:
        weekly_rows = _student_filter(weekly_rows, student_filter)
        print(f'  필터: {student_filter} ({len(weekly_rows)}명)')

    # [2] 학생 객체 조합
    students = []
    for row in weekly_rows:
        name = row.get('이름', '')
        info = master.get(name, {})
        s = {
            'name':         name,
            'school':       info.get('학교', ''),
            'grade':        info.get('학년', ''),
            'teacher_name': info.get('담당강사', ''),
            'phone':        info.get('학부모전화', ''),
            'slug':         info.get('슬러그', name),
            'r_score':      int(row.get('R점수', 0)  or 0),
            'r_total':      int(row.get('R총점', 9)  or 9),
            'k_score':      int(row.get('K점수', 0)  or 0),
            'k_total':      int(row.get('K총점', 28) or 28),
            'homework':     row.get('과제', 'O'),
            'attendance':   row.get('출결', 'O'),
            'teacher_note': row.get('강사메모', ''),
        }
        students.append(s)

    # [3] AI 한줄 평
    print('\n[2/5] AI 한줄 평 생성 (Haiku)')
    for s in students:
        print(f'  ⏳ {s["name"]} ... ', end='', flush=True)
        s['ai_comment'] = weekly_comment(s)
        print('✅')

    # [4] HTML 생성
    print('\n[3/5] HTML 생성')
    template = load_template('weekly')
    logo_b64 = load_logo_b64()
    out_week_dir = os.path.join(OUT_DIR, 'weekly', week_label)
    os.makedirs(out_week_dir, exist_ok=True)

    for s in students:
        url   = _slug_url(s['slug'], 'weekly', week_label)
        html  = render_weekly(template, s, logo_b64, week_label, s['ai_comment'], url)
        fname = os.path.join(out_week_dir, f"{s['name']}_{week_label}_주간리포트.html")
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(html)
        s['report_url'] = url
        print(f'  ✅ {fname}')

    # [5] 카톡 발송
    print(f'\n[4/5] 카톡 발송 (dry_run={dry_run})')
    kakao_targets = []
    for s in students:
        kakao_text = (
            f"안녕하세요, 리마크학원 {s['teacher_name']}입니다.\n\n"
            f"{s['name']} 학생의 {week_label} 주간 리포트를 보내드립니다.\n\n"
            f"{s['ai_comment']}\n\n"
            f"자세한 내용: {s['report_url']}"
        )
        kakao_targets.append({'name': s['name'], 'phone': s['phone'], 'text': kakao_text})

    results = send_batch(kakao_targets, dry_run=dry_run)

    # [6] 발송내역 기록
    if not dry_run:
        print('\n[5/5] 발송내역 기록')
        for s, r in zip(students, results):
            status = '성공' if r.get('ok') else '실패'
            log_send(SID, '주간', s['name'], s['report_url'], status, SHEETS['발송내역'])

    ok   = sum(1 for r in results if r.get('ok'))
    fail = len(results) - ok
    print(f'\n  완료: {ok}건 성공, {fail}건 실패')
    print(f'  출력: {out_week_dir}')


# ══════════════════════════════════════════════════════════════
# 월간 파이프라인
# ══════════════════════════════════════════════════════════════

def run_monthly(dry_run=False, student_filter=None, year_month=None):
    print('\n══════════════════════════════════════')
    print('  월간 리포트 파이프라인')
    print('══════════════════════════════════════')

    # [1] Sheets 읽기
    print('\n[1/5] Google Sheets 읽기')
    master_rows  = read_students(SID, SHEETS['학생명단'])
    master       = {r['이름']: r for r in master_rows}

    monthly_rows, ym = read_monthly_scores(SID, SHEETS['월간점수'], year_month)
    memo_rows,    _  = read_teacher_memos(SID,  SHEETS['강사메모'],  ym)
    if not monthly_rows:
        print('  ❌ 월간 데이터 없음')
        return
    print(f'  기간: {ym}, {len(monthly_rows)}명 데이터')

    # 년월 → 표시용 (예: '2026-04' → '4월', '2026')
    this_month  = ym[5:].lstrip('0') + '월' if ym else ''
    school_year = ym[:4] if ym else ''

    memo_map = {r.get('이름', ''): r for r in memo_rows}

    if student_filter:
        monthly_rows = _student_filter(monthly_rows, student_filter)
        print(f'  필터: {student_filter} ({len(monthly_rows)}명)')

    # [2] 학생 객체 조합
    students_raw = []
    for row in monthly_rows:
        name  = row.get('이름', '')
        info  = master.get(name, {})
        memo  = memo_map.get(name, {})
        wrong = [int(x.strip()) for x in (row.get('틀린문항', '') or '').split(',')
                 if x.strip().isdigit()]
        history = read_monthly_history(SID, SHEETS['월간점수'], name, last_n=3)
        s = {
            'name':              name,
            'school':            info.get('학교', ''),
            'grade':             info.get('학년', ''),
            'teacher_name':      info.get('담당강사', ''),
            'teacher':           info.get('담당강사', ''),
            'phone':             info.get('학부모전화', ''),
            'slug':              info.get('슬러그', name),
            'monthly_score':     int(row.get('점수', 0)   or 0),
            'monthly_total':     int(row.get('총점', 100) or 100),
            'homework_pct':      int(row.get('과제%', 0)  or 0),
            'participation':     int(row.get('참여도', 3) or 3),
            'participation_label': _participation_label(int(row.get('참여도', 3) or 3)),
            'wrong_answers':     wrong,
            'score_history':     history,
            'raw_growth':        memo.get('raw_growth', ''),
            'raw_improve':       memo.get('raw_improve', ''),
            'raw_comment':       memo.get('raw_comment', ''),
            'attendance_note':   memo.get('특이사항', ''),
        }
        students_raw.append(s)

    # [3] AI 월간 코멘트
    print('\n[2/5] AI 월간 코멘트 생성 (Sonnet)')
    enhanced_list = monthly_comments_batch(students_raw)
    enhanced_map  = {e['name']: e for e in enhanced_list}

    # [4] HTML 생성
    print('\n[3/5] HTML 생성')
    template = load_template('monthly')
    logo_b64 = load_logo_b64()
    avg      = class_avg(students_raw)
    out_month_dir = os.path.join(OUT_DIR, 'monthly', ym or 'latest')
    os.makedirs(out_month_dir, exist_ok=True)

    for s in students_raw:
        enc  = enhanced_map.get(s['name'], {})
        url  = _slug_url(s['slug'], 'monthly', ym)
        html = render_monthly(template, s, logo_b64, enc, avg, this_month, school_year)
        fname = os.path.join(out_month_dir, f"{s['name']}_{this_month}_월간리포트.html")
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(html)
        s['report_url']  = url
        s['kakao_text']  = enc.get('kakao_text', '')
        print(f'  ✅ {fname}')

    # 카톡 발송 목록 JSON 저장
    kakao_path = os.path.join(out_month_dir, '카톡_발송_목록.json')
    kakao_list = [{'name': s['name'], 'phone': s['phone'],
                   'kakao_text': s.get('kakao_text', '')} for s in students_raw]
    with open(kakao_path, 'w', encoding='utf-8') as f:
        json.dump(kakao_list, f, ensure_ascii=False, indent=2)

    # [5] 카톡 발송
    print(f'\n[4/5] 카톡 발송 (dry_run={dry_run})')
    kakao_targets = [
        {'name': s['name'], 'phone': s['phone'],
         'text': s.get('kakao_text') or f"안녕하세요, {s['name']} 학생 {this_month} 월간 리포트입니다.\n{s['report_url']}"}
        for s in students_raw
    ]
    results = send_batch(kakao_targets, dry_run=dry_run)

    # [6] 발송내역 기록
    if not dry_run:
        print('\n[5/5] 발송내역 기록')
        for s, r in zip(students_raw, results):
            status = '성공' if r.get('ok') else '실패'
            log_send(SID, '월간', s['name'], s['report_url'], status, SHEETS['발송내역'])

    ok   = sum(1 for r in results if r.get('ok'))
    fail = len(results) - ok
    print(f'\n  반 평균: {avg}점')
    print(f'  완료: {ok}건 성공, {fail}건 실패')
    print(f'  출력: {out_month_dir}')


def _participation_label(n: int) -> str:
    return {1: '노력 필요', 2: '보통', 3: '양호', 4: '좋음', 5: '매우 좋음'}.get(n, '양호')


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='REMARK 학부모 리포트 엔진')
    parser.add_argument('mode',      choices=['weekly', 'monthly'])
    parser.add_argument('--dry-run', action='store_true', help='발송 없이 HTML만 생성')
    parser.add_argument('--student', type=str, default=None, help='특정 학생만 처리')
    parser.add_argument('--date',    type=str, default=None,
                        help='주간: YYYY-MM-DD | 월간: YYYY-MM  (기본: 최신)')
    args = parser.parse_args()

    if args.mode == 'weekly':
        run_weekly(dry_run=args.dry_run, student_filter=args.student, target_date=args.date)
    else:
        run_monthly(dry_run=args.dry_run, student_filter=args.student, year_month=args.date)


if __name__ == '__main__':
    main()
