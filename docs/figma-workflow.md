# Figma 협업 가이드

웹 프론트엔드(`web/`)와 Figma 디자인을 **Figma MCP**로 연결해, 디자이너(사람)와 Claude가 같은 디자인 시스템을 보며 작업하는 방법입니다.

## 1. 연결 (최초 1회)

Figma 원격 MCP 서버(`https://mcp.figma.com/mcp`)를 사용합니다. 아래 중 하나를 고르세요.

| 사용 환경 | 방법 |
|---|---|
| Claude 데스크톱 앱 / claude.ai | 설정 → 커넥터에서 **Figma** 연결 후 Figma 계정으로 로그인 |
| Claude Code CLI | 이 저장소의 [`.mcp.json`](../.mcp.json)에 이미 등록되어 있음. `claude` 실행 후 `/mcp` → `figma` → 로그인 |

연결되면 Claude가 `get_design_context`, `get_variable_defs`, `get_screenshot`, `get_metadata` 등의 도구를 사용할 수 있습니다.

> 참고: Figma 플랜/시트(Dev·Full seat)에 따라 MCP 호출 횟수에 제한이 있을 수 있습니다.

## 디자인 파일

- 파일: [시간표 메이커 (Figma)](https://www.figma.com/design/ocYp0Lpe3PB396q6nJhr6c) — fileKey `ocYp0Lpe3PB396q6nJhr6c`
- `Page 1`
  - `Components` 프레임 (node `9:2`): `CourseBlock` (`9:37`, color=1~8), `Badge` (`9:50`, tone), `Button` (`9:59`, variant)
  - `Desktop / 시간표` 프레임 (node `10:2`): 1440×900, 웹 앱 데스크톱 화면

### Starter(무료) 플랜이라 달라진 점
- 컬렉션 하나에 모드를 하나만 만들 수 있어서, Light/Dark를 **`Color · Light`, `Color · Dark` 두 컬렉션**으로 나눴습니다. 두 컬렉션의 변수 이름은 같습니다. 화면은 `Color · Light`에 바인딩되어 있습니다.
  - 유료 플랜(Professional 이상)으로 바꾸면 한 컬렉션의 Light/Dark 모드로 합칠 수 있습니다.
- MCP 읽기 호출이 월 20회로 제한됩니다. 변수·화면 생성 같은 쓰기 작업은 한도에서 빠집니다.
- Figma에 Pretendard가 없어 화면 글꼴은 **Noto Sans KR**(Regular/Medium/Bold)로 대체했습니다. 코드는 Pretendard를 그대로 씁니다.

## 2. Figma 파일 구성 규칙

코드와 이름이 1:1로 맞아야 Claude가 디자인을 정확히 코드로 옮길 수 있습니다.

### 페이지
- **Tokens** — 변수(Variables) 정의 화면
- **Components** — 아래 컴포넌트 목록과 같은 이름의 컴포넌트
- **Screens** — `Desktop / 강의 검색`, `Desktop / 시간표`, `Mobile / 시간표` 처럼 `기기 / 화면` 이름의 프레임

### 변수(Variables) ↔ 디자인 토큰

단일 출처는 [`web/src/styles/tokens.css`](../web/src/styles/tokens.css)입니다. Figma 변수 이름의 `/`를 `-`로 바꾸면 CSS 변수 이름이 됩니다. 모든 변수에는 코드 이름(`var(--color-…)`)이 지정되어 있어 Dev Mode에서 바로 보입니다.

| Figma 컬렉션 / 변수 | CSS 변수 | Tailwind 클래스 예 |
|---|---|---|
| Color · Light/Dark / `color/surface/raised` | `--color-surface-raised` | `bg-surface-raised` |
| Color · Light/Dark / `color/surface/default` | `--color-surface` | `bg-surface` |
| Color · Light/Dark / `color/fg/muted` | `--color-fg-muted` | `text-fg-muted` |
| Color · Light/Dark / `color/accent/default` | `--color-accent` | `bg-accent` |
| Color · Light/Dark / `color/course/3/bg` | `--color-course-3-bg` | (시간표 블록, 인라인 스타일) |
| Radius / `radius/md` | `--radius-md` | `rounded-md` |
| 이펙트 스타일 `shadow/md` | `--shadow-md` | `shadow-md` |

- `surface`, `fg`, `accent`처럼 하위 토큰(`surface-raised` 등)이 있는 토큰은 Figma에서 그룹과 이름이 겹칠 수 없어 **`…/default`**로 끝납니다.
- `Color · Dark` 컬렉션이 `[data-theme='dark']` 블록에 해당합니다.
- Tailwind 기본 팔레트는 꺼 두었기 때문에(`--color-*: initial`) **토큰에 없는 색은 코드에서 쓸 수 없습니다.** 새 색이 필요하면 Figma 변수를 먼저 추가하세요.
- 글꼴: Pretendard Variable

### 컴포넌트 ↔ 코드

| Figma 컴포넌트 | 속성(Variant) | 코드 |
|---|---|---|
| Button | variant: primary/secondary/ghost/danger, size: sm/md | `web/src/components/ui.tsx` `Button` |
| IconButton | size: sm/md | `IconButton` |
| Badge | tone: neutral/accent/required/desired/warning | `Badge` |
| Segmented | size: sm/md | `Segmented` |
| Panel | — | `Panel` |
| Stepper | — | `Stepper` |
| CourseBlock | color: 1~8, pinned: true/false | `web/src/features/Timetable.tsx` |
| Timetable | — | `Timetable` |

아이콘은 [Lucide](https://lucide.dev) 세트를 사용합니다 (Figma의 Lucide 플러그인과 같은 이름).

## 3. 작업 흐름

### Figma → 코드 (디자인을 바꿨을 때)
1. Figma에서 바뀐 프레임/컴포넌트를 선택하고 **링크 복사** (`Copy link to selection`)
2. Claude에게 링크와 함께 요청
   - "이 링크대로 시간표 화면 업데이트해줘"
   - "Tokens 페이지 변수 바뀐 거 코드에 반영해줘"
3. Claude는 `get_variable_defs`로 토큰을 먼저 맞추고(`tokens.css`), `get_design_context`로 구조를 읽어 해당 컴포넌트를 수정한 뒤, `get_screenshot` 이미지와 실제 화면을 비교해 확인합니다.

### 코드 → Figma (코드에서 먼저 만들었을 때)
1. `npm run dev`로 화면을 띄워 확인
2. Claude에게 "tokens.css 기준으로 Figma 변수 목록 정리해줘"라고 요청하면, Figma에 그대로 만들 수 있는 변수 표를 만들어 줍니다.
3. Figma MCP가 캔버스 쓰기 기능을 지원하는 플랜/버전이라면 화면을 Figma 프레임으로 바로 가져오도록 요청할 수 있습니다. 지원하지 않으면 화면 캡처를 기준으로 Figma에서 다시 구성합니다.

### 리뷰
- Figma 댓글로 피드백 → 링크를 Claude에게 전달 → 수정 후 스크린샷으로 확인
- 디자인 결정(새 토큰, 새 컴포넌트)은 Figma에 먼저 반영하고 코드가 따라가는 것을 원칙으로 합니다.

## 4. 로컬 실행

```bash
cd web
npm install
npm run dev     # http://localhost:5173
npm test        # 엔진 테스트 (Python 엔진과 결과 일치 검증 포함)
npm run build   # dist/ 정적 파일 생성
```

강의 데이터(`web/public/data/*.json`)는 `data/csv/`의 CSV에서 만듭니다. 새 학기 CSV를 넣은 뒤:

```bash
python tools/export_courses.py
```
