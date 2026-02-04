"""
Search Interface
Replaces SearchTab with modern Fluent UI components.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QHeaderView, QTableWidgetItem, QMenu,
    QAbstractItemView
)

from PySide6.QtCore import Qt, Signal, Slot
from qfluentwidgets import (
    SearchLineEdit, CheckBox, PrimaryPushButton, TableWidget,
    FluentIcon as FIF, RoundMenu, Action, BodyLabel, TitleLabel,
    SubtitleLabel, StrongBodyLabel, PushButton, SegmentedWidget
)

from ..viewmodels.search_viewmodel import SearchViewModel


class CourseDetailWidget(QWidget):
    """
    Widget to be displayed in the expanded row.
    Single Row Layout: [Toggle (Req/Des)] <Stretch> [Btn1] [Btn2] [Btn3]
    """
    def __init__(self, vm, course_id, course_name, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.course_id = course_id
        self.course_name = course_name
        self.current_mode = 'required' # Default
        
        self._setup_ui()
        self.setFixedHeight(70) # Compact height - Adjusted request
        self.setStyleSheet("background-color: #f9f9f9; border-bottom: 1px solid #e0e0e0;")

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 0, 40, 0)
        main_layout.setSpacing(20)

        # 1. Segmented Toggle
        # Fix: Prevent vertical stretching which causes the "empty block" artifact
        self.pivot = SegmentedWidget(self)
        self.pivot.addItem("required", "📌 필수 추가", lambda: self._update_mode('required'))
        self.pivot.addItem("desired", "⭐ 희망 추가", lambda: self._update_mode('desired'))
        self.pivot.setCurrentItem("required")
        self.pivot.setFixedHeight(32) # Force compact height
        
        # Align VCenter to keep it centered vertically
        main_layout.addWidget(self.pivot, 0, Qt.AlignVCenter)
        
        # Add extra spacing as requested (20 * 3 = 60)
        main_layout.addSpacing(60)
        
        # 2. Action Buttons Group
        self.right_group = QWidget(self)
        self.right_group.setObjectName("rightGroup")
        # Match SegmentedWidget styling
        self.right_group.setStyleSheet("""
            #rightGroup {
                background-color: #f8f8f8; 
                border: 1px solid #e5e5e5;
                border-radius: 6px;
            }
        """)
        group_layout = QHBoxLayout(self.right_group)
        group_layout.setContentsMargins(8, 3, 8, 3)
        group_layout.setSpacing(10)
        
        self.btn_fixed = PushButton(f"이 강의만 추가 ({self.course_id})", self)
        self.btn_fixed.setFixedWidth(180)
        self.btn_fixed.setCursor(Qt.PointingHandCursor)
        self.btn_fixed.clicked.connect(lambda: self._on_add('fixed'))
        
        self.btn_name = PushButton("이 강의명으로 추가", self)
        self.btn_name.setFixedWidth(180)
        self.btn_name.setCursor(Qt.PointingHandCursor)
        self.btn_name.clicked.connect(lambda: self._on_add('name'))
        
        self.btn_prof = PushButton("강의명 + 교수로 추가", self)
        self.btn_prof.setFixedWidth(180)
        self.btn_prof.setCursor(Qt.PointingHandCursor)
        self.btn_prof.clicked.connect(lambda: self._on_add('name_prof'))
        
        group_layout.addWidget(self.btn_fixed)
        group_layout.addWidget(self.btn_name)
        group_layout.addWidget(self.btn_prof)
        
        # Add the group container to main layout
        main_layout.addWidget(self.right_group, 0, Qt.AlignVCenter)
        
        main_layout.addStretch(1)
        
        # Initial Style Update
        self._update_mode('required')

    def _update_mode(self, mode):
        self.current_mode = mode
        
        base_style = """
            PushButton {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                color: #333333;
                font-family: 'Segoe UI';
                font-size: 13px;
                padding: 4px;
            }
        """
        
        if mode == 'required':
             hover_style = """
                PushButton:hover {
                    background-color: #ffe6e6; 
                    border: 1px solid #ff4d4f;
                    color: #d9363e;
                }
                PushButton:pressed {
                    background-color: #ffcccc;
                }
             """
             # Icon removed as requested
        else:
             hover_style = """
                PushButton:hover {
                    background-color: #fffbe6;
                    border: 1px solid #faad14;
                    color: #d48806;
                }
                PushButton:pressed {
                    background-color: #fff1b8;
                }
             """
             # Icon removed as requested
        
        final_style = base_style + hover_style
        
        self.btn_fixed.setStyleSheet(final_style)
        self.btn_name.setStyleSheet(final_style)
        self.btn_prof.setStyleSheet(final_style)

    def _on_add(self, method):
        self.vm.add_to_config(self.course_id, self.current_mode, method)



class SearchInterface(QWidget):
    """
    Search Interface with Fluent Design
    """
    
    def __init__(self, parent=None, controller=None):
        super().__init__(parent=parent)
        self.setObjectName("searchInterface")
        
        self.controller = controller
        # ViewModel Initialization
        course_service = controller.course_service if controller else None
        config_service = controller.config_service if controller else None
        self.vm = SearchViewModel(course_service, config_service)
        
        # Inject Interaction Service (Critical for Alerts)
        if controller and controller.interaction_service:
            self.vm.set_interaction_service(controller.interaction_service)
        elif parent: # Fallback
            self.vm.set_interaction_service(parent)
        
        self._setup_ui()
        self._bind_viewmodel()
        
        # Initial search simulation
        self.vm.perform_search()

    def _setup_ui(self):
        # Main Layout
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(15)

        # Header
        self.titleLabel = TitleLabel("강의 검색", self)
        self.vBoxLayout.addWidget(self.titleLabel)

        # Search Bar Area
        self.searchLayout = QHBoxLayout()
        
        self.searchLineEdit = SearchLineEdit(self)
        self.searchLineEdit.setPlaceholderText("강의명, 교수명 검색...")
        self.searchLineEdit.setFixedWidth(300)
        self.searchLineEdit.textChanged.connect(self._on_query_change)
        self.searchLineEdit.returnPressed.connect(self.vm.perform_search)
        self.searchLayout.addWidget(self.searchLineEdit)
        
        # Options
        self.nameCheckBox = CheckBox("강의명", self)
        self.nameCheckBox.setChecked(True)
        self.nameCheckBox.stateChanged.connect(self._on_options_change)
        self.searchLayout.addWidget(self.nameCheckBox)
        
        self.profCheckBox = CheckBox("교수명", self)
        self.profCheckBox.setChecked(True)
        self.profCheckBox.stateChanged.connect(self._on_options_change)
        self.searchLayout.addWidget(self.profCheckBox)
        
        self.searchLayout.addStretch(1)
        
        # Search Button (Optional, since Enter works, but good for UX)
        self.searchButton = PrimaryPushButton("검색", self)
        self.searchButton.setIcon(FIF.SEARCH)
        self.searchButton.clicked.connect(self.vm.perform_search)
        self.searchLayout.addWidget(self.searchButton)

        self.vBoxLayout.addLayout(self.searchLayout)
        
        # Results Count
        self.countLabel = BodyLabel("검색 결과: 0개", self)
        self.countLabel.setTextColor(Qt.GlobalColor.gray, Qt.GlobalColor.gray) # Fluent way might differ
        self.vBoxLayout.addWidget(self.countLabel)

        # Table
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['강의번호', '강의명', '학점', '교수', '시간'])
        self.table.verticalHeader().hide()
        
        header = self.table.horizontalHeader()
        
        # Reset all to Interactive for manual control
        for i in range(5):
             header.setSectionResizeMode(i, QHeaderView.Interactive)
        
        # Selection Mode
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setWordWrap(False) 
        
        # Context Menu - REMOVED (Replaced by Expansion)
        # self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Click Interaction
        self.table.cellClicked.connect(self._on_table_click)
        
        self.vBoxLayout.addWidget(self.table)
        

        
        # -- Dynamic Resizing Logic --
        # Ratios: No(1), Name(4), Cred(0.6), Prof(2), Time(4)
        # Total: 11.6
        self.column_ratios = [1, 4, 0.6, 2, 4] 
        
        # Hook resize event
        self.table.resizeEvent = self._on_table_resize
        
    def _on_table_resize(self, event):
        # Call original resize first
        super(TableWidget, self.table).resizeEvent(event)
        
        width = self.table.viewport().width()
        total_ratio = sum(self.column_ratios)
        
        for i, ratio in enumerate(self.column_ratios):
            new_width = int(width * (ratio / total_ratio))
            self.table.setColumnWidth(i, new_width)

    def _bind_viewmodel(self):
        self.vm.bind('results', self._update_results)
        # self.vm.bind('sort_changed', ...) # Sort logic adaptation needed for TableWidget if custom

    def _on_query_change(self, text):
        self.vm.query = text

    def _on_options_change(self, state):
        self.vm.set_search_options(self.nameCheckBox.isChecked(), self.profCheckBox.isChecked())

    def _update_results(self, data):
        self.table.setRowCount(len(data))
        self.countLabel.setText(f"검색 결과: {len(data)}개")
        
        for i, row_data in enumerate(data):
            for j, val in enumerate(row_data):
                text = str(val)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                # Tooltip for truncated text
                item.setToolTip(text)
                self.table.setItem(i, j, item)
        
    

    def _on_table_click(self, row, col):
        # 1. Check if clicked row is a Detail Row
        # We identify detail rows by checking if they contain our widget
        if self.table.cellWidget(row, 0):
            # It's a detail row or has a widget. 
            # In our logic, detail row spans all columns and has widget in col 0.
            return

        # 2. Check if the NEXT row is already a detail row (Toggle Off)
        if row + 1 < self.table.rowCount():
            if isinstance(self.table.cellWidget(row + 1, 0), CourseDetailWidget):
                self.table.removeRow(row + 1)
                return

        # 3. Collapse any other open detail rows
        # Iterate backwards to avoid index shifting issues when removing
        for i in range(self.table.rowCount() - 1, -1, -1):
            if isinstance(self.table.cellWidget(i, 0), CourseDetailWidget):
                self.table.removeRow(i)
        
        # 4. Re-calculate row index (it might have changed if we removed rows above)
        # But wait, if we removed a row *above* the clicked one, 'row' is invalid.
        # Simple fix: We cleared ALL detail rows. So the clicked row index might need adjustment?
        # Actually, if we remove Detail Rows, formatting changes.
        # To be safe: Store the Item (unique ID) of clicked row before clearing?
        # But `row` is just an index.
        #
        # Better approach: 
        # Since we enforce "One Detail Row", just find it. 
        # If it was below current row, current row index is same.
        # If it was above current row, current row index decreases.
        
        # Let's rely on QTableWidget.item to find the row again?
        # Or simplistic: Just clear all, then find which row has the data we want?
        # 
        # FASTEST WAY:
        # Just use the data from the clicked row (text) to identify it, clear all, then find the row with that data.
        
        c_id = self.table.item(row, 0).text()
        c_name = self.table.item(row, 1).text()
        
        # Clear all detail rows again (just to be sure)
        for i in range(self.table.rowCount() - 1, -1, -1):
             if isinstance(self.table.cellWidget(i, 0), CourseDetailWidget):
                self.table.removeRow(i)
                
        # Find the row again (as indices shifted)
        current_row = -1
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if item and item.text() == c_id:
                # Potential collision if multiple same IDs? (Unlikely for lecture ID)
                # But actually ID is unique per lecture usually, or at least visible one.
                # Let's assume ID is column 0.
                current_row = i
                break
        
        if current_row == -1: return 
        
        # 5. Insert New Detail Row
        insert_idx = current_row + 1
        self.table.insertRow(insert_idx)
        
        # Widget
        detail_widget = CourseDetailWidget(self.vm, c_id, c_name)
        self.table.setCellWidget(insert_idx, 0, detail_widget)
        self.table.setRowHeight(insert_idx, 60)
        self.table.setSpan(insert_idx, 0, 1, 5) # Span 5 columns
        
    # Context menu removed
