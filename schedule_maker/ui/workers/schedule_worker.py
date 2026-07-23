"""
시간표 생성 워커 클래스
MainWindow에서 분리하여 별도 파일로 관리
단일 책임 원칙(SRP) 준수를 위한 분리
"""
import os
from PySide6.QtCore import QThread, Signal
from .generation_state_manager import GenerationState


class ScheduleGenerationWorker(QThread):
    """
    백그라운드에서 시간표 생성을 수행하는 워커 스레드
    UI 블로킹을 방지하기 위해 별도 스레드에서 실행
    """
    
    finished = Signal(int)  # 생성된 시간표 개수
    error = Signal(str)     # 에러 메시지
    progress = Signal(str)  # 진행 상황 메시지
    
    def __init__(self, controller, state_manager=None):
        """
        Args:
            controller: AppController 인스턴스
            state_manager: GenerationStateManager 인스턴스 (선택사항)
        """
        super().__init__()
        self.controller = controller
        self.state_manager = state_manager
        
    def run(self):
        """스레드 메인 실행 로직"""
        try:
            # 🎯 상태 전이: PREPARING → LOADING
            if self.state_manager:
                self.state_manager.transition_to(
                    GenerationState.LOADING,
                    "⏳ 데이터 준비 중..."
                )
            
            all_courses = self.controller.course_service.get_all_courses()
            config = self.controller.config_service.get_config()
            
            # [DEBUG] Verify Config
            print(f"[DEBUG] Worker Config: Min={config.min_credits}, Max={config.max_credits}")
            print(f"[DEBUG] Worker Config: Required={len(config.required_filters)}, Desired={len(config.desired_filters)}")
            print(f"[DEBUG] Worker Config: ExcludedDays={config.excluded_days}, ExcludedTimes={len(config.excluded_time_slots)}")
            
            # 🎯 상태 전이: LOADING → PROCESSING
            if self.state_manager:
                self.state_manager.transition_to(
                    GenerationState.PROCESSING,
                    "🚀 시간표 조합 찾는 중..."
                )
            
            # 진행 핸들러 정의
            def on_progress(msg):
                self.progress.emit(msg)
            
            # 콜백 설정
            self.controller.schedule_service.set_progress_callback(on_progress)
            
            # 2. 시간표 생성
            schedules = self.controller.schedule_service.generate_schedules(all_courses, config)
            
            if not schedules:
                if self.state_manager:
                    self.state_manager.transition_to(GenerationState.ERROR)
                self.error.emit("조건에 맞는 결과가 없습니다.")
                return

            # 3. HTML로 내보내기 (브라우저 자동 열기 안 함)
            output_path = os.path.join(self.controller.data_path, 'data', 'schedule_results.html')
            year = None
            semester = None
            term_key = getattr(self.controller, 'current_term_key', None)
            if term_key and '_' in term_key:
                year, semester = term_key.split('_', 1)

            self.controller.schedule_service.export_to_html(
                output_path,
                open_browser=False,
                year=year,
                semester=semester
            )
            
            # 🎯 상태 전이: PROCESSING → COMPLETED
            if self.state_manager:
                self.state_manager.transition_to(
                    GenerationState.COMPLETED,
                    f"✅ {len(schedules)}개의 시간표 생성 완료"
                )
            
            # 4. 완료 시그널 발생
            self.finished.emit(len(schedules))

        except Exception as e:
            # 🎯 상태 전이: ERROR
            if self.state_manager:
                self.state_manager.transition_to(
                    GenerationState.ERROR,
                    f"오류 발생: {str(e)}"
                )
            
            # GenerationError라면 구체적 메시지 전달
            if e.__class__.__name__ == 'GenerationError':
                self.error.emit(str(e))
            else:
                self.error.emit(f"오류가 발생했습니다: {e}")
            import traceback
            traceback.print_exc()
