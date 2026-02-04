"""
Stable text label widget that maintains position when text changes
"""
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont


class StableLabel(QLabel):
    """
    텍스트 변경 시에도 위치가 고정되는 라벨
    
    특징:
    - Monospace 폰트로 문자 너비 일정하게 유지
    - 고정 크기로 레이아웃 재계산 방지  
    - 중앙 정렬 시에도 위치 고정
    - sizeHint 고정으로 레이아웃 점프 방지
    """
    
    def __init__(self, text="", width=500, height=30, font_size=11, parent=None):
        super().__init__(text, parent)
        
        # 고정 크기 저장
        self._fixed_width = width
        self._fixed_height = height
        
        # 🎯 Monospace 폰트: 모든 문자가 동일한 너비
        self.setFont(QFont("Consolas", font_size))
        
        # 🎯 고정 크기: 레이아웃 엔진의 재계산 방지
        self.setFixedSize(width, height)
        
        # 중앙 정렬
        self.setAlignment(Qt.AlignCenter)
        
        # 텍스트 포맷 설정
        self.setTextFormat(Qt.PlainText)
        self.setWordWrap(False)
        
        # 크기 정책 고정
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    
    def sizeHint(self):
        """🎯 고정 크기 반환 - 레이아웃 재계산 방지"""
        return QSize(self._fixed_width, self._fixed_height)
    
    def minimumSizeHint(self):
        """🎯 고정 크기 반환 - 레이아웃 재계산 방지"""
        return QSize(self._fixed_width, self._fixed_height)
    
    def hasHeightForWidth(self):
        """🎯 높이가 너비에 의존하지 않음"""
        return False
    
    def setText(self, text: str):
        """
        텍스트 업데이트
        
        Monospace 폰트 + 고정 sizeHint 덕분에 
        텍스트 길이가 변해도 레이아웃이 재계산되지 않음
        """
        super().setText(text)
        # updateGeometry() 호출 방지 - 레이아웃 재계산 트리거하지 않음
