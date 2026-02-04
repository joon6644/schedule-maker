"""
스타일 적용 기본 컴포넌트 클래스
모든 커스텀 UI 컴포넌트의 베이스
"""
import tkinter as tk
from tkinter import ttk
from .theme import theme


class StyledComponent:
    """
    테마를 자동으로 적용하는 기본 컴포넌트 클래스
    모든 커스텀 위젯이 상속
    """
    
    def __init__(self):
        self.theme = theme
        self._hover_bindings = []
    
    def apply_theme(self, widget, **custom_styles):
        """
        위젯에 테마 스타일 적용
        
        Args:
            widget: 스타일을 적용할 tkinter 위젯
            **custom_styles: 커스텀 스타일 오버라이드
        """
        default_styles = {
            'font': (theme.FONT_FAMILY.split(',')[0].strip("'"), theme.FONT_SIZE_BODY),
            'bg': theme.SURFACE,
            'fg': theme.TEXT_PRIMARY,
        }
        
        # 커스텀 스타일로 오버라이드
        styles = {**default_styles, **custom_styles}
        
        # 위젯에 적용 (가능한 속성만)
        for key, value in styles.items():
            try:
                widget.config(**{key: value})
            except tk.TclError:
                # 해당 위젯이 지원하지 않는 옵션은 무시
                pass
    
    def bind_hover(self, widget, enter_callback=None, leave_callback=None):
        """
        호버 이벤트 바인딩 헬퍼
        
        Args:
            widget: 이벤트를 바인딩할 위젯
            enter_callback: 마우스 진입 시 콜백
            leave_callback: 마우스 이탈 시 콜백
        """
        if enter_callback:
            widget.bind('<Enter>', enter_callback)
        if leave_callback:
            widget.bind('<Leave>', leave_callback)
        
        self._hover_bindings.append((widget, enter_callback, leave_callback))
    
    def create_hover_effect(self, widget, normal_bg, hover_bg):
        """
        간단한 배경색 호버 효과 생성
        
        Args:
            widget: 효과를 적용할 위젯
            normal_bg: 일반 배경색
            hover_bg: 호버 배경색
        """
        def on_enter(e):
            try:
                widget.config(bg=hover_bg)
            except:
                pass
        
        def on_leave(e):
            try:
                widget.config(bg=normal_bg)
            except:
                pass
        
        self.bind_hover(widget, on_enter, on_leave)


class ModernFrame(tk.Frame, StyledComponent):
    """테마가 적용된 현대적 프레임"""
    
    def __init__(self, parent, bg=None, padding=0, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        StyledComponent.__init__(self)
        
        # 배경색 설정
        if bg is None:
            bg = theme.SURFACE
        
        self.config(
            bg=bg,
            padx=padding if isinstance(padding, int) else padding[0],
            pady=padding if isinstance(padding, int) else padding[1] if len(padding) > 1 else padding[0]
        )


class CardFrame(tk.Frame, StyledComponent):
    """
    카드 스타일 프레임
    약간의 그림자 효과와 둥근 모서리 느낌
    """
    
    def __init__(self, parent, bg=None, border_color=None, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        StyledComponent.__init__(self)
        
        if bg is None:
            bg = theme.SURFACE
        if border_color is None:
            border_color = theme.BORDER
        
        self.config(
            bg=bg,
            highlightthickness=1,
            highlightbackground=border_color,
            highlightcolor=border_color,
        )
