"""
설정 탭
필수/희망 강의 관리, 학점 범위 설정, 제외 시간 설정
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

from .base_tab import BaseTab
from ..base.theme import theme
from ..components.modern_button import ModernButton
from ..components.modern_treeview import ModernTreeview
from ..viewmodels.config_viewmodel import ConfigViewModel
from ..utils.drag_drop_manager import DragDropManager
from ..utils.popup_factory import PopupFactory

class ConfigTab(BaseTab):
    """설정 탭 UI (View)"""
    
    def __init__(self, parent, controller=None):
        super().__init__(parent, controller)
        
        # ViewModel 초기화
        config_service = controller.config_service if controller else None
        course_service = controller.course_service if controller else None
        self.vm = ConfigViewModel(config_service, course_service)
        self.vm.set_interaction_service(controller.interaction_service if controller else None)
        
        # DragDrop Manager
        self.dd_manager = DragDropManager()
        
        self.setup_ui()
        self.bind_viewmodel()
        
        # 초기 데이터 로드
        self.vm.load_data()
    
    def setup_ui(self):
        """UI 구성 (3단 레이아웃)"""
        # 하단: 액션 버튼 (가장 먼저 배치하여 공간 확보)
        self._create_action_buttons(self)
        
        # 메인 컨테이너 (3단)
        main_container = tk.Frame(self, bg=theme.BACKGROUND)
        main_container.pack(fill=tk.BOTH, expand=True, pady=(0, theme.SPACE_M))
        
        # 1. 왼쪽 열: 설정 (학점/요일/시간) - 갈색 느낌의 그룹
        self._create_settings_panel(main_container)
        
        tk.Frame(main_container, width=theme.SPACE_M, bg=theme.BACKGROUND).pack(side=tk.LEFT)
        
        # 2. 중앙 열: 필수 강의 - 노란 느낌의 그룹
        self._create_course_list_column(
            main_container, '📌 필수 강의', 'required', '반드시 포함'
        )
        
        tk.Frame(main_container, width=theme.SPACE_M, bg=theme.BACKGROUND).pack(side=tk.LEFT)
        
        # 3. 오른쪽 열: 희망 강의 - 노란 느낌의 그룹
        self._create_course_list_column(
            main_container, '⭐ 희망 강의', 'desired', '가능하면 포함'
        )

    def _create_settings_panel(self, parent):
        """왼쪽 열: 종합 설정 패널"""
        # 갈색 느낌의 테두리를 원하셨으므로 테두리 색상 조정 가능 (여기선 테마 유지)
        frame = tk.Frame(parent, bg=theme.SURFACE, highlightthickness=1, highlightbackground=theme.BORDER)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 헤더
        header = tk.Frame(frame, bg=theme.SURFACE)
        header.pack(fill=tk.X, padx=theme.SPACE_M, pady=theme.SPACE_S)
        tk.Label(header, text="⚙️ 기본 설정", font=(theme.FONT_FAMILY, theme.FONT_SIZE_SUBHEADING, 'bold'),
                 bg=theme.SURFACE).pack(side=tk.LEFT)
                 
        content = tk.Frame(frame, bg=theme.SURFACE)
        content.pack(fill=tk.BOTH, expand=True, padx=theme.SPACE_M, pady=theme.SPACE_S)
        
        # 1. 학점
        tk.Label(content, text="🎓 이수 학점", font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, 'bold'),
                 bg=theme.SURFACE).pack(anchor=tk.W, pady=(0, 5))
        
        credit_row = tk.Frame(content, bg=theme.SURFACE)
        credit_row.pack(fill=tk.X, pady=(0, theme.SPACE_L))
        self.min_credits_var = tk.StringVar()
        self.max_credits_var = tk.StringVar()
        
        self._create_entry(credit_row, self.min_credits_var, 5).pack(side=tk.LEFT)
        tk.Label(credit_row, text=' ~ ', bg=theme.SURFACE).pack(side=tk.LEFT)
        self._create_entry(credit_row, self.max_credits_var, 5).pack(side=tk.LEFT)
        
        # 2. 공강 요일
        tk.Label(content, text="🗓️ 공강 요일 (체크 시 제외)", font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, 'bold'),
                 bg=theme.SURFACE).pack(anchor=tk.W, pady=(0, 5))
        
        day_row = tk.Frame(content, bg=theme.SURFACE)
        day_row.pack(fill=tk.X, pady=(0, theme.SPACE_L))
        self.day_vars = {}
        for day in ['월', '화', '수', '목', '금']:
            var = tk.BooleanVar()
            self.day_vars[day] = var
            tk.Checkbutton(day_row, text=day, variable=var, bg=theme.SURFACE, 
                          activebackground=theme.SURFACE, selectcolor=theme.SURFACE).pack(side=tk.LEFT, padx=4)
                          
        # 3. 제외 시간
        tk.Label(content, text="🚫 제외 시간 설정", font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, 'bold'),
                 bg=theme.SURFACE).pack(anchor=tk.W, pady=(0, 5))
        
        # 입력 폼
        # 입력 폼 (Input Group Style - 통합형)
        time_form = tk.Frame(content, bg=theme.SURFACE)
        time_form.pack(fill=tk.X, pady=(0, 5))
        
        # 통합 컨테이너 (테두리로 묶음, 내용물만큼만 너비 차지 -> anchor='w')
        input_group = tk.Frame(time_form, bg=theme.SURFACE, 
                               highlightthickness=1, highlightbackground=theme.BORDER)
        input_group.pack(anchor='w')
        
        # 1. 요일 (좌측)
        self.ex_day_var = tk.StringVar(value='월')
        day_cb = ttk.Combobox(input_group, textvariable=self.ex_day_var, 
                             values=['월', '화', '수', '목', '금'], width=3, state="readonly")
        day_cb.pack(side=tk.LEFT, padx=(5, 2), pady=2)
        
        # 2. 시간 입력 (바로 이어서 배치)
        entry_bg = theme.BACKGROUND 
        self.ex_start_var = tk.StringVar(value='09:00')
        self.ex_end_var = tk.StringVar(value='10:00')
        
        tk.Entry(input_group, textvariable=self.ex_start_var, width=5, 
                relief='flat', bg=entry_bg, justify='center').pack(side=tk.LEFT, pady=2, padx=2)
        
        tk.Label(input_group, text='~', bg=theme.SURFACE, fg=theme.TEXT_SECONDARY).pack(side=tk.LEFT, padx=0)
        
        tk.Entry(input_group, textvariable=self.ex_end_var, width=5, 
                relief='flat', bg=entry_bg, justify='center').pack(side=tk.LEFT, pady=2, padx=2)
        
        # 3. 버튼 (바로 이어서 배치)
        ModernButton(input_group, text="+", variant='primary', padx=10, pady=0,
                     command=self._add_excluded_time).pack(side=tk.LEFT, fill=tk.Y)

        # 목록 (Treeview 높이 확보)
        self.ex_tree = ModernTreeview(content, columns=('Day', 'Time'), show='headings')
        self.ex_tree.heading('Day', text='요일'); self.ex_tree.column('Day', width=40, anchor=tk.CENTER)
        self.ex_tree.heading('Time', text='시간'); self.ex_tree.column('Time', width=120, anchor=tk.CENTER)
        self.ex_tree.pack(fill=tk.BOTH, expand=True)
        self.ex_tree.bind("<Button-3>", self._show_ex_time_menu)

    def _create_course_list_column(self, parent, title, list_type, desc):
        """중앙/오른쪽 열: 강의 목록 패널"""
        frame = tk.Frame(parent, bg=theme.SURFACE, highlightthickness=1, highlightbackground=theme.BORDER)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 헤더
        header = tk.Frame(frame, bg=theme.SURFACE)
        header.pack(fill=tk.X, padx=theme.SPACE_M, pady=theme.SPACE_S)
        tk.Label(header, text=title, font=(theme.FONT_FAMILY, theme.FONT_SIZE_SUBHEADING, 'bold'),
                 bg=theme.SURFACE).pack(side=tk.LEFT)
        
        # 버튼 영역 (가장 아래에 배치)
        btn_frame = tk.Frame(frame, bg=theme.SURFACE)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=theme.SPACE_M, pady=theme.SPACE_S)
        
        ModernButton(btn_frame, text='추가', variant='primary', 
                    command=lambda: self._show_add_dialog(list_type)).pack(side=tk.LEFT)
        ModernButton(btn_frame, text='삭제', variant='outline',
                    command=lambda: self._delete_course(list_type)).pack(side=tk.RIGHT)

        # 트리뷰 (남은 공간 채우기)
        columns = ('ID', 'Name', 'Prof')
        tree = ModernTreeview(frame, columns=columns, show='headings')
        tree.heading('ID', text='번호'); tree.column('ID', width=50, anchor=tk.CENTER)
        tree.heading('Name', text='강의명'); tree.column('Name', width=120, anchor=tk.CENTER)
        tree.heading('Prof', text='교수'); tree.column('Prof', width=60, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=theme.SPACE_M, pady=(0, theme.SPACE_S))
        
        self.dd_manager.register_draggable(tree, self._on_drop)
        
        if list_type == 'required':
            self.req_tree = tree
        else:
            self.des_tree = tree

    def _create_action_buttons(self, parent):
        """하단 액션 버튼 (좌: 저장/로드, 우: 생성)"""
        """하단 액션 버튼 (좌: 저장/로드, 우: 생성)"""
        frame = tk.Frame(parent, bg=theme.SURFACE, height=60)
        frame.pack(side=tk.BOTTOM, fill=tk.X, pady=theme.SPACE_M)
        
        # 왼쪽 (빨간 박스 영역)
        left_box = tk.Frame(frame, bg=theme.SURFACE)
        left_box.pack(side=tk.LEFT, padx=theme.SPACE_L)
        
        ModernButton(left_box, text="설정 저장", variant='outline', command=self._save_settings).pack(side=tk.LEFT, padx=5)
        ModernButton(left_box, text="설정 불러오기", variant='outline', command=self._load_settings_file).pack(side=tk.LEFT, padx=5)
        
        # 오른쪽 (파란 박스 영역)
        right_box = tk.Frame(frame, bg=theme.SURFACE)
        right_box.pack(side=tk.RIGHT, padx=theme.SPACE_L)
        
        ModernButton(right_box, text="🚀 시간표 생성", variant='primary', command=self.controller.generate_schedules).pack(side=tk.LEFT)

    def _load_settings_file(self):
        """설정 파일 불러오기"""
        initial_dir = os.path.join(self.controller.data_path, 'data') if self.controller else 'data'
        filepath = filedialog.askopenfilename(
            title="설정 파일 선택",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        if filepath:
            self.vm.load_config_from_file(filepath)

    def _create_entry(self, parent, variable, width):
        return tk.Entry(parent, textvariable=variable, width=width, bg=theme.SURFACE,
                       relief=tk.FLAT, highlightthickness=1, highlightbackground=theme.BORDER)

    def bind_viewmodel(self):
        """데이터 바인딩"""
        self.vm.bind('credits', lambda val: (self.min_credits_var.set(val[0]), self.max_credits_var.set(val[1])))
        self.vm.bind('excluded_days', self._update_day_vars)
        self.vm.bind('required_list', lambda data: self._update_tree(self.req_tree, data))
        self.vm.bind('desired_list', lambda data: self._update_tree(self.des_tree, data))
        self.vm.bind('excluded_times', self._update_ex_tree)

    def _update_day_vars(self, data):
        for day, is_checked in data.items():
            if day in self.day_vars:
                # 공강 요일: 데이터가 True이면 체크
                self.day_vars[day].set(is_checked)

    def _update_tree(self, tree, data):
        # populate 메서드를 사용하여 데이터 채우기 및 그리드 채움 효과 적용
        # tree['columns']로 컬럼 정보 가져오기 가능
        print(f"[DEBUG] Tree update: {len(data)} items")
        tree.populate(data, tree['columns'], min_rows=20)
        self.update_idletasks() # UI 강제 갱신
            
    def _update_ex_tree(self, data):
        # 데이터 포매팅 후 populate 호출
        formatted_data = [(d, f"{s} ~ {e}") for d, s, e in data]
        self.ex_tree.populate(formatted_data, self.ex_tree['columns'], min_rows=30)

    # --- Event Handlers ---

    def _on_drop(self, source, target, values, item):
        """드래그 앤 드롭 처리"""
        source_type = 'required' if source == self.req_tree else 'desired'
        target_type = 'required' if target == self.req_tree else 'desired'
        
        if source_type == target_type: return
        
        index = source.index(item)
        self.vm.move_course(source_type, target_type, index)

    def _show_add_dialog(self, list_type):
        """강의 추가 다이얼로그"""
        dialog = tk.Toplevel(self)
        dialog.title("강의 추가")
        dialog.geometry("300x250")
        dialog.configure(bg=theme.SURFACE)
        
        # 중앙 배치
        dialog.update_idletasks() # 크기 계산을 위해 업데이트
        width = 300
        height = 250
        
        # 부모 창 중앙 계산
        parent_x = self.winfo_toplevel().winfo_x()
        parent_y = self.winfo_toplevel().winfo_y()
        parent_w = self.winfo_toplevel().winfo_width()
        parent_h = self.winfo_toplevel().winfo_height()
        
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.configure(bg=theme.SURFACE)
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="※ 모든 항목을 입력할 필요는 없습니다", 
                 font=(theme.FONT_FAMILY, 10), fg=theme.TEXT_SECONDARY, bg=theme.SURFACE).pack(pady=(15, 5))
        
        tk.Label(dialog, text="🆔 강의번호", bg=theme.SURFACE).pack(pady=(5, 0))
        id_entry = tk.Entry(dialog); id_entry.pack(pady=2)
        
        tk.Label(dialog, text="📖 강의명", bg=theme.SURFACE).pack(pady=(5, 0))
        name_entry = tk.Entry(dialog); name_entry.pack(pady=2)
        
        tk.Label(dialog, text="👤 교수명", bg=theme.SURFACE).pack(pady=(5, 0))
        prof_entry = tk.Entry(dialog); prof_entry.pack(pady=2)
        
        def confirm():
            self.vm.add_course_filter(
                list_type, 
                name_entry.get().strip(), 
                prof_entry.get().strip(),
                id_entry.get().strip()
            )
            dialog.destroy()
            
        ModernButton(dialog, text="확인", variant='primary', command=confirm).pack(pady=15)

    def _delete_course(self, list_type):
        tree = self.req_tree if list_type == 'required' else self.des_tree
        sel = tree.selection()
        if sel:
            idx = tree.index(sel[0])
            self.vm.remove_course(list_type, idx)

    def _add_excluded_time(self):
        self.vm.add_excluded_time(
            self.ex_day_var.get(),
            self.ex_start_var.get(), 
            self.ex_end_var.get()
        )

    def _show_ex_time_menu(self, event):
        """제외 시간 우클릭 메뉴"""
        item = self.ex_tree.identify_row(event.y)
        if not item: return
        self.ex_tree.selection_set(item)
        
        menu = PopupFactory.create_menu(self, [
            {'label': '삭제', 'command': lambda: self._delete_ex_time(item)}
        ])
        PopupFactory.show_at_cursor(menu, event)

    def _delete_ex_time(self, item):
        idx = self.ex_tree.index(item)
        self.vm.remove_excluded_time(idx)

    def _save_settings(self):
        """설정 저장 (사용자 지정 경로)"""
        initial_dir = os.path.join(self.controller.data_path, 'data') if self.controller else 'data'
        filepath = filedialog.asksaveasfilename(
            title="설정 파일 저장",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=initial_dir,
            initialfile="config.json"
        )
        if filepath:
            self.vm.save_settings_to_file(filepath, self.min_credits_var.get(), self.max_credits_var.get(), self.day_vars)

    def refresh(self):
        self.vm.load_data()
