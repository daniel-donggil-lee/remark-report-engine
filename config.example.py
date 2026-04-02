"""
학원별 설정 파일 — B2B 납품 시 이 파일을 config.py로 복사 후 값 교체
"""
import os

ACADEMY = {
    "name":            "학원명",
    "spreadsheet_id":  "YOUR_SPREADSHEET_ID",
    "solapi_key":      "YOUR_SOLAPI_KEY",
    "solapi_secret":   "YOUR_SOLAPI_SECRET",
    "from_number":     "01000000000",
    "kakao_pf_id":     "YOUR_KAKAO_PF_ID",
    "report_base_url": "https://your-domain.com/report/",
    "cta_link":        "https://open.kakao.com/o/XXXXXXXX",
    "logo_path":       os.path.expanduser("~/path/to/logo.png"),
}

# Google Sheets 탭명 (엔진 전용 탭 사용 권장)
SHEETS = {
    "학생명단": "엔진_학생명단",  # 이름, 닉네임, 학교, 학년, 담당강사, 학부모전화, 슬러그
    "주간점수": "엔진_주간점수",  # 날짜, 이름, R점수, R총점, K점수, K총점, 과제, 출결
    "월간점수": "엔진_월간점수",  # 년월, 이름, 점수, 총점, 과제%, 참여도, 틀린문항
    "강사메모": "엔진_강사메모",  # 년월, 이름, raw_growth, raw_improve, raw_comment, 특이사항
    "발송내역": "엔진_발송내역",  # 날짜, 유형, 이름, URL, 상태
}

# 신호등 판정 기준
TRAFFIC = {
    "green":  {"r_min": 80, "k_min": 75},
    "red":    {"r_max": 65, "k_max": 65},
}
