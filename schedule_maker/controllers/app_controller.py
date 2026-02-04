"""
애플리케이션 컨트롤러
서비스와 뷰를 연결하고 전체 애플리케이션 흐름 관리
"""
import os
import threading
# from tkinter import messagebox (Removed for PySide6)


try:
    from ..services.course_service import CourseService
    from ..services.config_service import ConfigService
    from ..services.schedule_service import ScheduleService
except ImportError:
    from services.course_service import CourseService
    from services.config_service import ConfigService
    from services.schedule_service import ScheduleService


class AppController:
    """메인 애플리케이션 컨트롤러"""
    
    def __init__(
        self, 
        course_service=None,
        config_service=None,
        schedule_service=None,
        interaction_service=None,
        resource_path='.', 
        data_path='.'
    ):
        """
        Args:
            course_service: ICourseService 구현체 (None이면 자동 생성)
            config_service: IConfigService 구현체 (None이면 자동 생성)
            schedule_service: IScheduleService 구현체 (None이면 자동 생성)
            interaction_service: IInteractionService 구현체 (UI에서 주입)
            resource_path: 리소스 파일 경로
            data_path: 데이터 저장 경로
        """
        self.resource_path = resource_path
        self.data_path = data_path
        
        # 서비스 초기화 (의존성 주입 또는 기본 생성)
        # 하위 호환성: None이면 기존 방식대로 자동 생성
        if course_service is None:
            self.course_service = CourseService()
        else:
            self.course_service = course_service
            
        if config_service is None:
            self.config_service = ConfigService()
        else:
            self.config_service = config_service
            
        if schedule_service is None:
            self.schedule_service = ScheduleService()
        else:
            self.schedule_service = schedule_service
        
        self.interaction_service = interaction_service  # UI 초기화 시 설정됨
        
        # UI 참조 (나중에 설정됨)
        self.main_window = None
        
        # 상태
        self.is_initialized = False
    
    def initialize(self):
        """애플리케이션 초기화"""
        if self.is_initialized:
            return
        
        # CSV 파일 로드 (리소스 경로에서)
        csv_path = os.path.join(self.resource_path, 'mju_2026_1.csv')
        if os.path.exists(csv_path):
            try:
                self.course_service.load_courses(csv_path)
                print(f"✅ {self.course_service.get_course_count()}개 강의 로드 완료")
            except Exception as e:
                self._show_error('오류', f'CSV 파일 로드 실패:\n{e}')
                return False
        else:
            self._show_error('오류', f'CSV 파일을 찾을 수 없습니다:\n{csv_path}')
            return False
        
        # 설정 파일 로드 (데이터 경로에서)
        config_path = os.path.join(self.data_path, 'data', 'config.json')
        try:
            if os.path.exists(config_path):
                self.config_service.load_config(config_path)
            # 이전 버전 호환성: 루트 config.json이 있으면 이동 또는 로드
            elif os.path.exists(os.path.join(self.data_path, 'config.json')):
                 old_path = os.path.join(self.data_path, 'config.json')
                 try:
                     self.config_service.load_config(old_path)
                     # 새 위치로 저장
                     self.config_service.save_config(path=config_path)
                     print(f"📦 설정 파일을 새 위치로 이동했습니다: {config_path}")
                 except Exception:
                     pass
            else:
                # 기본 설정 생성
                self.config_service.create_default_config()
                # 중요: 생성 후 경로 설정을 위해 저장 한 번 수행
                self.config_service.save_config(path=config_path)
                print("⚠️ 설정 파일이 없어 기본 설정을 사용합니다.")
        except Exception as e:
            self._show_warning('경고', f'설정 파일 로드 실패. 기본 설정을 사용합니다.\n{e}')
            self.config_service.create_default_config()
            # 오류 시에도 경로 설정
            self.config_service.save_config(path=config_path)
        
        self.is_initialized = True
        return True
    
    def set_main_window(self, window):
        """메인 윈도우 참조 설정"""
        self.main_window = window
        # InteractionService 주입
        if hasattr(window, 'interaction_service'):
            self.interaction_service = window.interaction_service
            
    def _show_error(self, title, msg):
        if self.interaction_service:
            self.interaction_service.show_error(title, msg)
        else:
            print(f"[ERROR] {title}: {msg}")
            
    def _show_warning(self, title, msg):
        if self.interaction_service:
            self.interaction_service.show_warning(title, msg)
        else:
            print(f"[WARNING] {title}: {msg}")
            
    def _show_info(self, title, msg):
        if self.interaction_service:
            self.interaction_service.show_info(title, msg)
        else:
            print(f"[INFO] {title}: {msg}")
    
    def generate_schedules(self, progress_callback=None):
        """
        시간표 생성 (백그라운드 스레드에서 실행)
        
        Args:
            progress_callback: 진행 상태 콜백 함수
        """
        def run():
            try:
                if progress_callback:
                    progress_callback("시간표 생성 시작...")
                
                # 진행률 콜백 설정
                if progress_callback:
                    self.schedule_service.set_progress_callback(progress_callback)
                
                # 생성
                all_courses = self.course_service.get_all_courses()
                config = self.config_service.get_config()
                
                schedules = self.schedule_service.generate_schedules(all_courses, config)
                
                if not schedules:
                    if progress_callback:
                        progress_callback("오류: 조건에 맞는 시간표를 찾을 수 없습니다.")
                    self._show_error(
                        '오류',
                        '조건에 맞는 시간표 조합을 찾을 수 없습니다.\n\n'
                        '[팁]\n'
                        '- 학점 범위를 넓혀보세요.\n'
                        '- 필수 강의를 줄여보세요.\n'
                        '- 시간 충돌을 확인하세요.'
                    )
                    return
                
                # HTML 내보내기 (데이터 경로에 저장)
                output_path = os.path.join(self.data_path, 'schedule_results.html')
                self.schedule_service.export_to_html(
                    output_path=output_path,
                    open_browser=True
                )
                
                if progress_callback:
                    progress_callback(f"완료! {len(schedules)}개 조합 생성")
                
                # 최대 결과 제한 확인 (Scheduler.py의 MAX_RESULTS와 일치시켜야 함)
                MAX_LIMIT = 100000
                
                if len(schedules) >= MAX_LIMIT:
                    msg = f'시간표 생성 완료!\n\n총 {MAX_LIMIT}개 이상의 조합이 발견되었습니다.\n(시스템 성능을 위해 {MAX_LIMIT}개에서 중단됨)'
                else:
                    msg = f'시간표 생성 완료!\n\n총 {len(schedules)}개 조합이 생성되었습니다.'
                
                if len(schedules) > 10000:
                    msg += '\n\n(결과 파일에는 무작위 10,000개만 저장됩니다)'
                
                self._show_info('성공', msg)
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"오류: {e}")
                self._show_error('오류', f'시간표 생성 중 오류 발생:\n{e}')
                import traceback
                traceback.print_exc()
        
        # 백그라운드 스레드에서 실행
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def save_config(self):
        """현재 설정 저장"""
        try:
            config_path = os.path.join(self.data_path, 'data', 'config.json')
            self.config_service.save_config(path=config_path)
            return True
        except Exception as e:
            self._show_error('오류', f'설정 저장 실패:\n{e}')
            return False
    
    def load_config(self):
        """설정 다시 로드"""
        try:
            config_path = os.path.join(self.data_path, 'data', 'config.json')
            self.config_service.load_config(config_path)
            return True
        except Exception as e:
            self._show_error('오류', f'설정 로드 실패:\n{e}')
            return False
    def refresh_tabs(self):
        """탭 갱신 요청"""
        if self.main_window and hasattr(self.main_window, 'refresh_tabs'):
            self.main_window.refresh_tabs()
