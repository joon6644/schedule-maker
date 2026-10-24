# Schedule Maker

명지대 시간표 조합 생성기. 두 개의 프론트엔드가 같은 강의 데이터와 같은 알고리즘을 공유한다.

- `web/` — 웹 프론트엔드 (Vite + React + TypeScript + Tailwind v4). 서버 없는 정적 앱.
- `schedule_maker/` — PySide6 데스크톱 앱 (기존).
- `tools/export_courses.py` — `data/csv/*.csv` → `web/public/data/*.json` 변환 (데스크톱과 같은 파서 사용).

## 알고리즘 일관성
- 웹 엔진 `web/src/engine/generator.ts`는 Python `schedule_maker/services/scheduler.py`의 이식판이다. 한쪽을 바꾸면 다른 쪽도 같이 바꾼다.
- `web/src/engine/generator.test.ts`에 Python 결과와 맞춰 둔 기대값(4478, 8984, 2257, 209)이 있다. 알고리즘을 바꾸면 Python 쪽에서 값을 다시 확인한다.

## 디자인 시스템 규칙 (Figma 연동)
- 색·반경·그림자는 `web/src/styles/tokens.css`의 토큰만 사용한다. hex 값을 컴포넌트에 직접 쓰지 않는다. Tailwind 기본 팔레트는 꺼져 있다.
- 색 원칙 60·30·10: 강조색은 `accent` 하나뿐. 필수/희망 같은 역할에 색을 따로 주지 않는다(필수 = accent, 나머지 = 중립). 빨강(`danger`)은 오류·삭제 확인에만.
- 강의 색 10개는 OKLCH 같은 밝기·채도에 hue 만 36° 간격 (대비 7:1 이상). 새 색이 필요하면 같은 방식으로 계산한다.
- 버튼 위계: 한 영역에 primary 하나, 나머지는 secondary(회색 채움)·ghost(글자). 배지는 neutral·accent·warning 세 가지만. 목록 삭제는 `RemoveButton`, 추가는 `AddRow`.
- Figma 변수 `color/surface/raised` ↔ CSS `--color-surface-raised` ↔ Tailwind `bg-surface-raised`.
- 기본 컴포넌트는 `web/src/components/ui.tsx`에 있고 Figma 컴포넌트와 이름·variant가 같다. 새 UI는 먼저 여기 있는 컴포넌트를 조합한다.
- 아이콘은 `lucide-react`.
- Figma 링크를 받으면: `get_variable_defs`로 토큰 차이를 먼저 반영 → `get_design_context`로 구조 확인 → 기존 컴포넌트로 구현 → `get_screenshot`과 실제 화면 비교.
- Figma 파일: fileKey `ocYp0Lpe3PB396q6nJhr6c` (Starter 플랜: 컬렉션당 모드 1개 → `Color · Light`/`Color · Dark` 분리, MCP 읽기 월 20회라 읽기 호출은 아껴 쓸 것)
- 자세한 내용: `docs/figma-workflow.md`

## 명령
- 웹: `cd web && npm run dev | npm test | npm run build`
- Python 테스트: `venv/Scripts/python -m pytest`
- 이 PC의 사용자 PATH에 잘못된 따옴표가 있어 npm 스크립트가 `node`를 못 찾을 수 있다. PowerShell에서 `$env:Path = $env:Path -replace '"', ''` 후 실행한다.
