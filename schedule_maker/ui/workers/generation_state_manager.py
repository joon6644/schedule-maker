"""
시간표 생성 상태 관리자
State Pattern을 사용한 명시적 상태 관리
"""
from enum import Enum
from PySide6.QtCore import QObject, Signal


class GenerationState(Enum):
    """시간표 생성 상태"""
    IDLE = "idle"                # 대기 중
    PREPARING = "preparing"      # UI 준비 중
    LOADING = "loading"          # 데이터 로드 중
    PROCESSING = "processing"    # 시간표 생성 중
    COMPLETED = "completed"      # 완료
    ERROR = "error"              # 에러


class GenerationStateManager(QObject):
    """
    시간표 생성 상태를 관리하는 State Manager
    
    책임:
    - 상태 전이 검증 및 관리
    - 상태 변경 이벤트 발생
    - 잘못된 상태 전이 방지
    
    원칙:
    - Single Responsibility: 상태 관리만 담당
    - Open/Closed: 새로운 상태 추가 시 수정 최소화
    """
    
    # 시그널 정의
    state_changed = Signal(object, object)  # (old_state, new_state)
    progress_updated = Signal(str)          # 진행 메시지
    
    def __init__(self):
        super().__init__()
        self._state = GenerationState.IDLE
        
    @property
    def state(self) -> GenerationState:
        """현재 상태 반환"""
        return self._state
    
    @property
    def is_busy(self) -> bool:
        """생성 작업 진행 중 여부"""
        return self._state in {
            GenerationState.PREPARING,
            GenerationState.LOADING,
            GenerationState.PROCESSING
        }
        
    def transition_to(self, new_state: GenerationState, message: str = ""):
        """
        상태 전이 (유효성 검증 포함)
        
        Args:
            new_state: 전이할 상태
            message: 진행 메시지 (선택사항)
            
        Raises:
            ValueError: 잘못된 상태 전이 시
        """
        if not self._is_valid_transition(self._state, new_state):
            raise ValueError(
                f"Invalid state transition: {self._state.value} → {new_state.value}"
            )
        
        old_state = self._state
        self._state = new_state
        
        # 상태 변경 로깅
        print(f"[StateManager] {old_state.value} → {new_state.value}")
        if message:
            print(f"[StateManager] Message: {message}")
        
        # 이벤트 발생
        self.state_changed.emit(old_state, new_state)
        
        if message:
            self.progress_updated.emit(message)
    
    def _is_valid_transition(self, from_state: GenerationState, 
                            to_state: GenerationState) -> bool:
        """
        상태 전이 유효성 검증
        
        허용되는 상태 전이:
        IDLE → PREPARING
        PREPARING → LOADING, ERROR
        LOADING → PROCESSING, ERROR
        PROCESSING → COMPLETED, ERROR
        COMPLETED → IDLE
        ERROR → IDLE
        """
        valid_transitions = {
            GenerationState.IDLE: {
                GenerationState.PREPARING
            },
            GenerationState.PREPARING: {
                GenerationState.LOADING,
                GenerationState.ERROR
            },
            GenerationState.LOADING: {
                GenerationState.PROCESSING,
                GenerationState.ERROR
            },
            GenerationState.PROCESSING: {
                GenerationState.COMPLETED,
                GenerationState.ERROR
            },
            GenerationState.COMPLETED: {
               GenerationState.IDLE,
                GenerationState.ERROR  # 🎯 완료 후 에러 처리 가능하도록
            },
            GenerationState.ERROR: {
                GenerationState.IDLE
            }
        }
        
        return to_state in valid_transitions.get(from_state, set())
    
    def reset(self):
        """상태 초기화 (IDLE로 전환)"""
        if self._state != GenerationState.IDLE:
            self.transition_to(GenerationState.IDLE, "초기화됨")
