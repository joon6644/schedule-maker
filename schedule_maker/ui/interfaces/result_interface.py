"""
Result Interface
Embeds the generated HTML schedule using QWebEngineView.
Uses native Qt widgets for instant loading screen display.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QFont
import os

from ..widgets.loading_spinner import LoadingSpinner
from ..widgets.stable_label import StableLabel


class ResultInterface(QWidget):
    """
    Result Viewer with native loading screen
    """
    def __init__(self, parent=None, controller=None):
        super().__init__(parent=parent)
        self.setObjectName("resultInterface")
        self.controller = controller
        
        # 메인 레이아웃
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        
        # 🎯 스택 위젯 (로딩 화면 ↔ 결과 화면 전환)
        self.stackedWidget = QStackedWidget(self)
        self.mainLayout.addWidget(self.stackedWidget)
        
        # 🎯 페이지 1: 네이티브 로딩 화면 (즉시 표시)
        self.loadingWidget = self._create_loading_widget()
        self.stackedWidget.addWidget(self.loadingWidget)  # Index 0
        
        # 🎯 페이지 2: WebView 결과 화면
        self.webView = QWebEngineView(self)
        self.stackedWidget.addWidget(self.webView)  # Index 1
        
        # 초기 상태: 빈 화면
        self.stackedWidget.setCurrentIndex(1)
        
        # Initial load if exists
        self.load_schedule()
    
    def _create_loading_widget(self):
        """네이티브 Qt 위젯으로 로딩 화면 생성"""
        widget = QWidget()
        mainLayout = QVBoxLayout(widget)
        mainLayout.setAlignment(Qt.AlignCenter)
        mainLayout.setSpacing(25)
        
        # 🎯 커스텀 회전 스피너
        self.spinner = LoadingSpinner()
        
        # 중앙 정렬 컨테이너
        spinnerContainer = QWidget()
        spinnerLayout = QVBoxLayout(spinnerContainer)
        spinnerLayout.setAlignment(Qt.AlignCenter)
        spinnerLayout.addWidget(self.spinner)
        
        # 제목
        titleLabel = QLabel("⏳ 시간표를 탐색하고 있습니다...")
        titleFont = QFont("Segoe UI", 16, QFont.Bold)
        titleLabel.setFont(titleFont)
        titleLabel.setStyleSheet("color: #0078D4;")
        titleLabel.setAlignment(Qt.AlignCenter)
        
        # 🎯 StableLabel: 텍스트 변경 시에도 위치 고정
        self.statusLabel = StableLabel("준비 중...", width=600, height=30, font_size=11)
        self.statusLabel.setStyleSheet("color: #666;")
        
        # 레이아웃 구성
        mainLayout.addWidget(spinnerContainer)
        mainLayout.addWidget(titleLabel)
        mainLayout.addWidget(self.statusLabel)
        
        # 배경색 설정
        widget.setStyleSheet("background-color: white;")
        
        return widget
    def load_schedule(self):
        """Loads the schedule_results.html file"""
        # 🎯 스피너 정지
        if hasattr(self, 'spinner'):
            self.spinner.stop()
        
        # Try to find the file
        path = "schedule_results.html"
        if self.controller:
            path = os.path.join(self.controller.data_path, 'data', 'schedule_results.html')
            if not os.path.exists(path):
                 # Fallback
                 path = os.path.join(self.controller.data_path, 'schedule_results.html')
        
        if os.path.exists(path):
            import time
            abs_path = os.path.abspath(path)
            # Force reload by adding dummy query param
            self.webView.setUrl(QUrl(f"file:///{abs_path.replace(os.sep, '/')}?t={int(time.time()*1000)}"))
            
            # 🎯 WebView로 전환
            self.stackedWidget.setCurrentIndex(1)
        else:
            self.show_placeholder()
            
    def show_placeholder(self):
        """빈 화면 표시"""
        # 🎯 스피너 정지
        if hasattr(self, 'spinner'):
            self.spinner.stop()
            
        self.webView.setHtml("")
        self.stackedWidget.setCurrentIndex(1)

    def show_loading(self):
        """🎯 네이티브 로딩 화면으로 즉시 전환 (0~10ms)"""
        print("[ResultInterface] show_loading() - 즉시 네이티브 위젯 표시")
        
        # 🎯 즉시 로딩 화면으로 전환
        self.stackedWidget.setCurrentIndex(0)
        
        # 상태 메시지 초기화
        self.statusLabel.setText("준비 중...")
        
        # 🎯 스피너 애니메이션 시작
        if hasattr(self, 'spinner'):
            self.spinner.start()

    def update_progress(self, msg: str):
        """🎯 네이티브 위젯에 진행 메시지 즉시 업데이트"""
        if self.stackedWidget.currentIndex() == 0:  # 로딩 화면 표시 중일 때만
            self.statusLabel.setText(msg)
        
    def show_error(self, msg):
        """에러 메시지 표시"""
        self.webView.setHtml(f"""
        <div style="text-align: center; margin-top: 50px; font-family: 'Segoe UI', sans-serif; color: #d13438;">
            <h3>⚠️ 오류가 발생했습니다</h3>
            <p>{msg}</p>
        </div>
        """)
        self.stackedWidget.setCurrentIndex(1)
