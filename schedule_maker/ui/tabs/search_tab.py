"""
검색 탭
강의 검색 및 정보 확인, 설정에 추가 기능
"""
import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab
from ..base.theme import theme
from ..components.modern_button import ModernButton
from ..components.modern_treeview import ModernTreeview
from ..viewmodels.search_viewmodel import SearchViewModel
from ..utils.popup_factory import PopupFactory

class SearchTab(BaseTab):
    """검색 탭 UI (View)"""
    
    def __init__(self, parent, controller=None):
        super().__init__(parent, controller)
        
        # ViewModel 초기화
        course_service = controller.course_service if controller else None
        config_service = controller.config_service if controller else None
        self.vm = SearchViewModel(course_service, config_service)
        self.vm.set_interaction_service(controller.interaction_service if controller else None)
        
        self.setup_ui()
        self.bind_viewmodel()
        
        # 초기 모든 강의 로드 시뮬레이션
        self.vm.perform_search()
        
    def setup_ui(self):
        """UI 구성"""
        # 상단 검색 바 영역 (고정 높이 80px)
        self._create_search_bar(self)
        
        # 결과 요약/카운트
        self.results_count_var = tk.StringVar(value="검색 결과: 0개")
        count_label = tk.Label(self, textvariable=self.results_count_var, 
                             font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY),
                             bg=theme.BACKGROUND, fg=theme.TEXT_SECONDARY)
        count_label.pack(anchor=tk.W, padx=theme.SPACE_L, pady=(0, theme.SPACE_S))
        
        # 메인 결과 트리뷰
        self._create_results_list(self)
        
        # 하단 버튼 가이드 (팁)
        hint = tk.Label(self, text="💡 강의를 우클릭하여 필수/희망 목록에 추가할 수 있습니다.",
                       font=(theme.FONT_FAMILY, theme.FONT_SIZE_CAPTION),
                       bg=theme.BACKGROUND, fg=theme.TEXT_TERTIARY)
        hint.pack(side=tk.BOTTOM, pady=theme.SPACE_M)
        
    def _create_search_bar(self, parent):
        """검색 바 구성"""
        bar = tk.Frame(parent, bg=theme.SURFACE, highlightthickness=1, 
                       highlightbackground=theme.BORDER, height=80)
        bar.pack(fill=tk.X, pady=(0, theme.SPACE_M))
        bar.pack_propagate(False)
        
        inner = tk.Frame(bar, bg=theme.SURFACE)
        inner.pack(fill=tk.BOTH, expand=True, padx=theme.SPACE_L)
        
        # 검색어 입력
        tk.Label(inner, text="🔍 검색", font=(theme.FONT_FAMILY, theme.FONT_SIZE_SUBHEADING, 'bold'),
                 bg=theme.SURFACE, fg=theme.TEXT_PRIMARY).pack(side=tk.LEFT, padx=(0, theme.SPACE_M))
        
        self.search_var = tk.StringVar()
        # 입력 시마다 ViewModel의 query 업데이트 (Debounce 없이 일단 직접 연결)
        self.search_var.trace_add("write", self._on_query_change)
        
        entry = tk.Entry(inner, textvariable=self.search_var, font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY),
                        bg=theme.SURFACE, fg=theme.TEXT_PRIMARY, relief=tk.FLAT, 
                        highlightthickness=1, highlightbackground=theme.BORDER)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=theme.SPACE_M)
        entry.bind("<Return>", lambda e: self.vm.perform_search())
        
        # 옵션
        self.name_var = tk.BooleanVar(value=True)
        self.prof_var = tk.BooleanVar(value=True)
        for text, var in [("강의명", self.name_var), ("교수명", self.prof_var)]:
            tk.Checkbutton(inner, text=text, variable=var, bg=theme.SURFACE,
                          activebackground=theme.SURFACE, selectcolor=theme.SURFACE,
                          command=self._on_options_change).pack(side=tk.LEFT, padx=5)
            
        # 버튼
        ModernButton(inner, text="검색", variant='primary', command=self.vm.perform_search).pack(side=tk.LEFT, padx=(theme.SPACE_M, 0))

    def _create_results_list(self, parent):
        """결과 데이터 그리드"""
        frame = tk.Frame(parent, bg=theme.SURFACE, highlightthickness=1, highlightbackground=theme.BORDER)
        frame.pack(fill=tk.BOTH, expand=True, padx=theme.SPACE_L, pady=(0, theme.SPACE_S))
        
        columns = ('ID', 'Name', 'Credits', 'Professor', 'Time')
        self.tree = ModernTreeview(frame, columns=columns, show='headings')
        
        # 헤더 설정 및 정렬 바인딩
        col_info = [
            ('ID', '번호', 80), ('Name', '강의명', 250),
            ('Credits', '학점', 50), ('Professor', '교수', 100), ('Time', '시간', 350)
        ]
        
        for cid, label, width in col_info:
            self.tree.heading(cid, text=label, command=lambda c=cid: self.vm.toggle_sort(c))
            self.tree.column(cid, width=width, anchor=tk.CENTER)
            
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 우클릭 메뉴
        self.tree.bind("<Button-3>", self._show_context_menu)

    def bind_viewmodel(self):
        """데이터 바인딩"""
        self.vm.bind('results', self._update_results)
        self.vm.bind('sort_changed', self._update_sort_visuals)
        self.vm.bind('config_updated', lambda _: self.controller.refresh_tabs() if self.controller else None)

    def _on_query_change(self, *args):
        self.vm.query = self.search_var.get()

    def _on_options_change(self):
        self.vm.set_search_options(self.name_var.get(), self.prof_var.get())

    def _update_results(self, data):
        """결과 목록 갱신"""
        self.tree.delete(*self.tree.get_children())
        for item in data:
            self.tree.insert_with_alternating_colors('', 'end', values=item)
        self.results_count_var.set(f"검색 결과: {len(data)}개")

    def _update_sort_visuals(self, info):
        """헤더의 정렬 화살표 표시"""
        col_id, state = info
        # 모든 헤더 텍스트 초기화
        for cid in self.tree['columns']:
            # get current text without arrows
            current_heading = self.tree.heading(cid)
            text = current_heading['text'].replace(' ▲', '').replace(' ▼', '')
            if cid == col_id:
                if state == 1: text += ' ▲'
                elif state == 2: text += ' ▼'
            self.tree.heading(cid, text=text)

    def _show_context_menu(self, event):
        """우클릭 메뉴 표시"""
        item = self.tree.identify_row(event.y)
        if not item: return
        self.tree.selection_set(item)
        
        course_id = str(self.tree.item(item, "values")[0])
        course_name = self.tree.item(item, "values")[1]
        
        # 메뉴 구조 정의
        menu_structure = [
            {
                'label': '📌 필수 강의에 추가',
                'submenu': [
                    {'label': f"이 강좌만 추가 (번호 고정)", 
                     'command': lambda: self.vm.add_to_config(course_id, 'required', 'fixed')},
                    {'label': f"강의명 '{course_name}'으로 추가", 
                     'command': lambda: self.vm.add_to_config(course_id, 'required', 'name')},
                    {'label': f"강의명+교수명으로 추가", 
                     'command': lambda: self.vm.add_to_config(course_id, 'required', 'name_prof')}
                ]
            },
            {
                'label': '⭐ 희망 강의에 추가',
                'submenu': [
                    {'label': f"이 강좌만 추가 (번호 고정)", 
                     'command': lambda: self.vm.add_to_config(course_id, 'desired', 'fixed')},
                    {'label': f"강의명 '{course_name}'으로 추가", 
                     'command': lambda: self.vm.add_to_config(course_id, 'desired', 'name')},
                    {'label': f"강의명+교수명으로 추가", 
                     'command': lambda: self.vm.add_to_config(course_id, 'desired', 'name_prof')}
                ]
            }
        ]
        
        menu = PopupFactory.create_menu(self, menu_structure)
        PopupFactory.show_at_cursor(menu, event)

    def refresh(self):
        """데이터 수동 갱신"""
        if self.vm.query:
             self.vm.perform_search()
        else:
             self.vm.perform_search() # 전체 목록 로드 목적
