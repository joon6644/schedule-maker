"""
현대적인 스타일 버튼 컴포넌트
호버 효과, 다양한 변형, 아이콘 지원
"""
import tkinter as tk
from ..base.theme import theme
from ..base.styled_component import StyledComponent


class ModernButton(tk.Button, StyledComponent):
    """
    현대적 스타일 버튼
    
    Args:
        parent: 부모 위젯
        text: 버튼 텍스트
        variant: 버튼 스타일 ('primary', 'secondary', 'accent', 'danger', 'ghost', 'outline')
        command: 클릭 시 실행할 함수
        **kwargs: 추가 tkinter Button 옵션
    """
    
    def __init__(self, parent, text='', variant='primary', command=None, **kwargs):
        self.variant = variant
        
        # 스타일 가져오기
        style = theme.get_button_style(variant)
        
        # 기본 설정
        default_config = {
            'text': text,
            'command': command,
            'bg': style['bg'],
            'fg': style['fg'],
            'activebackground': style['active_bg'],
            'activeforeground': style['fg'],
            'font': (theme.FONT_FAMILY.split(',')[0].strip("'"), theme.FONT_SIZE_BODY), # Bold 제거 또는 사이즈 조정
            'relief': tk.FLAT,
            'borderwidth': 0,
            'cursor': 'hand2',
            'padx': theme.SPACE_L, # 패딩 유지
            'pady': 6, # 세로 패딩 약간 조정 (8->6)
        }
        
        # Outline 변형 - 연한 색상의 세련된 테두리
        if variant == 'outline' and 'border' in style:
            default_config['relief'] = tk.FLAT
            default_config['borderwidth'] = 0
            default_config['highlightthickness'] = 1
            default_config['highlightbackground'] = theme.BORDER  # 연한 회색 테두리
            default_config['highlightcolor'] = style['border']  # 포커스 시 메인 색상
            default_config['bg'] = theme.SURFACE_HOVER  # 약간의 배경색
        
        # 커스텀 설정으로 오버라이드
        config = {**default_config, **kwargs}
        
        tk.Button.__init__(self, parent, **config)
        StyledComponent.__init__(self)
        
        # 호버 효과 추가
        self._setup_hover_effect(style)
    
    def _setup_hover_effect(self, style):
        """호버 효과 설정"""
        normal_bg = style['bg']
        hover_bg = style['hover_bg']
        
        def on_enter(e):
            self.config(bg=hover_bg)
        
        def on_leave(e):
            self.config(bg=normal_bg)
        
        self.bind_hover(self, on_enter, on_leave)


class IconButton(tk.Button, StyledComponent):
    """
    아이콘 전용 작은 버튼
    """
    
    def __init__(self, parent, text='', command=None, **kwargs):
        default_config = {
            'text': text,
            'command': command,
            'bg': theme.SURFACE,
            'fg': theme.TEXT_SECONDARY,
            'activebackground': theme.SURFACE_HOVER,
            'activeforeground': theme.TEXT_PRIMARY,
            'font': (theme.FONT_FAMILY.split(',')[0].strip("'"), theme.FONT_SIZE_BODY),
            'relief': tk.FLAT,
            'borderwidth': 0,
            'cursor': 'hand2',
            'padx': theme.SPACE_S,
            'pady': theme.SPACE_S,
        }
        
        config = {**default_config, **kwargs}
        
        tk.Button.__init__(self, parent, **config)
        StyledComponent.__init__(self)
        
        # 호버 효과
        def on_enter(e):
            self.config(bg=theme.SURFACE_HOVER, fg=theme.TEXT_PRIMARY)
        
        def on_leave(e):
            self.config(bg=theme.SURFACE, fg=theme.TEXT_SECONDARY)
        
        self.bind_hover(self, on_enter, on_leave)


class LinkButton(tk.Label, StyledComponent):
    """
    링크 스타일 버튼 (Label 기반)
    """
    
    def __init__(self, parent, text='', command=None, **kwargs):
        default_config = {
            'text': text,
            'bg': theme.SURFACE,
            'fg': theme.PRIMARY,
            'font': (theme.FONT_FAMILY.split(',')[0].strip("'"), theme.FONT_SIZE_BODY),
            'cursor': 'hand2',
        }
        
        config = {**default_config, **kwargs}
        
        tk.Label.__init__(self, parent, **config)
        StyledComponent.__init__(self)
        
        # 클릭 이벤트
        if command:
            self.bind('<Button-1>', lambda e: command())
        
        # 호버 효과 (색상 변경 + 밑줄)
        def on_enter(e):
            self.config(fg=theme.PRIMARY_DARK)
            # 밑줄은 font 설정으로 추가
            current_font = self.cget('font')
            if isinstance(current_font, tuple):
                self.config(font=(*current_font[:2], 'underline'))
        
        def on_leave(e):
            self.config(fg=theme.PRIMARY)
            current_font = self.cget('font')
            if isinstance(current_font, tuple):
                self.config(font=current_font[:2])
        
        self.bind_hover(self, on_enter, on_leave)
