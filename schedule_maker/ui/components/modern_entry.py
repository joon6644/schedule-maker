"""
현대적인 스타일 입력 필드 컴포넌트
"""
import tkinter as tk
from ..base.theme import theme
from ..base.styled_component import StyledComponent


class ModernEntry(tk.Entry, StyledComponent):
    """
    현대적 스타일 입력 필드
    
    Args:
        parent: 부모 위젯
        placeholder: 플레이스홀더 텍스트
        **kwargs: 추가 tkinter Entry 옵션
    """
    
    def __init__(self, parent, placeholder='', **kwargs):
        self.placeholder = placeholder
        self.placeholder_color = theme.TEXT_TERTIARY
        self.normal_color = theme.TEXT_PRIMARY
        
        default_config = {
            'bg': theme.SURFACE,
            'fg': theme.TEXT_PRIMARY,
            'font': (theme.FONT_FAMILY.split(',')[0].strip("'"), theme.FONT_SIZE_BODY),
            'relief': tk.FLAT,
            'borderwidth': 1,
            'highlightthickness': 2,
            'highlightbackground': theme.BORDER,
            'highlightcolor': theme.PRIMARY,
            'insertbackground': theme.TEXT_PRIMARY,
        }
        
        config = {**default_config, **kwargs}
        
        tk.Entry.__init__(self, parent, **config)
        StyledComponent.__init__(self)
        
        # 플레이스홀더 설정
        if placeholder:
            self._setup_placeholder()
    
    def _setup_placeholder(self):
        """플레이스홀더 기능 설정"""
        self._showing_placeholder = True
        self.insert(0, self.placeholder)
        self.config(fg=self.placeholder_color)
        
        def on_focus_in(e):
            if self._showing_placeholder:
                self.delete(0, tk.END)
                self.config(fg=self.normal_color)
                self._showing_placeholder = False
        
        def on_focus_out(e):
            if not self.get():
                self.insert(0, self.placeholder)
                self.config(fg=self.placeholder_color)
                self._showing_placeholder = True
        
        self.bind('<FocusIn>', on_focus_in)
        self.bind('<FocusOut>', on_focus_out)
    
    def get_value(self):
        """플레이스홀더가 아닌 실제 값만 반환"""
        if self._showing_placeholder:
            return ''
        return self.get()


class SearchEntry(tk.Frame, StyledComponent):
    """
    검색 아이콘이 포함된 검색 입력 필드
    """
    
    def __init__(self, parent, placeholder='검색...', on_change=None, **kwargs):
        tk.Frame.__init__(self, parent, bg=theme.SURFACE)
        StyledComponent.__init__(self)
        
        # 컨테이너 프레임 (테두리 효과용)
        self.container = tk.Frame(
            self,
            bg=theme.SURFACE,
            highlightthickness=2,
            highlightbackground=theme.BORDER,
            highlightcolor=theme.PRIMARY,
        )
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # 검색 아이콘 (유니코드)
        icon_label = tk.Label(
            self.container,
            text='🔍',
            bg=theme.SURFACE,
            fg=theme.TEXT_TERTIARY,
            font=(theme.FONT_FAMILY.split(',')[0].strip("'"), theme.FONT_SIZE_BODY),
        )
        icon_label.pack(side=tk.LEFT, padx=(theme.SPACE_M, theme.SPACE_S))
        
        # 입력 필드
        self.entry = tk.Entry(
            self.container,
            bg=theme.SURFACE,
            fg=theme.TEXT_PRIMARY,
            font=(theme.FONT_FAMILY.split(',')[0].strip("'"), theme.FONT_SIZE_BODY),
            relief=tk.FLAT,
            borderwidth=0,
            insertbackground=theme.TEXT_PRIMARY,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, theme.SPACE_M))
        
        # 플레이스홀더
        self.placeholder = placeholder
        self._showing_placeholder = True
        self.entry.insert(0, placeholder)
        self.entry.config(fg=theme.TEXT_TERTIARY)
        
        def on_focus_in(e):
            if self._showing_placeholder:
                self.entry.delete(0, tk.END)
                self.entry.config(fg=theme.TEXT_PRIMARY)
                self._showing_placeholder = False
        
        def on_focus_out(e):
            if not self.entry.get():
                self.entry.insert(0, self.placeholder)
                self.entry.config(fg=theme.TEXT_TERTIARY)
                self._showing_placeholder = True
        
        self.entry.bind('<FocusIn>', on_focus_in)
        self.entry.bind('<FocusOut>', on_focus_out)
        
        # 변경 이벤트
        if on_change:
            self.entry.bind('<KeyRelease>', lambda e: on_change())
    
    def get_value(self):
        """실제 값 반환"""
        if self._showing_placeholder:
            return ''
        return self.entry.get()
    
    def set_value(self, value):
        """값 설정"""
        self.entry.delete(0, tk.END)
        if value:
            self.entry.insert(0, value)
            self.entry.config(fg=theme.TEXT_PRIMARY)
            self._showing_placeholder = False
        else:
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=theme.TEXT_TERTIARY)
            self._showing_placeholder = True
