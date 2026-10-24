"""
Main Window
Fluent Window with Navigation
"""
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from qfluentwidgets import FluentWindow, FluentIcon as FIF, SplashScreen

from .interfaces.search_interface import SearchInterface
from .interfaces.config_interface import ConfigInterface
from .interfaces.result_interface import ResultInterface
from .services.interaction_service import MainWindowInteractionService
from .workers import ScheduleGenerationWorker, GenerationStateManager, GenerationState

class MainWindow(FluentWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.controller.set_main_window(self)
        
        # Interaction Service 생성 및 주입
        self._interaction_service = MainWindowInteractionService(self)
        self.controller.interaction_service = self._interaction_service
        
        # 🎯 State Manager 생성
        self.generation_state_manager = GenerationStateManager()
        self.generation_state_manager.state_changed.connect(self._on_generation_state_changed)
        self.generation_state_manager.progress_updated.connect(self._on_progress_message)
        
        # FIX: Force white background to solve visibility issues
        self.setObjectName("MainWindow")
        self.setStyleSheet("#MainWindow { background-color: white; }")

        self.initWindow()
        
        self.is_settings_dirty = True # Initial state

        # Create Interfaces
        self.searchInterface = SearchInterface(self, controller)
        self.configInterface = ConfigInterface(self, controller)
        self.resultInterface = ResultInterface(self, controller)
        
        self.initNavigation()
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.finish()
        
    def initWindow(self):
        self.setWindowTitle("Schedule Maker 2026")
        self.resize(1200, 950)
        self.setMinimumWidth(1100)
        self.setMinimumHeight(800)
        # Center window
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def initNavigation(self):
        self.addSubInterface(self.searchInterface, FIF.SEARCH, "강의 검색")
        self.addSubInterface(self.configInterface, FIF.SETTING, "설정")
        self.addSubInterface(self.resultInterface, FIF.CALENDAR, "결과 확인")

        # Set start interface
        self.navigationInterface.setCurrentItem(self.searchInterface.objectName())
        
        # FIX: Force overlay (Menu) mode naturally
        # 1. Disable MINIMAL mode to keep the strip visible when collapsed
        if hasattr(self.navigationInterface, 'panel'):
            self.navigationInterface.panel.isMinimalEnabled = False
            
        # 2. Set huge Minimum Expand Width to force MENU (Overlay) mode when expanding
        # This tricks the logic into thinking the window is always too narrow for split interactions.
        self.navigationInterface.setMinimumExpandWidth(9000)
        self.navigationInterface.setExpandWidth(300) 

        # Connect signal
        self.stackedWidget.currentChanged.connect(self._on_stack_changed)
        
        if hasattr(self.searchInterface.vm, 'bind'):
            # 1. Search VM updates -> Reload Config Data
            self.searchInterface.vm.bind('config_updated', lambda _: self.configInterface.vm.load_data())
            # 2. Search VM updates -> Mark Dirty
            self.searchInterface.vm.bind('config_updated', lambda _: self.set_dirty(True))
            
        if hasattr(self.configInterface.vm, 'bind'):
            # 3. Config VM updates -> Mark Dirty
            self.configInterface.vm.bind('config_changed', lambda _: self.set_dirty(True))


    # --- Interaction Service Implementation ---
    # MainWindow는 IInteractionService를 구현하여 하위 호환성 유지
    def show_error(self, title, msg):
        """에러 메시지 표시 (InteractionService에 위임)"""
        self._interaction_service.show_error(title, msg)
        
    def show_warning(self, title, msg):
        """경고 메시지 표시 (InteractionService에 위임)"""
        self._interaction_service.show_warning(title, msg)
        
    def show_info(self, title, msg):
        """정보 메시지 표시 (InteractionService에 위임)"""
        self._interaction_service.show_info(title, msg)

    def set_dirty(self, dirty=True):
        print(f"[DEBUG] MainWindow.set_dirty({dirty}) - Prev: {self.is_settings_dirty}")
        self.is_settings_dirty = dirty

    # --- Controller callbacks ---
    def refresh_tabs(self):
        # Refresh logic
        if hasattr(self.searchInterface.vm, 'perform_search'):
             self.searchInterface.vm.perform_search()
        if hasattr(self.configInterface.vm, 'load_data'):
             self.configInterface.vm.load_data()
            
    def switch_to_result(self):
        # switchTo will trigger _on_stack_changed signal which calls _check_and_generate
        # No need to call it explicitly here!
        self.switchTo(self.resultInterface)

    def _on_interface_changed(self, index):
        # Override or connect to stackedWidget signal if FluentWindow exposes it.
        # FluentWindow uses self.stackedWidget.currentChanged?
        # Actually FluentWindow handles navigation. 
        # We can override switchTo or check currentInterface.
        super().switchTo(self.stackedWidget.widget(index))
        
        current_widget = self.stackedWidget.widget(index)
        if current_widget == self.resultInterface:
            self._check_and_generate()
            
    def _on_stack_changed(self, index):
        current_widget = self.stackedWidget.widget(index)
        if current_widget == self.resultInterface:
            self._check_and_generate()

    def _check_and_generate(self):
        print(f"[DEBUG] _check_and_generate called. is_settings_dirty={self.is_settings_dirty}")
        if self.is_settings_dirty:
            # [Validation Check]
            if hasattr(self.configInterface, 'vm'):
                is_valid, msg = self.configInterface.vm.get_validation_status()
                if not is_valid:
                    print(f"[INFO] Generation skipped due to validation error: {msg}")
                    self.resultInterface.show_error(f"생성 불가: {msg}")
                    self.is_settings_dirty = False 
                    return

            # 🎯 상태 전이: IDLE → PREPARING (이벤트가 UI 업데이트 트리거)
            self.generation_state_manager.transition_to(
                GenerationState.PREPARING,
                "UI 준비 중..."
            )
            # 이후 처리는 _on_generation_state_changed에서
            
        else:
            self.resultInterface.load_schedule()

    def _on_generation_state_changed(self, old_state, new_state):
        """상태 전이 핸들러 - 각 상태별 UI 업데이트"""
        print(f"[MainWindow] State: {old_state.value} → {new_state.value}")
        
        if new_state == GenerationState.PREPARING:
            # 🎯 즉시 로딩 화면 표시
            self.resultInterface.show_loading()
            
            # 🎯 다음 이벤트 루프에서 워커 시작 (UI 렌더링 시간 확보)
            QTimer.singleShot(0, self._start_worker_generation)
            
        elif new_state == GenerationState.COMPLETED:
            # 완료 처리는 _on_generation_finished에서
            pass
            
        elif new_state == GenerationState.ERROR:
            # 에러 처리는 _on_generation_error에서
            pass
    
    def _on_progress_message(self, msg):
        """진행 메시지 업데이트"""
        if self.resultInterface:
            self.resultInterface.update_progress(msg)
    
    def _start_worker_generation(self):
        """워커 생성 및 시작 (분리된 메서드)"""
        self.worker = ScheduleGenerationWorker(
            self.controller,
            self.generation_state_manager
        )
        self.worker.finished.connect(self._on_generation_finished)
        self.worker.error.connect(self._on_generation_error)
        self.worker.progress.connect(self._on_generation_progress)
        self.worker.start()
        
        self.is_settings_dirty = False
        
    def _on_generation_progress(self, msg):
        """진행 상황 업데이트"""
        if self.resultInterface:
            self.resultInterface.update_progress(msg)
        
    def _on_generation_finished(self, count):
        # [State Management] Mark current config as "Generated Basis" on SUCCESS
        if hasattr(self.configInterface, 'vm') and hasattr(self.configInterface.vm, 'mark_as_generated'):
            self.configInterface.vm.mark_as_generated()

        # 완료 시 자동으로 결과 인터페이스의 로드 함수 호출
        if self.resultInterface:
            self.resultInterface.load_schedule()
        
        # 🎯 상태 초기화
        self.generation_state_manager.reset()
            
        # 결과 탭이 아닐 경우 (예: 다른 탭에서 생성만 시켰을 때) 알림 혹은 이동
        # 하지만 _check_and_generate는 보통 결과 탭 진입 시 호출되므로 이미 결과 탭임.
        pass
        
    def _on_generation_error(self, msg):
        self.show_error("오류", msg)
        # Reset loading state if needed
        self.resultInterface.show_error(msg)
        
        # 🎯 상태 초기화
        self.generation_state_manager.reset()
