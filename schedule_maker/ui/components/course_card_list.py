"""
강의 카드 목록 컴포넌트
Required/Desired 강의를 카드 형태로 시각화하고, 핀(Pin) 기능을 제공.
"""
import tkinter as tk
from tkinter import ttk
from ..base.theme import theme
from .modern_button import ModernButton

class CourseCard(tk.Frame):
    """개별 강의 카드"""
    def __init__(self, parent, item, index, on_click=None, on_pin=None, on_delete=None):
        super().__init__(parent, bg=theme.SURFACE, highlightthickness=1, highlightbackground=theme.BORDER)
        self.item = item
        self.index = index
        self.on_click = on_click
        self.on_pin = on_pin
        self.on_delete = on_delete
        
        self.setup_ui()
        
        # 이벤트 바인딩
        self.bind("<Button-1>", self._on_card_click)
        for widget in self.winfo_children():
            widget.bind("<Button-1>", self._on_card_click)
            
    def setup_ui(self):
        # 왼쪽 컬러 바 (학점/유형에 따라 색상 변경 가능하지만 여기선 고정)
        bar_color = theme.PRIMARY if self.item.get('type') == 'required' else theme.SECONDARY
        start_bar = tk.Frame(self, bg=bar_color, width=5)
        start_bar.pack(side=tk.LEFT, fill=tk.Y)
        
        # 내용 컨테이너
        content = tk.Frame(self, bg=theme.SURFACE)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        # 1행: 강의명 + (필수)
        row1 = tk.Frame(content, bg=theme.SURFACE)
        row1.pack(fill=tk.X)
        
        name_txt = self.item.get('name', 'Unknown')
        tk.Label(row1, text=name_txt, font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, 'bold'),
                 bg=theme.SURFACE, fg=theme.TEXT_PRIMARY).pack(side=tk.LEFT)
                 
        if self.item.get('type') == 'required':
             tk.Label(row1, text="(필수)", font=(theme.FONT_FAMILY, theme.FONT_SIZE_CAPTION),
                 bg=theme.SURFACE, fg=theme.ERROR).pack(side=tk.LEFT, padx=5)
        
        # 핀 아이콘 (고정 여부)
        is_fixed = self.item.get('is_fixed', False)
        pin_color = theme.ERROR if is_fixed else theme.TEXT_TERTIARY
        pin_btn = tk.Label(row1, text="📌", font=(theme.FONT_FAMILY, 12),
                           bg=theme.SURFACE, fg=pin_color, cursor="hand2")
        pin_btn.pack(side=tk.LEFT, padx=5)
        pin_btn.bind("<Button-1>", self._on_pin_click)
        
        # 삭제 버튼 (우측 상단)
        del_btn = tk.Label(self, text="×", font=("Arial", 14), bg=theme.SURFACE, 
                          fg=theme.TEXT_TERTIARY, cursor="hand2")
        del_btn.place(relx=1.0, x=-5, y=0, anchor="ne")
        del_btn.bind("<Button-1>", self._on_delete_click)
        
        # 2행: 교수명 - 학점 - 시간
        row2 = tk.Frame(content, bg=theme.SURFACE)
        row2.pack(fill=tk.X, pady=(4, 0))
        
        # 교수 · 학점
        meta_txt = f"{self.item.get('professor', '')} · {self.item.get('credits', '?')}학점"
        tk.Label(row2, text=meta_txt, font=(theme.FONT_FAMILY, theme.FONT_SIZE_CAPTION),
                 bg=theme.SURFACE, fg=theme.TEXT_SECONDARY).pack(side=tk.LEFT)
                 
        # 시간 표시 (있는 경우)
        time_str = self.item.get('time', '')
        if time_str:
            # 칸이 좁으므로 줄바꿈하여 3행에 표시하거나, 우측에 표시?
            # 3행으로 분리 (가독성 위함)
            row3 = tk.Frame(content, bg=theme.SURFACE)
            row3.pack(fill=tk.X, pady=(2, 0))
            tk.Label(row3, text=time_str, font=(theme.FONT_FAMILY, theme.FONT_SIZE_CAPTION - 2),
                     bg=theme.SURFACE, fg=theme.PRIMARY).pack(side=tk.LEFT)
        
    def _on_card_click(self, event):
        if self.on_click:
            self.on_click(self.index)
            
    def _on_pin_click(self, event):
        if self.on_pin:
            self.on_pin(self.index)
        return "break" # 이벤트 전파 방지
        
    def _on_delete_click(self, event):
        if self.on_delete:
            self.on_delete(self.index)
        return "break"


class CourseCardList(tk.Frame):
    """스크롤 가능한 카드 목록 컨테이너"""
    def __init__(self, parent, on_card_interaction=None):
        super().__init__(parent, bg=theme.BACKGROUND)
        self.on_card_interaction = on_card_interaction # dict of callbacks
        
        self.canvas = tk.Canvas(self, bg=theme.BACKGROUND, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=theme.BACKGROUND)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.cards = []

    def populate(self, data):
        """데이터로 카드 목록 갱신"""
        # 기존 카드 제거
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.cards = []
        
        for i, item in enumerate(data):
            # callbacks
            # item dict should have: name, professor, credits, is_fixed, type
            card = CourseCard(
                self.scrollable_frame, 
                item, 
                i,
                on_click=self.on_card_interaction.get('click'),
                on_pin=self.on_card_interaction.get('pin'),
                on_delete=self.on_card_interaction.get('delete')
            )
            card.pack(fill=tk.X, padx=5, pady=5)
            self.cards.append(card)
            
        # Canvas width update
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
    def _on_canvas_configure(self, event):
        # Frame 너비를 Canvas 너비에 맞춤
        self.canvas.itemconfig(self.canvas.find_withtag("all")[0], width=event.width)
