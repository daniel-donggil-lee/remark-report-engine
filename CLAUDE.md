# 월간리포트엔진 v2

**GitHub**: https://github.com/daniel-donggil-lee/remark-report-engine
**GitHub Pages 데모**: https://daniel-donggil-lee.github.io/remark-report-engine/demo/readin-sample.html

---

## 프로젝트 개요

학원 학부모 리포트 자동화 엔진. 고등국어 R/K 점수 기반 주간·월간 리포트 HTML 생성 + 카카오 친구톡 발송.
B2B SaaS 방향으로 확장 예정 — `config.py` 교체만으로 타 학원 배포 가능한 구조.

---

## 파일 구조

```
월간리포트엔진_v2/
├── config.py              # 학원 설정 (gitignore — 배포 시 config.example.py 복사)
├── config.example.py      # B2B 납품용 템플릿
├── run.py                 # 엔트리포인트: python3 run.py weekly/monthly [--dry-run]
├── sheets_client.py       # Google Sheets r/w (clasprc.json OAuth2)
├── report_engine.py       # HTML 렌더링 + SVG 차트 생성
├── ai_comments.py         # Claude Haiku(주간) / Sonnet(월간) AI 코멘트
├── sender.py              # Solapi BMS 카카오 친구톡 발송
├── question_bank_v2.json  # 틀린 문항 → 스킬 매핑 DB
├── templates/
│   ├── monthly.html       # 월간 리포트 템플릿
│   └── weekly.html        # 주간 리포트 템플릿
└── demo/
    ├── generate_readin_demo.py   # 독서논술 데모 생성 스크립트
    └── readin-sample.html        # 생성된 데모 (GitHub Pages 배포)
```

---

## Google Sheets 연동

**스프레드시트 ID**: `17oD2prV7kF35L-7iPf6EeGq7UDEJvgqcHXXY3tib4mQ` (리마크 리포트 엔진 전용 시트)

| 탭명 | 컬럼 |
|------|------|
| 엔진_학생명단 | 이름 / 닉네임 / 학교 / 학년 / 담당강사 / 학부모전화 / 슬러그 |
| 엔진_주간점수 | 날짜 / 이름 / R점수 / R총점 / K점수 / K총점 / 과제 / 출결 |
| 엔진_월간점수 | 년월 / 이름 / 점수 / 총점 / 과제% / 참여도 / 틀린문항 |
| 엔진_강사메모 | 년월 / 이름 / raw_growth / raw_improve / raw_comment / 특이사항 |
| 엔진_발송내역 | 날짜 / 유형 / 이름 / URL / 상태 |
| 엔진_영어_학생명단 | 이름 / 학교 / 학년 / 담당강사 / 학부모전화 / 슬러그 |
| 엔진_영어_수업기록 | 날짜 / 이름 / 수업내용 / 시험유형 / 맞은수 / 전체수 / 재시상태 / 재시점수 / 재시약속일 / 강사메모 |
| 엔진_영어_발송내역 | 날짜 / 이름 / URL / 상태 |

---

## 핵심 설계

- **신호등**: 🟢 R≥80%&K≥75% / 🔴 R<65% or K<65% / 🟡 그 외
- **AI 코멘트**: 주간 → Haiku 1~2문장, 월간 → Sonnet 6개 필드 JSON
- **SVG 차트**: `build_trend_chart()` (3개월 추이 스파크라인), `build_avg_chart()` (반 평균 비교)
- **Python 3.9 호환**: `float | None` union 타입 사용 금지 → 타입 힌트 제거

---

## 실행 방법

```bash
# 주간 dry-run
python3 run.py weekly --dry-run

# 월간 특정 학생
python3 run.py monthly --student 홍길동 --dry-run

# 독서논술 데모 재생성
python3 demo/generate_readin_demo.py
open -g demo/readin-sample.html
```

---

## B2B 확장 전략

- 독립 독서논술 학원 대상 (리드인 프랜차이즈 포함)
- 본사 시스템 대체 X → 보완 레이어 (3개월 추이 + AI 코멘트 + 비주얼 차트)
- 강사 추가 부담: 월 약 20분 (주 1회 Sheets 입력 5분)
- 데모 링크 하나로 영업: GitHub Pages HTML 공유

---

## 호스팅 구조

- **도메인**: remarkedu.com → **Vercel** 호스팅
- **GitHub 레포**: `donggillee-ship-it/remark-homepage` (Next.js)
- **리포트 서빙**: `public/report/` 폴더 → `remarkedu.com/report/...` 정적 파일로 직접 서빙
- **영어 리포트 URL**: `https://www.remarkedu.com/report/english/{date}/{slug}.html`
- **배포 방식**: GitHub push → Vercel 자동 배포

## 영어 회차 리포트 자동화 (설계 확정, 구현 예정)

**목표**: 수업 당일 밤 10시 자동 발송

**파이프라인**:
```
GitHub Actions cron (22:00 KST)
  → Python: Google Sheets 읽기 (서비스 계정 필요)
  → HTML 생성 → remark-homepage/public/report/english/ 커밋+푸시
  → Vercel 자동 배포
  → Solapi 친구톡 발송 (링크 포함)
```

**시트 구조 (`엔진_영어_수업기록`)**:
- 조교 입력: 날짜 / 이름 / 시험유형 / 맞은수 / 전체수 / 재시상태 / 재시점수 / 재시약속일
- 강사 입력: 수업내용 (같은 반 첫 행만) / 강사메모 (특이사항 있을 때만)
- 재시상태 값: 빈칸(통과) / 당일완료 / 예정 / 이번완료

**담당 강사**: 권보경, 김선정, 윤혜원

**리포트 내용**: 수업내용 + 시험별 결과 막대 + 재시 상태 + 강사메모 (AI 코멘트 없음)

**블로커**: Google Sheets 서비스 계정 전환 필요 (현재 clasprc.json OAuth → 서비스 계정)

## 최근 작업 맥락 (2026-04-02)

- 엔진 전체 모듈 신규 작성 완료: sheets_client / sender / ai_comments / report_engine / run
- 영어과 확장: sheets_client 영어 함수 추가, report_engine build_exam_bars/render_english_weekly, ai_comments english_weekly_comment, run.py english 모드, templates/weekly_en.html
- 스프레드시트 국어내신마스터에서 분리 → 전용 시트 생성 (ID: 17oD2prV7kF35L-7iPf6EeGq7UDEJvgqcHXXY3tib4mQ)
- 영어 데모 HTML 생성: demo/english-sample.html (이서연 더미 데이터)
- 다음 단계: ① 서비스 계정 전환 ② GitHub Actions cron 셋업 ③ 영어 회차 리포트 시트 구조 반영 (엔진_영어_주간시험 → 엔진_영어_수업기록으로 리네임, 컬럼 추가)
