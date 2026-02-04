"""
현대적인 스타일 Treeview 컴포넌트
"""
import tkinter as tk
from tkinter import ttk
from ..base.theme import theme


class ModernTreeview(ttk.Treeview):
    """
    현대적 스타일 Treeview
    스타일이 자동으로 적용되며 호버 효과 포함
    
    Args:
        parent: 부모 위젯
        columns: 열 정의
        **kwargs: 추가 ttk.Treeview 옵션
    """
    
    def __init__(self, parent, columns=(), **kwargs):
        # 스타일 이름 생성
        style_name = f'Modern.Treeview'
        
        # ttk 스타일 설정
        style = ttk.Style()
        
        # Treeview 스타일
        style.configure(
            style_name,
            background=theme.SURFACE,
            foreground=theme.TEXT_PRIMARY,
            fieldbackground=theme.SURFACE,
            borderwidth=1,
            relief='flat',
        )
        
        # Heading 스타일
        style.configure(
            f'{style_name}.Heading',
            background=theme.BACKGROUND,
            foreground=theme.TEXT_PRIMARY,
            relief='flat',
            borderwidth=1,
        )
        
        # 선택 시 스타일
        style.map(
            style_name,
            background=[('selected', '!focus', theme.BORDER), ('selected', theme.PRIMARY_LIGHTER)],
            foreground=[('selected', '!focus', theme.TEXT_PRIMARY), ('selected', theme.TEXT_PRIMARY)],
        )
        
        # Heading 호버 효과
        style.map(
            f'{style_name}.Heading',
            background=[('active', theme.SURFACE_HOVER)],
        )
        
        default_config = {
            'columns': columns,
            'show': 'headings',  # 'tree headings'에서 'headings'로 변경 - #0 컬럼 숨김
            'selectmode': 'browse',
            'style': style_name,
        }
        
        config = {**default_config, **kwargs}
        
        super().__init__(parent, **config)
        
        # 행 높이 설정으로 정렬 개선
        style.configure(style_name, rowheight=25)
        
        # 교차 행 색상 효과 (태그 사용)
        self.tag_configure('odd', background=theme.SURFACE)
        self.tag_configure('even', background=theme.BACKGROUND)
        
        # 호버 효과를 위한 태그
        self.tag_configure('hover', background=theme.SURFACE_HOVER)
        
        # 특수 상태 태그
        self.tag_configure('desired', foreground=theme.PRIMARY)
        
        # 빈 공간 클릭 시 선택 해제 바인딩
        self.bind("<Button-1>", self._on_click, add="+")
        # 선택 이벤트 바인딩 (더미 선택 방지)
        self.bind("<<TreeviewSelect>>", self._on_select, add="+")
        self._setup_scrollbar(parent)
    
    def _setup_scrollbar(self, parent):
        """스크롤바 자동 설정"""
        # 세로 스크롤바는 일반적으로 Treeview 부모 컨테이너에서 설정
        # 여기서는 스크롤 명령만 연결
        pass
    
    def insert_with_alternating_colors(self, parent='', index='end', **kwargs):
        """교차 색상이 적용된 행 삽입"""
        # 현재 행 수 확인
        children = self.get_children(parent)
        row_index = len(children)
        
        # 태그 결정
        tags = list(kwargs.get('tags', ()))
        tags.append('even' if row_index % 2 == 0 else 'odd')
        kwargs['tags'] = tuple(tags)
        
        return self.insert(parent, index, **kwargs)
    
    def populate(self, data, columns, min_rows=20):
        """
        데이터로 Treeview 채우기
        
        Args:
            data: 행 데이터 리스트 (각 행은 딕셔너리 또는 튜플)
            columns: 열 이름 리스트
            min_rows: 최소 표시 행 수 (빈 공간 채우기용)
        """
        # 기존 데이터 삭제
        for item in self.get_children():
            self.delete(item)
        
        # 새 데이터 삽입
        current_idx = 0
        for idx, row in enumerate(data):
            if isinstance(row, dict):
                values = [row.get(col, '') for col in columns]
            else:
                values = row
            
            tags = ('even',) if idx % 2 == 0 else ('odd',)
            self.insert('', 'end', values=values, tags=tags)
            current_idx = idx + 1
            
        # 빈 공간 채우기 (더미 데이터)
        for i in range(max(0, min_rows - current_idx)):
            parity_idx = current_idx + i
            tags = ('even', 'dummy') if parity_idx % 2 == 0 else ('odd', 'dummy')
            # 빈 값으로 채움
            empty_values = [''] * len(columns)
            self.insert('', 'end', values=empty_values, tags=tags)

    def _on_click(self, event):
        """클릭 이벤트 핸들러: 빈 공간 클릭 시 선택 해제"""
        region = self.identify_region(event.x, event.y)
        if region == "nothing":
            self.selection_remove(self.selection())

    def _on_select(self, event):
        """선택 이벤트 핸들러: 더미 항목 선택 방지"""
        sel = self.selection()
        if not sel: return
        
        # 더미 태그 확인
        # 선택된 모든 항목 검사 (여러 개일 수 있음)
        for item in sel:
            if 'dummy' in self.item(item, 'tags'):
                self.selection_remove(item)
