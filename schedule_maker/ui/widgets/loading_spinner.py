"""
Custom loading spinner widget with rotation animation
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor


class LoadingSpinner(QWidget):
    """심플한 점 3개 펄스 애니메이션"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.setFixedSize(60, 20)
        
        # 타이머로 애니메이션
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        
    def start(self):
        """애니메이션 시작"""
        self.timer.start(150)  # 150ms마다 업데이트
        
    def stop(self):
        """애니메이션 정지"""
        self.timer.stop()
        self.angle = 0
        self.update()
        
    def animate(self):
        """애니메이션 각도 업데이트"""
        self.angle = (self.angle + 1) % 3
        self.update()  # 다시 그리기
        
    def paintEvent(self, event):
        """점 3개 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 점 색상
        color = QColor(0, 120, 212)  # #0078D4
        
        # 중심 위치
        center_y = self.height() / 2
        spacing = 20
        start_x = (self.width() - spacing * 2) / 2
        
        # 3개의 점 그리기
        for i in range(3):
            x = start_x + i * spacing
            
            # 현재 활성화된 점만 크고 진하게
            if i == self.angle:
                radius = 5
                color.setAlphaF(1.0)
            else:
                radius = 3
                color.setAlphaF(0.3)
            
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x - radius), int(center_y - radius), 
                              radius * 2, radius * 2)
