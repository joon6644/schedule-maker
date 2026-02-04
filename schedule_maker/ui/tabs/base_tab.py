"""
기본 탭 클래스
모든 탭이 상속할 베이스 클래스
"""
import tkinter as tk
from tkinter import ttk
from ..base.theme import theme
from ..base.styled_component import ModernFrame


class BaseTab(ModernFrame):
    """
    기본 탭 클래스
    
    Args:
        parent: 부모 위젯 (보통 ttk.Notebook)
        controller: 애플리케이션 컨트롤러
    """
    
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg=theme.BACKGROUND, padding=theme.SPACE_L)
        self.controller = controller
        
        # 서비스 참조 (컨트롤러를 통해 접근)
        self.course_service = None
        self.config_service = None
        self.schedule_service = None
        
        if controller:
            self.course_service = getattr(controller, 'course_service', None)
            self.config_service = getattr(controller, 'config_service', None)
            self.schedule_service = getattr(controller, 'schedule_service', None)
    
    def setup_ui(self):
        """UI 설정 - 서브클래스에서 구현"""
        raise NotImplementedError("서브클래스에서 setup_ui()를 구현해야 합니다.")
    
    def refresh(self):
        """탭 새로고침 - 필요시 서브클래스에서 오버라이드"""
        pass
