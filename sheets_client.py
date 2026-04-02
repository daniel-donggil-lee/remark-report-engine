"""
Google Sheets 읽기/쓰기 클라이언트
~/.clasprc.json OAuth2 토큰 재사용
"""
import json
from datetime import datetime
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

CLASPRC = Path.home() / '.clasprc.json'


def get_creds():
    with open(CLASPRC) as f:
        tokens = json.load(f)['tokens']['default']
    creds = Credentials(
        token         = tokens.get('access_token'),
        refresh_token = tokens.get('refresh_token'),
        token_uri     = 'https://oauth2.googleapis.com/token',
        client_id     = tokens['client_id'],
        client_secret = tokens['client_secret'],
        scopes        = ['https://www.googleapis.com/auth/spreadsheets'],
    )
    if creds.expired or not creds.valid:
        creds.refresh(Request())
    return creds


def get_service(spreadsheet_id):
    creds = get_creds()
    svc   = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    return svc.spreadsheets(), spreadsheet_id


# ─────────────────────────────────────────────────────────────
# 읽기
# ─────────────────────────────────────────────────────────────

def read_sheet(spreadsheet_id, sheet_name, range_='A:Z'):
    ss, sid = get_service(spreadsheet_id)
    result  = ss.values().get(
        spreadsheetId=sid,
        range=f'{sheet_name}!{range_}',
    ).execute()
    rows = result.get('values', [])
    if len(rows) < 2:
        return []
    header = rows[0]
    return [
        {header[i]: row[i] if i < len(row) else '' for i in range(len(header))}
        for row in rows[1:]
    ]


def read_students(spreadsheet_id, sheet_name='학생_마스터'):
    """학생명단 탭 → [{이름, 닉네임, 학교, 학년, 담당강사, 학부모전화, 슬러그}, ...]"""
    return read_sheet(spreadsheet_id, sheet_name)


def read_weekly_scores(spreadsheet_id, sheet_name='학생_기록', target_date=None):
    """
    주간점수 탭에서 target_date(YYYY-MM-DD) 행 추출.
    target_date=None이면 최신 날짜 행 자동 선택.
    반환: [{날짜, 이름, R점수, R총점, K점수, K총점, 과제, 출결}, ...]
    """
    rows = read_sheet(spreadsheet_id, sheet_name)
    if not rows:
        return [], None

    if target_date:
        filtered = [r for r in rows if r.get('날짜', '') == target_date]
        return filtered, target_date

    # 최신 날짜 자동 탐지
    dates = sorted(set(r.get('날짜', '') for r in rows if r.get('날짜')), reverse=True)
    latest = dates[0] if dates else None
    filtered = [r for r in rows if r.get('날짜', '') == latest]
    return filtered, latest


def read_monthly_scores(spreadsheet_id, sheet_name='월간점수', year_month=None):
    """
    월간점수 탭. year_month 예: '2026-04'
    반환: [{년월, 이름, 점수, 총점, 과제%, 참여도, 틀린문항}, ...]
    """
    rows = read_sheet(spreadsheet_id, sheet_name)
    if not rows:
        return [], None
    if year_month:
        filtered = [r for r in rows if r.get('년월', '') == year_month]
        return filtered, year_month
    months = sorted(set(r.get('년월', '') for r in rows if r.get('년월')), reverse=True)
    latest = months[0] if months else None
    filtered = [r for r in rows if r.get('년월', '') == latest]
    return filtered, latest


def read_teacher_memos(spreadsheet_id, sheet_name='강사메모', year_month=None):
    """강사메모 탭. 반환: [{년월, 이름, raw_growth, raw_improve, raw_comment, 특이사항}, ...]"""
    rows = read_sheet(spreadsheet_id, sheet_name)
    if not year_month:
        months = sorted(set(r.get('년월', '') for r in rows if r.get('년월')), reverse=True)
        year_month = months[0] if months else None
    return [r for r in rows if r.get('년월', '') == year_month], year_month


def read_monthly_history(spreadsheet_id, sheet_name='월간점수', student_name=None, last_n=3):
    """학생별 최근 N개월 점수 이력"""
    rows = read_sheet(spreadsheet_id, sheet_name)
    if student_name:
        rows = [r for r in rows if r.get('이름', '') == student_name]
    months = sorted(set(r.get('년월', '') for r in rows if r.get('년월')), reverse=True)
    recent = months[:last_n]
    result = []
    for ym in sorted(recent):
        for r in rows:
            if r.get('년월') == ym and r.get('이름') == student_name:
                result.append({
                    'month': ym[5:] + '월',   # '2026-04' → '4월'
                    'score': int(r['점수']) if r.get('점수') else None,
                    'total': int(r['총점']) if r.get('총점') else 100,
                })
    return result


# ─────────────────────────────────────────────────────────────
# 쓰기
# ─────────────────────────────────────────────────────────────

def append_log(spreadsheet_id, sheet_name='발송내역', row_data: list = None):
    """발송내역 탭에 1행 추가"""
    if not row_data:
        return
    ss, sid = get_service(spreadsheet_id)
    ss.values().append(
        spreadsheetId=sid,
        range=f'{sheet_name}!A:E',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': [row_data]},
    ).execute()


def log_send(spreadsheet_id, send_type, student_name, url, status, sheet_name='발송내역'):
    """발송 이력 기록: [날짜, 유형, 이름, URL, 상태]"""
    date = datetime.now().strftime('%Y-%m-%d %H:%M')
    append_log(spreadsheet_id, sheet_name, [date, send_type, student_name, url, status])
