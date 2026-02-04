"""
MainWindow를 위한 InteractionService 구현체
의존성 역전 원칙(DIP)에 따라 IInteractionService 인터페이스 구현
"""
from PySide6.QtCore import Qt, QTimer
from qfluentwidgets import InfoBar, InfoBarPosition
import time

from ...core.interfaces import IInteractionService


class MainWindowInteractionService(IInteractionService):
    """
    MainWindow의 UI 메시지 표시 기능을 별도 서비스로 분리
    MainWindow의 다중 책임을 해소하기 위한 구현체
    """
    
    def __init__(self, main_window):
        """
        Args:
            main_window: FluentWindow 인스턴스 (stackedWidget 참조용)
        """
        self.main_window = main_window
        self._last_alert_time = 0
        self._cooldown = 0.8
        
    def _can_show_alert(self):
        current_time = time.time()
        if current_time - self._last_alert_time < self._cooldown:
            return False
        self._last_alert_time = current_time
        return True

    def show_error(self, title: str, message: str):
        """에러 메시지를 우측 상단에 표시 (Cooldown 적용)"""
        if not self._can_show_alert(): return

        QTimer.singleShot(100, lambda: InfoBar.error(
            title=title, 
            content=message, 
            orient=Qt.Horizontal, 
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT, 
            duration=2000, 
            parent=self.main_window.stackedWidget
        ))
        
    def show_warning(self, title: str, message: str):
        """경고 메시지를 우측 상단에 표시 (Cooldown 적용)"""
        if not self._can_show_alert(): return

        QTimer.singleShot(100, lambda: InfoBar.warning(
            title=title, 
            content=message, 
            orient=Qt.Horizontal, 
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT, 
            duration=2000, 
            parent=self.main_window.stackedWidget
        ))
        
    def show_info(self, title: str, message: str):
        """정보 메시지를 우측 상단에 표시 (Cooldown 적용)"""
        if not self._can_show_alert(): return

        QTimer.singleShot(100, lambda: InfoBar.success(
            title=title, 
            content=message, 
            orient=Qt.Horizontal, 
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT, 
            duration=2000, 
            parent=self.main_window.stackedWidget
        ))
