"""
애플리케이션 전역 상수 정의
매직 넘버와 문자열을 한 곳에서 관리하여 유지보수성 향상
"""
from enum import Enum


# ============================================================
# UI 관련 상수
# ============================================================

class UIConstants:
    """UI 크기 및 레이아웃 상수"""
    
    # 메인 윈도우
    WINDOW_DEFAULT_WIDTH = 1200
    WINDOW_DEFAULT_HEIGHT = 950
    WINDOW_MIN_WIDTH = 1100
    WINDOW_MIN_HEIGHT = 800
    
    # 위젯 크기
    CREDIT_SPIN_WIDTH = 60
    TIME_TABLE_DAY_COLUMN_WIDTH = 50
    
    # 메시지 표시 시간 (ms)
    INFO_BAR_DURATION = 2000
    TIMER_DELAY = 100


# ============================================================
# 비즈니스 로직 상수
# ============================================================

class BusinessConstants:
    """비즈니스 로직 관련 상수"""
    
    # 학점 기본값
    DEFAULT_MIN_CREDITS = 12
    DEFAULT_MAX_CREDITS = 18
    
    # 시간표 생성
    MAX_SCHEDULE_RESULTS = 100000
    
    # 시간 관련
    DAYS_OF_WEEK = ['월', '화', '수', '목', '금']
    TIME_SLOT_UNIT = 30  # 분 단위
    
    # Random Fill 제외 과목 (하드코딩)
    # 졸업 요건 등으로 인해 사용자가 직접 선택해야 하는 과목들
    EXCLUDED_RANDOM_FILL_SUBJECTS = {
        '영어1', '영어2', '영어3', '영어4',
        '영어회화1', '영어회화2', '영어회화3', '영어회화4',
        '기초영어'
    }


class SchedulerConfig:
    """시간표 생성 알고리즘 설정값 (중앙화)"""
    
    # === 목표 및 배치 설정 ===
    TARGET_RESULTS = 10000          # 목표 시간표 개수
    BATCH_SIZE = 20                  # 한 번의 DFS에서 찾을 개수
    
    # === 병렬 처리 설정 ===
    USE_PARALLEL = True              # 병렬 처리 사용 여부
    PARALLEL_WORKERS = None          # Worker 수 (None = CPU 코어 수)
    
    # === 타임아웃 설정 (참고용, 실제로는 포화 감지로 자동 종료) ===
    MAX_TOTAL_TIME_SECONDS = 7.0     # 예상 실행 시간 (강제 종료 안 함)
    MAX_RESTARTS = 1000              # 최대 Restart 횟수 (무한 루프 방지)
    SINGLE_DFS_TIMEOUT = 0.5         # 단일 DFS 최대 시간 (미사용)
    
    # === 조기 종료 설정 ===
    SATURATION_CHECK_WINDOW = 100    # 발견율 체크 윈도우 (최근 N회)
    SATURATION_THRESHOLD = 3         # 최근 N회 중 이 개수 미만 발견 시 종료
    
    # === Phase 전환 설정 ===
    MAX_PURE_FAILURES = 50           # Pure 모드에서 연속 실패 허용 횟수
    
    # === 진행 상황 출력 주기 ===
    PROGRESS_REPORT_INTERVAL = 10    # N회 Restart마다 진행 상황 출력



# ============================================================
# 파일 경로 상수
# ============================================================

class PathConstants:
    """파일 및 디렉토리 경로 상수"""
    
    # 데이터 디렉토리
    DATA_DIR = 'data'
    
    # 설정 파일
    CONFIG_FILENAME = 'config.json'
    CONFIG_PATH = f'{DATA_DIR}/{CONFIG_FILENAME}'
    
    # CSV 데이터 파일
    CSV_FILENAME = 'mju_2026_1.csv'
    
    # 결과 파일
    RESULT_FILENAME = 'schedule_results.html'
    RESULT_PATH = f'{DATA_DIR}/{RESULT_FILENAME}'


# ============================================================
# 문자열 상수 (Enum)
# ============================================================

class CourseListType(Enum):
    """강의 리스트 타입"""
    REQUIRED = 'required'
    DESIRED = 'desired'


class Weekday(Enum):
    """요일"""
    MON = '월'
    TUE = '화'
    WED = '수'
    THU = '목'
    FRI = '금'
    
    @classmethod
    def all_values(cls):
        """모든 요일 문자열 리스트 반환"""
        return [day.value for day in cls]


class SortState(Enum):
    """정렬 상태"""
    DEFAULT = 0     # 기본 (정렬 안 됨)
    ASCENDING = 1   # 오름차순
    DESCENDING = 2  # 내림차순


# ============================================================
# 메시지 상수
# ============================================================

class Messages:
    """사용자 메시지 템플릿"""
    
    # 성공 메시지
    SUCCESS_COURSE_ADDED = "강의가 추가되었습니다: {name}"
    SUCCESS_CONFIG_SAVED = "설정이 저장되었습니다.\n{path}"
    SUCCESS_CONFIG_LOADED = "설정을 불러왔습니다.\n{path}"
    
    # 오류 메시지
    ERROR_COURSE_ADD_FAILED = "강의 추가에 실패했습니다."
    ERROR_CONFIG_SAVE_FAILED = "저장 실패: {error}"
    ERROR_CONFIG_LOAD_FAILED = "설정 로드 실패: {error}"
    ERROR_MOVE_FAILED = "강의 이동에 실패했습니다."
    ERROR_REORDER_FAILED = "순서 변경에 실패했습니다."
    ERROR_TIME_ADD_FAILED = "시간대 추가 실패"
    ERROR_TIME_REMOVE_FAILED = "시간대 삭제 실패"
    ERROR_CREDITS_INVALID = "최소 학점이 최대 학점보다 클 수 없습니다."
    ERROR_NO_SCHEDULES = "조건에 맞는 시간표가 없습니다."
    
    # 정보 메시지
    INFO_NO_ALT_SECTION = "다른 분반을 찾을 수 없습니다."
    INFO_DEFAULT_CONFIG = "설정 파일이 없어 기본 설정을 사용합니다."
    INFO_CONFIG_MIGRATED = "설정 파일을 새 위치로 이동했습니다: {path}"
    
    # 경고 메시지
    WARNING_CONFIG_LOAD_FAILED = "설정 파일 로드 실패. 기본 설정을 사용합니다.\n{error}"
    WARNING_CSV_LOAD_FAILED = "CSV 파일 로드 실패:\n{error}"
    WARNING_CSV_NOT_FOUND = "CSV 파일을 찾을 수 없습니다:\n{path}"


# ============================================================
# 헬퍼 함수
# ============================================================

def get_weekday_list():
    """요일 리스트 반환 (하위 호환성)"""
    return Weekday.all_values()
