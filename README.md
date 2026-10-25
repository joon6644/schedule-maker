# 시간표 생성기 (명지대학교)

담고 싶은 강의와 조건(학점·공강·피하고 싶은 시간)을 정하면 가능한 시간표 조합을 모두 찾아 줍니다.

**바로 쓰기: https://joon6644.github.io/schedule-maker/**

## 기능

- 강의 검색 → 필수/희망으로 담기 → 시간표가 바로 계산됨
- 시간표의 강의를 고정해 후보 좁히기, 고정한 강의는 다른 분반으로 바꾸기
- 마음에 드는 시간표·조건을 이름 붙여 저장 (이 브라우저에 보관, 서버 없음)
- PC·모바일, 라이트/다크 테마

## 구성

| 폴더 | 내용 |
|---|---|
| `web/` | 웹 앱 (Vite + React + TypeScript). 서버 없는 정적 사이트, 계산은 Web Worker |
| `schedule_maker/` | 데스크톱 앱 (Python + PySide6) — 웹과 같은 알고리즘 |
| `data/csv/` | 학기별 강의 CSV |
| `tools/export_courses.py` | CSV → 웹용 JSON 변환 |

## 개발

```bash
cd web
npm install
npm run dev     # 개발 서버
npm test        # 테스트 (Python 엔진과 결과 일치 검증 포함)
npm run build   # web/dist 생성
```

데스크톱 앱: `pip install -r requirements.txt` 후 `python run.py` · 테스트: `python -m pytest`

`main`에 `web/` 변경을 push하면 GitHub Actions가 GitHub Pages로 자동 배포합니다.

## 새 학기 추가

1. 강의 CSV를 `data/csv/mju_YYYY_N.csv`로 넣기 (예: `mju_2027_1.csv`)
2. `cd web && npm run data` — 최신 학기 JSON 생성, 지난 학기는 정리
3. 커밋 후 `main`에 push → 자동 배포
