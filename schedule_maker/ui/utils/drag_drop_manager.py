"""
드래그 앤 드롭 관리자
UI 컴포넌트에서 드래그 앤 드롭 로직을 분리하여 재사용성을 높임
"""
import tkinter as tk
from typing import Callable, Any, Optional

class DragDropManager:
    """
    드래그 앤 드롭 기능을 관리하는 유틸리티 클래스
    
    사용법:
    manager = DragDropManager()
    manager.register_source(treeview, on_drag_start)
    manager.register_target(treeview, on_drop)
    """
    
    def __init__(self):
        self._drag_data = {"item": None, "source": None, "values": None}
        self._on_drop_callback = None
        
    def register_draggable(self, widget, on_drop_callback: Callable[[str, str, tuple, Any], None]):
        """
        위젯을 드래그 소스이자 드롭 타겟으로 등록
        
        Args:
            widget: 대상 위젯 (Treeview 등)
            on_drop_callback: 드롭 발생 시 호출될 콜백 (source_widget, target_widget, values, item)
        """
        widget.bind("<ButtonPress-1>", self._on_drag_start)
        widget.bind("<B1-Motion>", self._on_drag_motion)
        widget.bind("<ButtonRelease-1>", lambda e: self._on_drag_release(e, on_drop_callback))
        
    def _on_drag_start(self, event):
        """드래그 시작 핸들러"""
        widget = event.widget
        # Treeview라고 가정
        if not hasattr(widget, 'identify_row'):
            return
            
        item = widget.identify_row(event.y)
        if not item:
            return
            
        values = widget.item(item, "values")
        # 빈 행 무시 (값이 없거나 모든 컬럼이 비어있음)
        if not values or all(not str(v) for v in values):
            return
            
        self._drag_data = {
            "item": item,
            "source": widget,
            "values": values
        }
        
        # 커서 변경
        widget.configure(cursor="fleur")

    def _on_drag_motion(self, event):
        """드래그 중 핸들러"""
        # 필요 시 시각적 효과 추가 가능
        pass

    def _on_drag_release(self, event, callback):
        """드래그 종료 핸들러"""
        source_widget = self._drag_data["source"]
        
        # 커서 복구
        if source_widget:
            source_widget.configure(cursor="")
            
        if not self._drag_data["item"]:
            return
            
        # 드롭된 위치의 위젯 확인
        x, y = event.x_root, event.y_root
        target_widget = event.widget.winfo_containing(x, y)
        
        # 유효한 드롭이면 콜백 호출
        if target_widget and source_widget and target_widget != source_widget:
            # 타겟이 트리뷰 내부 컴포넌트일 수 있으므로 상위 위젯 확인 로직은
            # 호출부(ViewModel/View)에서 판단하거나 여기서 좀 더 정교하게 처리해야 함.
            # 여기서는 단순히 위젯 객체를 넘김.
            callback(source_widget, target_widget, self._drag_data["values"], self._drag_data["item"])
            
        # 데이터 초기화
        self._drag_data = {"item": None, "source": None, "values": None}
