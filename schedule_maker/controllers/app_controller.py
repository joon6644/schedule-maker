"""
Application controller.
Manages service wiring and app-level lifecycle.
"""
import glob
import os
import re
import threading

try:
    from ..services.course_service import CourseService
    from ..services.config_service import ConfigService
    from ..services.schedule_service import ScheduleService
except ImportError:
    from services.course_service import CourseService
    from services.config_service import ConfigService
    from services.schedule_service import ScheduleService


class AppController:
    def __init__(
        self,
        course_service=None,
        config_service=None,
        schedule_service=None,
        interaction_service=None,
        resource_path='.',
        data_path='.'
    ):
        self.resource_path = resource_path
        self.data_path = data_path
        self.course_service = course_service or CourseService()
        self.config_service = config_service or ConfigService()
        self.schedule_service = schedule_service or ScheduleService()
        self.interaction_service = interaction_service
        self.main_window = None
        self.is_initialized = False
        self.current_term_key = None
        self.current_config_path = None

    def initialize(self):
        if self.is_initialized:
            return True

        csv_path = self._resolve_csv_path()
        if not os.path.exists(csv_path):
            self._show_error('오류', f'CSV 파일을 찾을 수 없습니다:\n{csv_path}')
            return False

        self.current_term_key = self._extract_term_key(csv_path)
        self.current_config_path = self._resolve_config_path(self.current_term_key)

        try:
            self.course_service.load_courses(csv_path)
            print(f"[INFO] {self.course_service.get_course_count()}개 강의 로드 완료")
        except Exception as e:
            self._show_error('오류', f'CSV 파일 로드 실패:\n{e}')
            return False

        try:
            if os.path.exists(self.current_config_path):
                self.config_service.load_config(self.current_config_path)
            else:
                legacy_path = os.path.join(self.data_path, 'config.json')
                if os.path.exists(legacy_path):
                    self.config_service.load_config(legacy_path)
                    self.config_service.save_config(path=self.current_config_path)
                else:
                    self.config_service.create_default_config()
                    self.config_service.save_config(path=self.current_config_path)
        except Exception as e:
            self._show_warning('경고', f'설정 파일 로드 실패. 기본 설정을 사용합니다.\n{e}')
            self.config_service.create_default_config()
            self.config_service.save_config(path=self.current_config_path)

        self.is_initialized = True
        return True

    def _resolve_csv_path(self):
        preferred = os.path.join(self.resource_path, 'mju_2026_2.csv')
        if os.path.exists(preferred):
            return preferred

        candidates = []
        candidates.extend(glob.glob(os.path.join(self.resource_path, 'mju_*.csv')))
        candidates.extend(glob.glob(os.path.join(self.resource_path, 'data', 'mju_*.csv')))

        if candidates:
            candidates.sort(key=lambda path: os.path.getmtime(path), reverse=True)
            return candidates[0]

        return preferred

    def _extract_term_key(self, csv_path: str):
        filename = os.path.basename(csv_path)
        match = re.match(r"mju_(\d{4})_(\d)\.csv$", filename)
        if match:
            return f"{match.group(1)}_{match.group(2)}"
        return None

    def _resolve_config_path(self, term_key: str = None):
        config_dir = os.path.join(self.data_path, 'data', 'configs')
        os.makedirs(config_dir, exist_ok=True)
        if term_key:
            return os.path.join(config_dir, f"{term_key}.json")
        return os.path.join(config_dir, 'default.json')

    def set_main_window(self, window):
        self.main_window = window
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
        def run():
            try:
                if progress_callback:
                    progress_callback("시간표 생성 시작...")
                if progress_callback:
                    self.schedule_service.set_progress_callback(progress_callback)

                all_courses = self.course_service.get_all_courses()
                config = self.config_service.get_config()
                schedules = self.schedule_service.generate_schedules(all_courses, config)

                if not schedules:
                    if progress_callback:
                        progress_callback("오류: 조건에 맞는 시간표를 찾을 수 없습니다.")
                    self._show_error(
                        '오류',
                        '조건에 맞는 시간표를 찾을 수 없습니다.\n\n'
                        '[확인]\n'
                        '- 학점 범위를 줄여보세요\n'
                        '- 필수 강의를 줄여보세요\n'
                        '- 시간표 충돌을 확인해보세요'
                    )
                    return

                output_path = os.path.join(self.data_path, 'schedule_results.html')
                self.schedule_service.export_to_html(
                    output_path=output_path,
                    open_browser=True,
                    year=self._term_year(),
                    semester=self._term_semester(),
                )

                if progress_callback:
                    progress_callback(f"완료! {len(schedules)}개 조합 생성")

                msg = f'시간표 생성 완료!\n\n총 {len(schedules)}개 조합이 생성되었습니다.'
                if len(schedules) > 10000:
                    msg += '\n\n(결과 파일에는 임의로 10,000개만 저장됩니다)'
                self._show_info('성공', msg)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"오류: {e}")
                self._show_error('오류', f'시간표 생성 중 오류 발생:\n{e}')
                import traceback
                traceback.print_exc()

        threading.Thread(target=run, daemon=True).start()

    def _term_year(self):
        if self.current_term_key and '_' in self.current_term_key:
            return self.current_term_key.split('_')[0]
        return None

    def _term_semester(self):
        if self.current_term_key and '_' in self.current_term_key:
            return self.current_term_key.split('_')[1]
        return None

    def save_config(self):
        try:
            config_path = self.current_config_path or self._resolve_config_path()
            self.config_service.save_config(path=config_path)
            return True
        except Exception as e:
            self._show_error('오류', f'설정 저장 실패:\n{e}')
            return False

    def load_config(self):
        try:
            config_path = self.current_config_path or self._resolve_config_path()
            self.config_service.load_config(config_path)
            return True
        except Exception as e:
            self._show_error('오류', f'설정 로드 실패:\n{e}')
            return False

    def refresh_tabs(self):
        if self.main_window and hasattr(self.main_window, 'refresh_tabs'):
            self.main_window.refresh_tabs()
