# Schedule Maker (명지대학교 시간표 생성기)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Qt for Python](https://img.shields.io/badge/Qt-PySide6-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Schedule Maker**는 명지대학교 학생들을 위한 지능형 시간표 생성 자동화 도구입니다. 
사용자가 원하는 필수/희망 강의와 제약 조건(공강 요일, 최소/최대 학점 등)을 입력하면, 백트래킹 알고리즘을 사용하여 가능한 모든 시간표 조합을 생성하고 시각화해줍니다.

## 🌐 웹 버전 (`web/`)

설치 없이 브라우저(PC·모바일)에서 쓰는 버전입니다. 서버 없이 정적 파일로 동작하고, 시간표 계산은 브라우저의 Web Worker에서 실행됩니다.

```bash
cd web
npm install
npm run dev
```

- 강의 검색 → 필수/희망 담기 → 학점·공강·피하고 싶은 시간 설정 → 시간표가 바로 계산됨
- 시간표의 강의를 고정해 후보 좁히기(다시 누르면 해제), 고정한 강의는 다른 분반으로 바꾸기, ← → 키로 넘기기
- 설정 JSON 불러오기/내보내기 (데스크톱 앱 설정 파일과 호환)
- 라이트/다크 테마, 디자인 토큰은 Figma 변수와 연결 → [docs/figma-workflow.md](docs/figma-workflow.md)

### 새 학기 강의 추가

1. 학교에서 받은 강의 CSV를 `data/csv/mju_YYYY_N.csv` 이름으로 넣습니다 (예: `mju_2027_1.csv`).
2. 웹 데이터 변환: `cd web && npm run data` (= `python tools/export_courses.py`)
3. `npm run build` 후 배포합니다.

- **웹:** 최신 학기만 다룹니다. 변환하면 지난 학기 JSON은 지워지고, 사용자가 다음에 접속하면 새 학기로 넘어가면서 알림이 한 번 뜹니다 (지난 학기에 담은 강의는 정리됨).
- **데스크톱 앱:** 파일 이름 기준으로 가장 최근 학기를 엽니다.

## ✨ 주요 기능 (데스크톱 앱)

- **🖥 현대적인 GUI 환경**: `PySide6`와 `Fluent UI`를 적용하여 깔끔하고 직관적인 사용자 경험을 제공합니다.
- **🔍 강력한 강의 검색**: 강의명, 교수명으로 빠르게 검색하고 클릭 한 번으로 목록에 추가할 수 있습니다.
- **🖱 드래그 앤 드롭**: 강의의 우선순위를 직관적으로 변경하거나 그룹(필수/희망) 간 이동이 가능합니다.
- **⚙️ 정밀한 제약 조건**:
    - 최소/최대 학점 설정
    - 공강 요일 지정 (예: 금요일 수업 제외)
    - 점심 시간 확보 등
- **🚀 고성능 알고리즘**: 스마트 백트래킹 알고리즘을 통해 수천 가지 조합 중 최적의 시간표를 빠르게 찾아냅니다.
- **📊 결과 시각화**: 생성된 시간표를 대화형 테이블로 확인하고, HTML 파일로 내보내어 편리하게 볼 수 있습니다.

## 🛠 설치 방법

이 프로젝트는 **Python 3.10 이상**을 권장합니다.

1. **저장소 클론**
   ```bash
   git clone https://github.com/joon6644/schedule-maker.git
   cd schedule-maker
   ```

2. **가상 환경 생성 및 활성화 (권장)**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 사용 가이드

### 1. 프로그램 실행
```bash
python run.py
```

### 2. 강의 검색 및 추가 (Search Tab)
- **검색**: 상단 검색창에 강의명이나 교수명을 입력합니다.
- **추가**: 검색 결과에서 원하는 강의를 **우클릭**하여 '필수(Required)' 또는 '희망(Desired)' 목록에 추가합니다.

### 3. 조건 설정 (Config Tab)
- **학점 설정**: 이번 학기에 들을 최소/최대 학점을 슬라이더로 조절합니다.
- **공강 설정**: 학교에 가지 않을 요일을 선택합니다.
- **강의 관리**: 추가한 강의 목록을 확인하고, 드래그하여 우선순위를 변경하거나 삭제할 수 있습니다.

### 4. 결과 생성 (Result Tab)
- 자동으로 최적의 시간표 조합을 계산하여 보여줍니다.
- 결과 리스트를 클릭하면 오른쪽 미리보기에 시간표가 표시됩니다.
- 마음에 드는 시간표는 HTML로 저장하여 소장할 수 있습니다.

## 📂 프로젝트 구조

```
schedule_maker/
├── data/                       # 데이터 리소스 (강의 목록 CSV 등)
├── schedule_maker/             # 메인 소스 코드
│   ├── core/                   # 데이터 모델 및 핵심 로직
│   ├── services/               # 비즈니스 로직 (알고리즘, 파일 처리)
│   └── ui/                     # 사용자 인터페이스 (View, ViewModel)
├── tests/                      # 단위 테스트 (Pytest)
├── run.py                      # 실행 파일
└── requirements.txt            # 의존성 목록
```

## 🏗 기술 스택

- **Language**: Python 3.10+
- **GUI Framework**: PySide6 (Qt for Python), QFluentWidgets
- **Algorithm**: Exhaustive Backtracking (Bitmask + Pruning)
- **Testing**: Pytest
- **Data**: Pandas (CSV Parsing)

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.
