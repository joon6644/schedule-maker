"""
Config Interface
Replaces ConfigTab with Fluent UI.
Uses Card Widgets for grouping settings.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QFileDialog, 
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSizePolicy, QAbstractSpinBox
)
from PySide6.QtCore import Qt, QTimer
from qfluentwidgets import (
    CardWidget, SimpleCardWidget, HeaderCardWidget, 
    SpinBox, CheckBox, TimePicker, ComboBox, PrimaryPushButton, PushButton,
    TableWidget, FluentIcon as FIF, BodyLabel, TitleLabel, SubtitleLabel,
    ScrollArea, StrongBodyLabel, InfoBar, InfoBarPosition
)

from ..viewmodels.config_viewmodel import ConfigViewModel

# Helper for dialogs
from .search_interface import SearchInterface # Just for reference or sharing types? No.

from ..widgets.draggable_table import DraggableTableWidget


class ConfigInterface(ScrollArea):
    """
    Config Interface
    """
    def __init__(self, parent=None, controller=None):
        super().__init__(parent=parent)
        self.setObjectName("configInterface")
        self.controller = controller
        
        # ViewModel Initialization
        config_service = controller.config_service if controller else None
        course_service = controller.course_service if controller else None
        self.vm = ConfigViewModel(config_service, course_service)
        
        # Inject Interaction Service (Critical for Alerts)
        if controller and controller.interaction_service:
            self.vm.set_interaction_service(controller.interaction_service)
        elif parent: # Fallback to parent (MainWindow)
            self.vm.set_interaction_service(parent)
        
        self._setup_ui()
        self._bind_viewmodel()
        
        # Load Data
        self.vm.load_data()

    def _setup_ui(self):
        self.view = QWidget(self)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        # Fix background of scroll area view
        self.view.setObjectName("ConfigView")
        self.view.setStyleSheet("#ConfigView { background-color: white; }")

        self.vBoxLayout = QVBoxLayout(self.view)
        self.vBoxLayout.setContentsMargins(40, 40, 40, 40)
        self.vBoxLayout.setSpacing(30)

        # Title
        self.titleLabel = TitleLabel("설정", self.view)
        self.vBoxLayout.addWidget(self.titleLabel)

        # Main Layout (Horizontal: Settings | Required | Desired)
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setSpacing(20)
        # Explicitly set stretch factors to the layout logic
        # Note: addWidget(w, stretch) should work, but minimum sizes can fight it.
        # We will set container minimum widths to 0 to allow shrinking.
        self.vBoxLayout.addLayout(self.mainLayout)

        # Helper to create clean container with 0 min width to obey stretch
        def create_container():
            w = CardWidget(self.view)
            w.setObjectName("Container")
            w.setMinimumWidth(0) # IMPORTANT for stretch
            # Force layout to respect stretch factors by ignoring content size
            w.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding) 
            w.setStyleSheet("""
                #Container {
                    background-color: #FAFAFA;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                }
            """)
            return w

        # 1. Settings Panel
        self.settingsCard = create_container()
        self.settingsLayout = QVBoxLayout(self.settingsCard)
        self.settingsLayout.setContentsMargins(15, 20, 15, 20) # Slightly tighter margins
        self.settingsLayout.setSpacing(15)

        self.settingsLayout.addWidget(SubtitleLabel("⚙️ 기본 설정", self.settingsCard))

        # Credits
        self.settingsLayout.addWidget(StrongBodyLabel("🎓 이수 학점", self.settingsCard))
        self.creditLayout = QHBoxLayout()
        
        # Style to hide spinbox arrows for cleaner look
        # Fluent SpinBox structure is complex, might need CompactSpinBox or just resize.
        # However, user said "remove arrows".
        # Making them wider actually helps, but we are constrained.
        # Let's try CompactSpinBox or just hide buttons via properties if available.
        # Fluent widgets SpinBox has sub-widgets.
        # A simple fix: Use CompactSpinBox from qfluentwidgets if available, or just standard QSpinBox if Fluent's is too bulky.
        # Let's stick to Fluent SpinBox but hide buttons via stylesheet hack or setButtonVisible(False) if exists to save space.
        
        # Use LineEdit with Validator
        from qfluentwidgets import LineEdit
        from PySide6.QtGui import QIntValidator

        self.minCreditSpin = LineEdit(self.view)
        self.minCreditSpin.setValidator(QIntValidator(0, 30))
        self.minCreditSpin.setAlignment(Qt.AlignCenter)
        self.minCreditSpin.setText("18") 
        self.minCreditSpin.setFixedWidth(60) # Increased to 60
        # Connect signals to VM
        # FIX: lambda must accept the argument emitted by signal (text)
        self.minCreditSpin.textChanged.connect(lambda _: self.vm.set_credits(self.minCreditSpin.text(), self.maxCreditSpin.text()))

        self.maxCreditSpin = LineEdit(self.view)
        self.maxCreditSpin.setValidator(QIntValidator(0, 30))
        self.maxCreditSpin.setAlignment(Qt.AlignCenter)
        self.maxCreditSpin.setText("19") 
        self.maxCreditSpin.setFixedWidth(60) # Increased to 60
        self.maxCreditSpin.textChanged.connect(lambda _: self.vm.set_credits(self.minCreditSpin.text(), self.maxCreditSpin.text()))

        self.creditLayout.addWidget(self.minCreditSpin)
        self.creditLayout.addWidget(BodyLabel(" ~ ", self.view))
        self.creditLayout.addWidget(self.maxCreditSpin)
        self.creditLayout.addStretch(1) # Pack to left
        self.settingsLayout.addLayout(self.creditLayout)

        # Days
        self.settingsLayout.addWidget(StrongBodyLabel("🗓️ 공강 요일", self.settingsCard))
        self.daysLayout = QHBoxLayout()
        self.daysLayout.setSpacing(4) # Reduced from 10 to 4 to fit in narrow col
        self.day_checkboxes = {}
        for day in ['월', '화', '수', '목', '금']:
            cb = CheckBox(day, self.view)
            # Connect signals to VM
            cb.stateChanged.connect(lambda state, d=day: self.vm.set_excluded_day(d, state == Qt.Checked))
            self.daysLayout.addWidget(cb)
            self.day_checkboxes[day] = cb
        self.settingsLayout.addLayout(self.daysLayout)

        # Excluded Times
        self.settingsLayout.addWidget(StrongBodyLabel("🚫 제외 시간", self.settingsCard))
        self.timeInputLayout = QHBoxLayout()
        self.timeInputLayout.setSpacing(2) 
        
        self.dayCombo = ComboBox(self.view)
        self.dayCombo.addItems(['월', '화', '수', '목', '금'])
        self.dayCombo.setFixedWidth(60) # Safe width
        
        # Simple Text Entry 
        from qfluentwidgets import LineEdit
        self.startLine = LineEdit(self.view)
        self.startLine.setPlaceholderText("09:00")
        self.startLine.setFixedWidth(60) # Safe width
        self.startLine.setAlignment(Qt.AlignCenter) 
        
        self.endLine = LineEdit(self.view)
        self.endLine.setPlaceholderText("10:00")
        self.endLine.setFixedWidth(60) # Safe width
        self.endLine.setAlignment(Qt.AlignCenter)

        self.addTimeBtn = PushButton("+", self.view)
        self.addTimeBtn.setFixedWidth(30)
        self.addTimeBtn.setFocusPolicy(Qt.NoFocus) # Remove focus artifact
        self.addTimeBtn.clicked.connect(self._add_excluded_time)

        self.timeInputLayout.addWidget(self.dayCombo)
        self.timeInputLayout.addWidget(self.startLine)
        self.timeInputLayout.addWidget(BodyLabel("~", self.view))
        self.timeInputLayout.addWidget(self.endLine)
        self.timeInputLayout.addWidget(self.addTimeBtn)
        self.timeInputLayout.addStretch(1) # Left align
        self.settingsLayout.addLayout(self.timeInputLayout)


        self.exScheduleTable = TableWidget(self.view)
        self.exScheduleTable.setColumnCount(2)
        self.exScheduleTable.setHorizontalHeaderLabels(['요일', '시간'])
        self.exScheduleTable.verticalHeader().hide()
        
        # Optimize Table Columns: Day is short, Time needs space
        header = self.exScheduleTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.exScheduleTable.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.exScheduleTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.exScheduleTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.exScheduleTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.settingsLayout.addWidget(self.exScheduleTable)

        # Context Menu for ExScheduleTable
        self.exScheduleTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.exScheduleTable.customContextMenuRequested.connect(self._show_ex_time_menu)

        self.mainLayout.addWidget(self.settingsCard, 25) # Reverted to 25% as requested
        
        # 2. Required Courses
        self.reqCard = create_container()
        self._setup_course_list(self.reqCard, 'required', "📌 필수 강의")
        self.mainLayout.addWidget(self.reqCard, 35) # 35%
        
        # 3. Desired Courses
        self.desCard = create_container()
        self._setup_course_list(self.desCard, 'desired', "⭐ 희망 강의")
        self.mainLayout.addWidget(self.desCard, 35) # 35%

        # Bottom Actions
        self.actionLayout = QHBoxLayout()
        
        self.saveBtn = PushButton("설정 저장", self.view)
        self.saveBtn.clicked.connect(self._save_settings)
        self.loadBtn = PushButton("설정 불러오기", self.view)
        self.loadBtn.clicked.connect(self._load_settings)
        
        self.genBtn = PrimaryPushButton("시간표 확인", self.view) # Changed Text
        self.genBtn.clicked.connect(self._go_to_result) # Changed Action
        
        self.actionLayout.addWidget(self.saveBtn)
        self.actionLayout.addWidget(self.loadBtn)
        self.actionLayout.addStretch(1)
        self.actionLayout.addWidget(self.genBtn)
        
        self.vBoxLayout.addLayout(self.actionLayout)

    def _setup_course_list(self, card, list_type, title):
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        
        layout.addWidget(SubtitleLabel(title, card))
        
        # Enable Drag/Drop with custom widget
        table = DraggableTableWidget(self.vm, list_type, self.view) 
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(['강의번호', '강의명', '교수']) # ID -> 강의번호
        table.verticalHeader().hide()
        table.setAlternatingRowColors(True) # REQUESTED: Auto adjust grid colors
        
        # Column Layout Optimization
        
        # Column Layout Optimization
        header = table.horizontalHeader()
        
        # Col 0: ID (Give enough space)
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        table.setColumnWidth(0, 75) 
        
        # Col 1: Name (Stretch to fill)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Col 2: Prof
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        table.setColumnWidth(2, 90)
        
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        layout.addWidget(table)

        if list_type == 'required':
            self.reqTable = table
        else:
            self.desTable = table

        btnLayout = QHBoxLayout()
        addBtn = PushButton("추가", self.view)
        addBtn.clicked.connect(lambda: self._show_add_dialog(list_type))
        delBtn = PushButton("삭제", self.view)
        delBtn.clicked.connect(lambda: self._delete_course(list_type))

        btnLayout.addWidget(addBtn)
        btnLayout.addWidget(delBtn)
        layout.addLayout(btnLayout)


    def _bind_viewmodel(self):
        # Bind ViewModel callbacks to UI updates
        self.vm.bind('credits', self._update_credits_view)
        self.vm.bind('excluded_days', self._update_day_vars)
        self.vm.bind('required_list', lambda data: self._update_course_table(self.reqTable, data))
        self.vm.bind('desired_list', lambda data: self._update_course_table(self.desTable, data))
        self.vm.bind('excluded_times', self._update_ex_table)
        self.vm.bind('message', self._show_message)
        self.vm.bind('error', self._show_error)
        
        self.vm.bind('error', self._show_error)
        
        # [State Management] Bind Dirty State
        # 1. Needs Generation (Stale Result) -> Marks MainWindow Dirty & Updates Button
        self.vm.bind('needs_generation_changed', self._on_needs_generation_changed)
        
        # 2. Saved State -> Visual Feedback (Optional, maybe for Save Button in future)
        # self.vm.bind('is_dirty_changed', self._on_unsaved_state_changed) # Currently unused by UI logic
        
        # Exclusive Selection Logic
        
        # Exclusive Selection Logic
        # When reqTable is clicked, clear desTable selection
        self.reqTable.itemClicked.connect(lambda: self.desTable.clearSelection())
        # When desTable is clicked, clear reqTable selection
        self.desTable.itemClicked.connect(lambda: self.reqTable.clearSelection())
        
        # [Validation] Bind Validation Status
        # [Validation] Bind Validation Status
        self.vm.bind('validation_status', self._on_validation_status)
        
        # [Validation] Cooldown/Bounce Logic removed
        # Now handled by MainWindowInteractionService

    # ... (handlers) ...
    # ... (handlers) ...

    def _show_message(self, msg):
        title, content = msg
        if hasattr(self.vm, 'interaction_service') and self.vm.interaction_service:
            self.vm.interaction_service.show_info(title, content)
        else:
             print(f"[WARN] No interaction service for: {msg}")

    def _show_error(self, msg):
        title, content = msg
        if hasattr(self.vm, 'interaction_service') and self.vm.interaction_service:
            self.vm.interaction_service.show_error(title, content)
        else:
             print(f"[WARN] No interaction service for: {msg}")

    def _update_credits_view(self, val):
        """Block signals to prevent loop"""
        self.minCreditSpin.blockSignals(True)
        self.maxCreditSpin.blockSignals(True)
        try:
            self.minCreditSpin.setText(str(val[0]))
            self.maxCreditSpin.setText(str(val[1]))
        finally:
            self.minCreditSpin.blockSignals(False)
            self.maxCreditSpin.blockSignals(False)

    def _update_day_vars(self, data):
        for day, is_checked in data.items():
            if day in self.day_checkboxes:
                cb = self.day_checkboxes[day]
                cb.blockSignals(True) # Block
                cb.setChecked(is_checked)
                cb.blockSignals(False) # Unblock
                
    def _update_course_table(self, table, data):
        table.setRowCount(len(data))
        table.setAlternatingRowColors(False) # Force reset
        
        for i, row in enumerate(data):
            # ... (rest of logic)
            # row is (id, name, prof, credit?)
            c_id = str(row[0]) if len(row) > 0 else ""
            c_name = str(row[1]) if len(row) > 1 else ""
            c_prof = str(row[2]) if len(row) > 2 else ""

            # Set Items
            table.setItem(i, 0, QTableWidgetItem(c_id))
            table.setItem(i, 1, QTableWidgetItem(c_name))
            table.setItem(i, 2, QTableWidgetItem(c_prof))
            
            # Center Align
            for j in range(3):
                if table.item(i, j):
                   table.item(i, j).setTextAlignment(Qt.AlignCenter)

        table.setAlternatingRowColors(True) # Re-enable to force repaint
        table.viewport().update()
                
    def _update_ex_table(self, data):
        self.exScheduleTable.setRowCount(len(data))
        for i, (day, start, end) in enumerate(data):
            item_day = QTableWidgetItem(day)
            item_day.setTextAlignment(Qt.AlignCenter)
            self.exScheduleTable.setItem(i, 0, item_day)
            
            # Combine start and end
            item_time = QTableWidgetItem(f"{start} ~ {end}")
            item_time.setTextAlignment(Qt.AlignCenter)
            self.exScheduleTable.setItem(i, 1, item_time)

    # --- Changed/New Logic ---

    # --- Changed/New Logic ---

    # def _mark_dirty(self, *args):
    #     if hasattr(self.window(), 'set_dirty'):
    #         self.window().set_dirty(True)

    def _go_to_result(self):
        # 1. Apply current settings to Service (Must apply before switching!)
        # Use simple try-catch or safe int conversion as LineEdit can have empty/partial text
        try:
            min_c = int(self.minCreditSpin.text()) if self.minCreditSpin.text() else 0
            max_c = int(self.maxCreditSpin.text()) if self.maxCreditSpin.text() else 0
        except ValueError:
            min_c, max_c = 0, 0

        if not self.vm.apply_changes(
            min_c, 
            max_c, 
            self.day_checkboxes
        ):
            return # Validation failed

        # 2. Force mark dirty REMOVED
        # We rely on actual change detection. If apply_changes detected a change, 
        # it would have notified 'config_changed', enabling dirty flag.
        # But wait, apply_changes applies to Memory Config, validation logic etc.
        # The signals (textChanged) already updated the VM state and triggered dirty if changed.
        # So we don't need to force it here.
        
        main_window = self.window()
        
        # if hasattr(main_window, 'set_dirty'):
        #     main_window.set_dirty(True)

        # 3. Switch tab. MainWindow will detect dirty state and gen.
        if hasattr(main_window, 'switch_to_result'):
             # Calling this will trigger _on_stack_changed in MainWindow
             # But if we want to ensure generation check, MainWindow.switch_to_result does calls _check_and_generate
             main_window.switch_to_result()

    def _add_excluded_time(self):
        self.vm.add_excluded_time(
            self.dayCombo.currentText(),
            self.startLine.text(),
            self.endLine.text()
        )
        # self._mark_dirty() -> Handled by VM Event

    def _show_ex_time_menu(self, pos):
        from qfluentwidgets import RoundMenu, Action
        item = self.exScheduleTable.itemAt(pos)
        if hasattr(item, 'row'): # Validation
            menu = RoundMenu(parent=self)
            menu.addAction(Action("삭제", triggered=lambda: self.vm.remove_excluded_time(item.row())))
            menu.exec(self.exScheduleTable.mapToGlobal(pos))

    def _delete_course(self, list_type):
        table = self.reqTable if list_type == 'required' else self.desTable
        row = table.currentRow()
        if row >= 0:
            self.vm.remove_course(list_type, row)
            # Show "Deleted" as Error (Red) as requested
            self._show_error(("삭제 완료", "강의가 삭제되었습니다."))

    
    def _load_settings(self):
        filename, _ = QFileDialog.getOpenFileName(self, "설정 불러오기", "data", "JSON Files (*.json)")
        if filename:
            self.vm.load_config_from_file(filename)
            # self._mark_dirty() -> Handled by VM Event
            # VM.load_config_from_file should triggers updates. But VM.notify calls might be many.
            # Actually explicit load probably should dirty it.
    
    def _save_settings(self):
        # ... (Same as before but keep it explicit)
        filename, _ = QFileDialog.getSaveFileName(self, "설정 저장", "data", "JSON Files (*.json)")
        if filename:
             d_vars = {d: cb.isChecked() for d, cb in self.day_checkboxes.items()}
             self.vm.save_settings_to_file(
                 filename, 
                 self.minCreditSpin.text(), 
                 self.maxCreditSpin.text(), 
                 d_vars
             )
    
    # Simple add dialog (Needs update to mark dirty)
    def _show_add_dialog(self, list_type):
        from qfluentwidgets import MessageBoxBase, SubtitleLabel, LineEdit
        
        class AddDialog(MessageBoxBase):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.titleLabel = SubtitleLabel("강의 수동 추가", self)
                self.viewLayout.addWidget(self.titleLabel)
                self.idEdit = LineEdit(self); self.idEdit.setPlaceholderText("강의번호"); self.viewLayout.addWidget(self.idEdit)
                self.nameEdit = LineEdit(self); self.nameEdit.setPlaceholderText("강의명"); self.viewLayout.addWidget(self.nameEdit)
                self.profEdit = LineEdit(self); self.profEdit.setPlaceholderText("교수명"); self.viewLayout.addWidget(self.profEdit)
                self.widget.setMinimumWidth(300)

        w = AddDialog(self.window())
        if w.exec():
            self.vm.add_course_filter(list_type, w.nameEdit.text().strip(), w.profEdit.text().strip(), w.idEdit.text().strip())
            # self._mark_dirty() -> Handled by VM Event



    
    def _on_needs_generation_changed(self, is_stale):
        """Called when ViewModel determines generation is needed (Stale Result)"""
        print(f"[DEBUG] Needs Generation Changed: {is_stale}")
        
        # Update MainWindow state
        main_window = self.window()
        if hasattr(main_window, 'set_dirty'):
            main_window.set_dirty(is_stale)


        self.genBtn.setText("시간표 확인")

    def _on_validation_status(self, status):
        """유효성 상태 변경 핸들러"""
        is_valid, msg = status
        
        # 1. Update Button State (Immediate)
        if self.genBtn:
            self.genBtn.setEnabled(is_valid)
            self.genBtn.setToolTip(msg if not is_valid else "")
        
        # 2. Show Alert (Delegated to Service with Cooldown)
        if not is_valid and msg:
            self._show_error(("설정 오류", msg))
