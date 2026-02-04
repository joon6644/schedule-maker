"""
팝업 메뉴 팩토리
컨텍스트 메뉴 및 버튼 드롭다운 메뉴 생성 로직 공통화
"""
import tkinter as tk
from tkinter import messagebox
from typing import List, Tuple, Callable, Any, Dict
from ..base.theme import theme

class PopupFactory:
    """
    팝업 메뉴 생성을 담당하는 팩토리 클래스
    """
    
    @staticmethod
    def create_menu(parent, items: List[Dict[str, Any]]) -> tk.Menu:
        """
        메뉴 생성 및 반환 (재귀적 서브메뉴 지원)
        
        Args:
            parent: 부모 위젯
            items: 메뉴 아이템 리스트. 각 아이템은 딕셔너리 형태
                   {'label': str, 'command': callable, 'separator': bool, 'state': str, 'submenu': List}
        """
        # 폰트 설정
        menu_font = (theme.FONT_FAMILY.split(',')[0].strip("'"), theme.FONT_SIZE_BODY)
        
        menu = tk.Menu(parent, tearoff=0, bg=theme.SURFACE, fg=theme.TEXT_PRIMARY, 
                      activebackground=theme.PRIMARY_LIGHTER, activeforeground=theme.PRIMARY,
                      font=menu_font)
        
        for item in items:
            if item.get('separator'):
                menu.add_separator()
            elif 'submenu' in item and item['submenu']:
                # 서브메뉴 재귀 생성
                submenu = PopupFactory.create_menu(menu, item['submenu'])
                menu.add_cascade(
                    label=item.get('label', ''),
                    menu=submenu,
                    state=item.get('state', 'normal')
                )
            else:
                menu.add_command(
                    label=item.get('label', ''),
                    command=item.get('command'),
                    state=item.get('state', 'normal'),
                    background=item.get('background') # 헤더용 배경색 지정 가능
                )
        return menu

    @staticmethod
    def show_at_cursor(menu: tk.Menu, event):
        """마우스 커서 위치에 메뉴 표시"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
            
    @staticmethod
    def show_above_button(menu: tk.Menu, button: tk.Widget):
        """버튼 위에 메뉴 표시 (위로 전개)"""
        menu.update_idletasks()
        
        x = button.winfo_rootx()
        y = button.winfo_rooty()
        
        # 메뉴 높이 추정 (항목 수 * 30px + 여유분)
        # 정확한 높이를 알기 어려우므로 대략적인 값 사용
        estimated_height = 0
        try:
            # item count
            count = menu.index('end')
            if count is None: count = 0
            else: count += 1
            estimated_height = count * 35 # 항목당 높이
        except:
             estimated_height = 150
             
        menu.post(x, y - estimated_height)
