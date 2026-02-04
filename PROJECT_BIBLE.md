# Schedule Maker v2 - Project Bible

> **최종 업데이트**: 2026-02-03 (Pytest Adoption & Refactoring)
> **버전**: Refactored v2.2 (Testing & Stability Enhanced)
> **설명**: 프로젝트의 구조, 로직, 아키텍처를 상세히 기록한 문서입니다.

---

## 1. 프로젝트 개요 (Overview)

**Schedule Maker v2**는 명지대학교 학생들을 위한 시간표 생성 자동화 도구입니다. 사용자가 수강하고 싶은 강의 목록(필수/희망)과 제약 조건(공강 요일, 등교 제외 시간 등)을 설정하면, 가능한 모든 시간표 조합을 생성하여 시각화된 HTML 파일로 제공합니다.

### 주요 특징
- **MVVM 아키텍처**: UI와 비즈니스 로직의 명확한 분리
- **객체지향 원칙 준수**: SOLID 원칙(DIP, SRP) 적용
- **의존성 주입 (DI)**: 서비스 계층의 유연한 결합 및 테스트 용이성 확보
- **매니저 패턴**: ViewModel의 비대화를 방지하고 역할 분담
- **자동화된 테스트**: Pytest 기반의 강력한 단위 테스트 스위트 구축
- **PySide6 & Fluent UI**: 현대적이고 세련된 사용자 인터페이스

---

## 2. 디렉토리 구조 (Directory Structure)

```
schedule_maker_v2.2/
├── data/                       # 데이터 및 설정 파일 저장소 (런타임 생성)
│   ├── config.json             # 사용자 설정 (JSON)
│   ├── mju_2026_1.csv          # 강의 데이터 (CSV)
│   └── schedule_results.html   # 생성된 시간표 결과
│
├── schedule_maker/             # 메인 패키지
│   ├── __init__.py
│   │
│   ├── controllers/            # 컨트롤러 계층
│   │   └── app_controller.py   # 앱 전체 조정자 (의존성 주입 적용)
│   │
│   ├── core/                   # 핵심 도메인 및 공통 모듈
│   │   ├── config.py           # 설정 데이터 모델 (Pydantic/Dataclass)
│   │   ├── constants.py        # 전역 상수 관리 (Business & Algo Constants)
│   │   ├── interfaces.py       # 서비스 인터페이스 (DIP 핵심)
│   │   └── models.py           # 핵심 데이터 모델 (Course, Schedule)
│   │
│   ├── services/               # 비즈니스 로직 구현체
│   │   ├── config_service.py   # 설정 관리 (IConfigService 구현)
│   │   ├── course_service.py   # 강의 데이터 관리 및 검색
│   │   ├── parser.py           # CSV 파싱 로직
│   │   ├── schedule_service.py # 시간표 생성 조정 (Facade)
│   │   ├── scheduler.py        # 백트래킹 알고리즘 (코어 엔진)
│   │   └── visualizer.py       # HTML 시각화 생성
│   │
│   └── ui/                     # 사용자 인터페이스 (View & ViewModel)
│       ├── __init__.py
│       ├── main_window.py      # 메인 윈도우 (FluentWindow)
│       │
│       ├── interfaces/         # UI 화면 구성 (View)
│       │   ├── config_interface.py
│       │   ├── result_interface.py
│       │   └── search_interface.py
│       │
│       ├── services/           # UI 전용 서비스
│       │   └── interaction_service.py # 사용자 알림/상호작용 처리
│       │
│       ├── viewmodels/         # 뷰 모델 (Presentation Logic)
│       │   ├── base_viewmodel.py
│       │   ├── config_viewmodel.py
│       │   ├── result_viewmodel.py
│       │   ├── search_viewmodel.py
│       │   │
│       │   └── managers/       # ViewModel 책임 분산
│       │       ├── course_list_manager.py # 강의 리스트 CRUD
│       │       └── settings_manager.py    # 설정/제약조건 관리
│       │
│       ├── widgets/            # 재사용 가능한 커스텀 위젯
│       │   └── draggable_table.py # 드래그 앤 드롭 테이블 위젯
│       │
│       └── workers/            # 비동기 작업
│           └── schedule_worker.py # 시간표 생성 백그라운드 처리
│
├── tests/                      # [NEW] 테스트 스위트
│   ├── core/                   # 데이터 모델 단위 테스트
│   ├── services/               # 비즈니스 로직 단위 테스트
│   ├── ui/                     # ViewModel 로직 테스트
│   └── conftest.py             # Pytest 설정 및 Fixture
│
├── resources/                  # 아이콘, 이미지 등 리소스
├── run.py                      # 애플리케이션 진입점
├── run_tests.bat               # [NEW] 원클릭 테스트 실행 스크립트
└── requirements.txt            # 의존성 패키지 목록
```

---

## 3. 시스템 아키텍처 (Architecture)

이 프로젝트는 **MVVM (Model-View-ViewModel)** 패턴을 기반으로 하며, 리팩토링을 통해 **Service Layer Pattern**과 **Manager Pattern**이 강화되었습니다. 또한 **Pytest**를 도입하여 안정성을 더욱 견고히 했습니다.

### 3.1 계층별 역할

1.  **Model (Core)**
    *   데이터의 구조와 상태를 정의합니다.
    *   `Course`, `Schedule`, `ScheduleConfig` 등은 순수 데이터 클래스입니다.
    *   `interfaces.py`는 서비스들이 지켜야 할 계약(Contract)을 정의하여 유연성을 높입니다.

2.  **Service (Business Logic)**
    *   실질적인 비즈니스 로직을 수행합니다.
    *   `Scheduler`는 알고리즘 로직을 완전히 캡슐화하고 있으며, `test_scheduler.py`를 통해 검증됩니다.
    *   **ConfigService**: 설정의 Load/Save 및 유효성 검증을 담당하며, 파일 시스템 의존성을 격리하여 테스트 가능하게 설계되었습니다.

3.  **Controller**
    *   `AppController`는 애플리케이션의 시작과 초기화를 담당합니다 (IoC Container).
    *   모든 서비스 인스턴스를 생성하고 의존성을 주입(Injection)하여 결합도를 낮춥니다.

4.  **ViewModel**
    *   View와 Service 사이를 중재하고 UI 상태를 관리합니다.
    *   `ConfigViewModel`은 복잡한 설정 로직을 `CourseListManager`와 `SettingsManager`로 위임하여 SRP를 준수합니다.
    *   `PySide6` 라이브러리에 직접 의존하지 않도록 `BaseViewModel`을 설계하여 `QApplication` 없이도 테스트 가능합니다.

5.  **View (UI)**
    *   `PySide6`와 `qfluentwidgets`를 사용하여 현대적인 UI를 제공합니다.
    *   로직을 포함하지 않고 오직 ViewModel의 상태 변화에 반응(Observer Pattern)합니다.

---

## 4. 데이터 모델 (Data Models)

### `Course` (dataclass)
강의 하나를 나타내는 불변(Immutable) 성격의 객체입니다.
*   **속성**: `course_id`, `name`, `credits`, `professor`, `time_slots`
*   **특징**: `time_mask` 속성을 통해 비트마스크 기반의 초고속 충돌 검사를 지원합니다.

### `TimeSlot` (dataclass)
강의의 구체적인 요일과 시간을 표현합니다.
*   **속성**: `day` (요일 인덱스), `start_time`, `end_time`
*   **기능**: 시간을 30분 단위의 인덱스로 변환하거나 비트마스크로 변환합니다.

### `Schedule`
생성된 시간표 결과 하나를 나타냅니다.
*   **속성**: `courses` (강의 리스트), `total_credits` (총 학점), `has_random_filled` (랜덤 채우기 여부)
*   **검증**: 중복된 강의가 없고, 시간이 겹치지 않음을 보장합니다.

---

## 5. 핵심 알고리즘 (Algorithm)

### 5.1 시간표 생성 알고리즘 (Randomized Backtracking with Restarts)
`schedule_maker/services/scheduler.py`에 구현된 이 시스템은 단순한 DFS가 아닌, **무작위 재시작(Randomized Restart)** 전략을 결합한 지능형 백트래킹 알고리즘입니다.

1.  **Phase 1: 필수 강의 조합 (Constraint Satisfaction)**
    *   사용자가 지정한 필수 강의들의 가능한 모든 조합을 먼저 생성합니다.
    *   충돌이 발생하는 조합은 이 단계에서 조기에 배제됩니다.

2.  **Phase 2: 휴리스틱 정렬 (Heuristics)**
    *   희망 강의 목록을 **Bin Packing** (큰 학점 우선) 및 **MRV** (시간 제약 많은 강의 우선) 순으로 정렬하여 탐색 효율을 극대화합니다.

3.  **Phase 3: 무작위 탐색 (Restart Engine)**
    *   제한된 시간과 깊이 내에서 DFS를 반복 수행하며, 매 반복마다 희망 강의 탐색 순서를 셔플하여 다양한 해를 찾습니다.
    *   **조기 종료**: 발견 속도가 현저히 떨어지면(Saturation), 목표 개수를 채우지 못했더라도 탐색을 멈춥니다.

4.  **Phase 4: 무작위 채우기 (Random Fill)**
    *   순수 조합만으로 최소 학점을 채우지 못할 경우, '전학년' 대상 강의(교양 등)로 빈 시간을 자동으로 채워 넣는 기능입니다.

---

## 6. 테스트 전략 (Testing Strategy) [NEW]

프로젝트의 안정성을 보장하기 위해 **Pytest**를 도입하였습니다. 모든 핵심 로직은 단위 테스트로 보호됩니다.

### 6.1 테스트 구조
*   `tests/core/`: 데이터 모델의 무결성 및 비트마스크 연산 정확성 검증.
*   `tests/services/`: 스케줄링 알고리즘, 설정 관리 로직 검증.
*   `tests/ui/`: ViewModel의 상태 로직 및 상호작용 검증 (UI 위젯 없이 순수 로직 테스트).

### 6.2 테스트 실행
프로젝트 루트에서 다음 명령어로 전체 테스트를 실행할 수 있습니다.
```bash
pytest
# 또는
run_tests.bat
```

---

## 7. 개발 가이드

### 새로운 서비스 추가하기
1. `core/interfaces.py`에 인터페이스 정의 (`IMyNewService`)
2. `services/` 패키지에 구현체 작성 (`MyNewService`)
3. `AppController` 생성자에 주입 코드 추가

### UI 수정하기
1. `ui/interfaces/`에 있는 View 파일 수정
2. 로직이 필요하면 `ui/viewmodels/`의 ViewModel 수정
3. 복잡한 로직은 `ui/viewmodels/managers/`에 매니저 클래스로 분리

### 테스트 작성 가이드
1. 새로운 로직 작성 시 반드시 `tests/` 폴더에 해당 모듈에 대한 테스트 코드를 작성합니다.
2. `conftest.py`에 정의된 Mock Fixture들을 적극 활용하여 격리된 테스트를 수행합니다.
3. `config_service` 같은 IO 의존성은 반드시 Mocking 처리합니다.

---

## 8. 사용자 경험 (User Experience)

### 시각적 피드백
*   **Toast 알림**: 저장, 로드, 에러 등 주요 이벤트 발생 시 우측 상단에 직관적인 팝업 알림을 제공합니다.
*   **반응형 UI**: 버튼, 리스트 등 상호작용 요소에 미세한 애니메이션을 적용하여 사용성을 높였습니다.

### 고급 제어
*   **드래그 앤 드롭**: 강의 우선순위 변경 및 그룹 간 이동을 직관적으로 수행할 수 있습니다.
*   **3단계 정렬**: 검색 결과 헤더 클릭 시 오름차순/내림차순/초기화 순으로 정렬됩니다.
*   **핀(Pin) 기능**: 결과 화면에서 특정 강의를 고정하여 해당 강의가 포함된 시간표만 필터링해서 볼 수 있습니다.

---

## 9. 사용자 가이드 (User Manual)

### 1단계: 강의 검색 및 담기
1.  **검색 탭 (Search)**에서 강의명/교수명으로 강의를 검색합니다.
2.  원하는 강의를 찾아 **필수(Required)** 또는 **희망(Desired)** 목록에 추가합니다.

### 2단계: 조건 설정
1.  **설정 탭 (Config)**에서 최소/최대 학점과 공강 요일을 설정합니다.
2.  드래그 앤 드롭으로 강의 우선순위를 조정하거나 필요 없는 강의를 삭제합니다.

### 3단계: 시간표 생성
1.  **결과 탭 (Result)**으로 이동하면 자동으로 최적의 시간표 조합을 생성합니다.
2.  생성된 시간표를 탐색하고, HTML 파일로 결과를 저장하여 활용합니다.
